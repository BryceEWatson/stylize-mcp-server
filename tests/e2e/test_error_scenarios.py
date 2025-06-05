"""
E2E tests for error scenarios and edge cases.

Tests various error conditions and edge cases across all interfaces.
"""
import pytest
import asyncio
import base64
from typing import Dict, Any

from tests.e2e.pages.demo_page import DemoPage
from tests.e2e.utils.mcp_client import E2EMCPClient


@pytest.mark.integration
class TestErrorScenarios:
    """Test various error scenarios and their handling."""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_config, test_data_manager, api_client):
        """Set up test environment."""
        self.test_config = test_config
        self.test_data = test_data_manager
        self.api_client = api_client
    
    async def test_openai_service_failures(self, mock_openai_failure, valid_test_image):
        """Test behavior when OpenAI API is unavailable or returns errors."""
        # Start trial session
        trial_response = await self.api_client.start_trial_session()
        assert trial_response.status_code == 200
        
        trial_data = trial_response.json()
        session_id = trial_data["session_id"]
        
        # Try to generate image with mocked OpenAI failure
        image_data = base64.b64decode(valid_test_image)
        
        response = await self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="OpenAI failure test"
        )
        
        # Should return appropriate error
        assert response.status_code in [500, 503, 502]
        
        if response.status_code != 500:
            error_data = response.json()
            assert "error" in error_data or "detail" in error_data
    
    async def test_gcs_upload_failures(self, mock_gcs_failure, valid_test_image):
        """Test behavior when GCS uploads fail."""
        # Start trial session
        trial_response = await self.api_client.start_trial_session()
        trial_data = trial_response.json()
        session_id = trial_data["session_id"]
        
        # Try to generate image with mocked GCS failure
        image_data = base64.b64decode(valid_test_image)
        
        response = await self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="GCS failure test"
        )
        
        # Should handle GCS failure gracefully
        assert response.status_code in [500, 503]
    
    async def test_malformed_request_handling(self):
        """Test handling of various malformed requests."""
        # Test invalid JSON
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Invalid JSON payload
            response = await client.post(
                f"{self.api_client.base_url}/stylize_image",
                content="invalid json",
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code == 400
            
            # Missing required fields
            response = await client.post(
                f"{self.api_client.base_url}/stylize_image",
                json={"style_id": "van_gogh"}  # Missing image
            )
            assert response.status_code == 400
            
            # Invalid field values
            response = await client.post(
                f"{self.api_client.base_url}/stylize_image",
                json={
                    "style_id": "",  # Empty style ID
                    "user_prompt": "x" * 10000  # Very long prompt
                }
            )
            assert response.status_code == 400
    
    async def test_session_expiration_scenarios(self):
        """Test behavior when trial sessions or JWT tokens expire."""
        # Test with expired/invalid session ID
        expired_session_id = "expired-session-12345"
        
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])
        
        response = await self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=expired_session_id,
            user_prompt="Expired session test"
        )
        
        assert response.status_code in [400, 401, 404]
        
        error_data = response.json()
        assert any(word in str(error_data).lower() for word in ["session", "invalid", "expired", "not found"])
    
    async def test_rate_limiting_scenarios(self):
        """Test rate limiting behavior."""
        # Make rapid requests to trigger rate limiting
        rapid_requests = []
        
        for i in range(10):  # Make many rapid requests
            task = self.api_client.start_trial_session()
            rapid_requests.append(task)
        
        responses = await asyncio.gather(*rapid_requests, return_exceptions=True)
        
        # Should eventually hit rate limits
        rate_limited_count = 0
        successful_count = 0
        
        for response in responses:
            if isinstance(response, Exception):
                rate_limited_count += 1
            elif hasattr(response, 'status_code'):
                if response.status_code == 429:  # Too Many Requests
                    rate_limited_count += 1
                elif response.status_code == 200:
                    successful_count += 1
        
        # Should have some rate limiting or at least handle all requests
        assert rate_limited_count > 0 or successful_count == len(responses)
    
    async def test_invalid_image_formats(self):
        """Test handling of invalid image formats and data."""
        # Start valid trial session
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        # Test corrupted image data
        corrupted_image = self.test_data.get_test_images()["corrupted"]
        
        response = await self.api_client.stylize_image(
            image_data=base64.b64decode(corrupted_image),
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="Corrupted image test"
        )
        
        assert response.status_code == 400
        
        # Test oversized image
        oversized_image = self.test_data.get_test_images()["oversized_image"]
        
        response = await self.api_client.stylize_image(
            image_data=base64.b64decode(oversized_image),
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="Oversized image test"
        )
        
        assert response.status_code == 400
        
        # Test invalid base64 data
        response = await self.api_client.stylize_image(
            image_data=b"not base64 image data",
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="Invalid data test"
        )
        
        assert response.status_code == 400
    
    async def test_invalid_style_ids(self):
        """Test handling of invalid style IDs."""
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        invalid_styles = self.test_data.get_invalid_style_ids()
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])
        
        for invalid_style in invalid_styles:
            response = await self.api_client.stylize_image(
                image_data=image_data,
                style_id=invalid_style,
                session_id=session_id,
                user_prompt="Invalid style test"
            )
            
            assert response.status_code == 400
            error_data = response.json()
            assert "style" in str(error_data).lower()
    
    async def test_content_policy_violations(self):
        """Test content policy violation handling."""
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        problematic_prompts = self.test_data.get_problematic_prompts()
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])
        
        for prompt in problematic_prompts[:3]:  # Test first few
            response = await self.api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=prompt
            )
            
            # Should either reject or sanitize the content
            if response.status_code == 400:
                error_data = response.json()
                assert any(word in str(error_data).lower() for word in ["content", "policy", "inappropriate"])
            elif response.status_code == 200:
                # Content was sanitized and processed
                result = response.json()
                assert "stylized_image_url" in result
    
    async def test_mcp_error_handling(self):
        """Test MCP-specific error scenarios."""
        mcp_client = E2EMCPClient(f"{self.test_config.base_url}/mcp")
        
        try:
            await mcp_client.connect()
            
            # Test tool with invalid parameters
            try:
                await mcp_client.stylize_image(
                    image_base64="invalid_base64",
                    style_id="nonexistent_style",
                    session_id="invalid_session"
                )
                pytest.fail("Expected MCP error")
            except Exception as e:
                assert len(str(e)) > 0
            
            # Test missing required parameters
            try:
                await mcp_client.stylize_image(image_base64="")  # Empty required field
                pytest.fail("Expected MCP error")
            except Exception as e:
                assert len(str(e)) > 0
            
            # Test invalid tool name
            try:
                result = await mcp_client.client.call_tool("nonexistent_tool", {})
                pytest.fail("Expected error for invalid tool")
            except Exception as e:
                assert "tool" in str(e).lower() or "not found" in str(e).lower()
                
        finally:
            await mcp_client.disconnect()
    
    async def test_concurrent_session_conflicts(self):
        """Test handling of concurrent session operations."""
        # Create multiple trial sessions rapidly
        session_tasks = [self.api_client.start_trial_session() for _ in range(5)]
        responses = await asyncio.gather(*session_tasks)
        
        session_ids = []
        for response in responses:
            if response.status_code == 200:
                session_ids.append(response.json()["session_id"])
        
        assert len(session_ids) > 0
        
        # Try to use sessions concurrently
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])
        
        concurrent_tasks = []
        for session_id in session_ids[:3]:  # Use first 3 sessions
            task = self.api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt="Concurrent session test"
            )
            concurrent_tasks.append(task)
        
        concurrent_responses = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Should handle concurrent operations gracefully
        successful_responses = 0
        for response in concurrent_responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_responses += 1
        
        assert successful_responses > 0  # At least some should succeed


@pytest.mark.integration
class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    async def test_extremely_large_project_context(self, api_client, valid_test_image):
        """Test handling of very large project context data."""
        trial_response = await api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        # Create oversized project context
        oversized_context = self.test_data.get_project_contexts()["oversized"]
        
        image_data = base64.b64decode(valid_test_image)
        
        response = await api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="Large context test",
            project_context=oversized_context
        )
        
        # Should either reject or truncate the context
        assert response.status_code in [200, 400]
        
        if response.status_code == 400:
            error_data = response.json()
            assert any(word in str(error_data).lower() for word in ["size", "large", "limit"])
    
    async def test_special_characters_in_prompts(self, api_client, valid_test_image):
        """Test handling of special characters, emojis, etc. in user prompts."""
        trial_response = await api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        special_prompts = [
            "🎨🎭🎪 Create art with emojis 🎨🎭🎪",
            "Prompt with üñíçødé characters",
            "Prompt with\nnewlines\nand\ttabs",
            "Prompt with \"quotes\" and 'apostrophes'",
            "Prompt with <tags> & special symbols @#$%",
        ]
        
        image_data = base64.b64decode(valid_test_image)
        
        for prompt in special_prompts:
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=prompt
            )
            
            # Should handle special characters gracefully
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                result = response.json()
                assert "stylized_image_url" in result
    
    async def test_simultaneous_trial_conversion(self, api_client):
        """Test race conditions in trial-to-account conversion."""
        # Create trial session
        trial_response = await api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        # Create multiple simultaneous conversion attempts
        user_data = self.test_data.get_test_user_data()
        
        conversion_data = {
            "session_id": session_id,
            **user_data
        }
        
        conversion_tasks = [
            api_client.convert_trial_to_user(conversion_data)
            for _ in range(3)
        ]
        
        responses = await asyncio.gather(*conversion_tasks, return_exceptions=True)
        
        # Only one should succeed
        successful_conversions = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code in [200, 201]:
                successful_conversions += 1
        
        assert successful_conversions <= 1, "Only one conversion should succeed"
    
    async def test_boundary_value_testing(self, api_client):
        """Test boundary values for various parameters."""
        # Test with minimum and maximum allowed values
        test_cases = [
            {
                "description": "Empty prompt",
                "prompt": "",
                "expected_status": [200, 400]
            },
            {
                "description": "Very long prompt",
                "prompt": "x" * 5000,
                "expected_status": [200, 400]
            },
            {
                "description": "Minimum image size",
                "image_data": self._create_minimal_image(),
                "expected_status": [200, 400]
            }
        ]
        
        trial_response = await api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]
        
        default_image = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])
        
        for test_case in test_cases:
            image_data = test_case.get("image_data", default_image)
            prompt = test_case.get("prompt", "boundary test")
            
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=prompt
            )
            
            assert response.status_code in test_case["expected_status"], f"Failed for {test_case['description']}"
    
    def _create_minimal_image(self) -> bytes:
        """Create minimal valid image data."""
        from PIL import Image
        import io
        
        # Create tiny 1x1 image
        img = Image.new("RGB", (1, 1), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return buffer.getvalue()


@pytest.mark.integration
@pytest.mark.web_ui
class TestWebUIErrorScenarios:
    """Test error scenarios specific to web UI."""
    
    @pytest.fixture(autouse=True)
    def setup(self, webdriver_instance, test_config):
        """Set up web driver."""
        self.driver = webdriver_instance
        self.base_url = test_config.base_url
        self.demo_page = DemoPage(self.driver, self.base_url)
    
    def test_javascript_errors_handling(self):
        """Test handling of JavaScript errors in web interface."""
        self.demo_page.navigate_to_demo()
        
        # Check for JavaScript errors
        logs = self.driver.get_log("browser")
        js_errors = [log for log in logs if log["level"] == "SEVERE"]
        
        # Should not have critical JavaScript errors
        assert len(js_errors) == 0, f"JavaScript errors found: {js_errors}"
    
    def test_network_failure_handling(self):
        """Test web UI behavior during network failures."""
        self.demo_page.navigate_to_demo()
        
        # Simulate network failure by navigating to invalid URL
        self.driver.get("http://invalid-url-that-does-not-exist.com")
        
        # Should handle gracefully (browser will show error page)
        # Then return to valid page
        self.demo_page.navigate_to_demo()
        
        # Should work normally after network is restored
        assert "Demo" in self.demo_page.get_page_title_text()
    
    def test_file_upload_edge_cases(self):
        """Test edge cases in file upload functionality."""
        self.demo_page.navigate_to_demo()
        
        # Test with non-existent file path
        try:
            self.demo_page.upload_image("/path/to/nonexistent/file.jpg")
            # Should handle gracefully - either show error or ignore
        except Exception:
            # Exception is acceptable for invalid file path
            pass
        
        # Verify page still functions
        assert self.demo_page.is_element_present(self.demo_page.FILE_INPUT)
    
    def test_browser_back_forward_handling(self):
        """Test browser navigation edge cases."""
        self.demo_page.navigate_to_demo()
        
        # Navigate to different page
        self.demo_page.navigate_to("/")
        
        # Go back
        self.demo_page.go_back()
        
        # Should return to demo page
        current_url = self.demo_page.get_current_url()
        assert "demo" in current_url or current_url.endswith("/")
        
        # Page should still be functional
        assert self.demo_page.is_element_present(self.demo_page.GENERATE_BUTTON)