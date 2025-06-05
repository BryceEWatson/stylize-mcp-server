"""
E2E tests for MCP AI assistant integration.

Tests the complete AI assistant workflow using MCP tools.
"""

import pytest

from tests.e2e.utils.mcp_client import E2EMCPClient


@pytest.mark.integration
@pytest.mark.mcp_only
class TestMCPAIIntegration:
    """Test complete AI assistant workflow using MCP tools."""

    @pytest.fixture(autouse=True)
    def setup(self, test_config, test_data_manager):
        """Set up test environment."""
        self.test_config = test_config
        self.test_data = test_data_manager
        self.mcp_url = f"{test_config.base_url}/mcp"

    async def test_complete_mcp_trial_workflow(self, valid_test_image):
        """Test complete AI assistant workflow using MCP tools."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Step 1: Start trial session
            trial_result = await client.start_trial_session()
            assert trial_result["session_id"]
            assert trial_result["images_remaining"] == 5
            session_id = trial_result["session_id"]

            # Step 2: List available styles
            styles_result = await client.list_styles()
            assert "styles" in styles_result
            styles = styles_result["styles"]
            assert len(styles) > 0

            # Verify we have expected styles
            style_ids = [style["id"] for style in styles]
            assert "van_gogh" in style_ids
            assert "pixel_art" in style_ids

            # Step 3: Get style details
            van_gogh_details = await client.get_style_details("van_gogh")
            assert van_gogh_details["id"] == "van_gogh"
            assert "description" in van_gogh_details
            assert "prompt_template" in van_gogh_details

            # Step 4: Generate single-style image
            single_result = await client.stylize_image(
                image_base64=valid_test_image,
                style_id="van_gogh",
                user_prompt="a majestic mountain landscape",
                session_id=session_id
            )

            assert single_result["style"] == "van_gogh"
            assert "stylized_image_url" in single_result
            assert single_result["trial_info"]["images_remaining"] == 4
            assert single_result["trial_info"]["images_used"] == 1

            # Step 5: Generate multi-style variations (omitting style_id)
            multi_result = await client.stylize_image(
                image_base64=valid_test_image,
                user_prompt="a serene forest scene",
                session_id=session_id
            )

            assert multi_result["multiple_styles"] is True
            assert "images" in multi_result
            assert len(multi_result["images"]) == 4
            assert multi_result["total_images"] == 4

            # Verify different styles were used
            used_styles = [img["style_id"] for img in multi_result["images"]]
            assert len(set(used_styles)) == 4  # All different styles

            # Step 6: Check trial status
            status_result = await client.check_trial_status(session_id)
            assert status_result["images_remaining"] == 0  # Used all 5 (1 + 4)
            assert status_result["images_used"] == 5

            # Step 7: Handle trial expiration gracefully
            try:
                expired_result = await client.stylize_image(
                    image_base64=valid_test_image,
                    style_id="pixel_art",
                    session_id=session_id
                )
                # If no exception, check for error in response
                if "error" in expired_result:
                    assert "trial" in expired_result["error"].lower()
                else:
                    pytest.fail("Expected trial limit error")
            except Exception as e:
                # Exception is also acceptable for trial limit
                assert "trial" in str(e).lower() or "limit" in str(e).lower()

        finally:
            await client.disconnect()

    async def test_mcp_api_key_authentication(self, valid_test_image, test_config):
        """Test MCP tools with API key authentication."""
        if not test_config.test_api_key:
            pytest.skip("API key not provided for testing")

        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Generate image with API key (should bypass trial limits)
            result = await client.stylize_image(
                image_base64=valid_test_image,
                style_id="van_gogh",
                user_prompt="API key test",
                api_key=test_config.test_api_key
            )

            assert "stylized_image_url" in result
            assert result["style"] == "van_gogh"
            # Should not have trial_info when using API key
            assert "trial_info" not in result or result["trial_info"] is None

        finally:
            await client.disconnect()

    async def test_mcp_error_handling(self, valid_test_image):
        """Test MCP tool error responses and recovery."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Test invalid style ID
            try:
                await client.stylize_image(
                    image_base64=valid_test_image,
                    style_id="nonexistent_style",
                    session_id="dummy_session"
                )
                pytest.fail("Expected error for invalid style")
            except Exception as e:
                assert "style" in str(e).lower() or "invalid" in str(e).lower()

            # Test invalid session ID
            try:
                await client.stylize_image(
                    image_base64=valid_test_image,
                    style_id="van_gogh",
                    session_id="invalid_session_id"
                )
                pytest.fail("Expected error for invalid session")
            except Exception as e:
                assert "session" in str(e).lower() or "invalid" in str(e).lower()

            # Test invalid image data
            try:
                await client.stylize_image(
                    image_base64="invalid_base64_data",
                    style_id="van_gogh",
                    session_id="dummy_session"
                )
                pytest.fail("Expected error for invalid image data")
            except Exception as e:
                assert "image" in str(e).lower() or "invalid" in str(e).lower() or "base64" in str(e).lower()

            # Test missing required parameters
            try:
                await client.stylize_image(
                    image_base64=valid_test_image
                    # Missing session_id and api_key
                )
                pytest.fail("Expected error for missing authentication")
            except Exception as e:
                assert any(word in str(e).lower() for word in ["auth", "session", "key", "required"])

        finally:
            await client.disconnect()

    async def test_mcp_project_context_processing(self, valid_test_image):
        """Test MCP tools with complex project context."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Test with complex project context
            project_contexts = self.test_data.get_project_contexts()
            complex_context = project_contexts["complete_with_logo"]

            result = await client.stylize_image(
                image_base64=valid_test_image,
                style_id="flat_ui_icon",
                user_prompt="company logo design",
                session_id=session_id,
                project_context=complex_context
            )

            assert "stylized_image_url" in result
            assert result["style"] == "flat_ui_icon"

            # Test with minimal context
            minimal_context = project_contexts["minimal"]

            result2 = await client.stylize_image(
                image_base64=valid_test_image,
                style_id="neumorphic_button",
                user_prompt="UI element design",
                session_id=session_id,
                project_context=minimal_context
            )

            assert "stylized_image_url" in result2
            assert result2["style"] == "neumorphic_button"

        finally:
            await client.disconnect()

    async def test_mcp_text_to_image_generation(self):
        """Test text-to-image generation via MCP."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Generate image from text
            result = await client.generate_image_from_text(
                prompt="a futuristic city skyline at sunset",
                style_id="flat_ui_icon",
                session_id=session_id
            )

            assert "image_url" in result or "stylized_image_url" in result
            assert result.get("style") == "flat_ui_icon"

            # Test with project context
            project_context = self.test_data.get_project_contexts()["minimal"]

            result2 = await client.generate_image_from_text(
                prompt="modern office building",
                style_id="glassmorphic_card",
                session_id=session_id,
                project_context=project_context
            )

            assert "image_url" in result2 or "stylized_image_url" in result2

        finally:
            await client.disconnect()

    async def test_mcp_tool_schema_validation(self):
        """Test MCP tool schemas and parameters."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Get available tools
            tools = await client.get_available_tools()
            assert len(tools) > 0

            # Verify expected tools are present
            tool_names = [tool["name"] for tool in tools]
            expected_tools = [
                "start_trial_session",
                "check_trial_status",
                "stylize_image",
                "generate_image_from_text",
                "list_styles",
                "get_style_details"
            ]

            for expected_tool in expected_tools:
                assert expected_tool in tool_names, f"Tool {expected_tool} not found"

            # Validate specific tool schemas
            stylize_schema = await client.validate_tool_schema("stylize_image")
            assert stylize_schema["found"] is True
            assert "image_base64" in str(stylize_schema["schema"])

            styles_schema = await client.validate_tool_schema("list_styles")
            assert styles_schema["found"] is True

        finally:
            await client.disconnect()

    async def test_mcp_concurrent_requests(self, valid_test_image):
        """Test concurrent MCP requests."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Prepare concurrent requests
            request_args = [
                {
                    "image_base64": valid_test_image,
                    "style_id": "van_gogh",
                    "user_prompt": f"concurrent test {i}",
                    "session_id": session_id
                }
                for i in range(3)
            ]

            # Execute concurrent requests
            results = await client.test_concurrent_requests(
                "stylize_image",
                request_args,
                max_concurrent=3
            )

            assert len(results) == 3

            # Check results
            successful_results = 0
            for _result, response_time, error in results:
                if error is None:
                    successful_results += 1
                    assert response_time > 0
                else:
                    # Some requests might fail due to trial limits
                    assert "trial" in error.lower() or "limit" in error.lower()

            # At least one request should succeed
            assert successful_results >= 1

        finally:
            await client.disconnect()

    @pytest.mark.slow
    async def test_mcp_performance_benchmarks(self, valid_test_image):
        """Test MCP performance benchmarks."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Test single image generation performance
            result, response_time, error = await client.measure_tool_response_time(
                "stylize_image",
                {
                    "image_base64": valid_test_image,
                    "style_id": "van_gogh",
                    "user_prompt": "performance test",
                    "session_id": session_id
                }
            )

            assert error is None, f"Request failed: {error}"
            assert response_time < 30.0, f"Response time too slow: {response_time}s"

            # Test styles listing performance
            styles_result, styles_time, styles_error = await client.measure_tool_response_time(
                "list_styles",
                {}
            )

            assert styles_error is None
            assert styles_time < 5.0, f"Styles listing too slow: {styles_time}s"

        finally:
            await client.disconnect()

    async def test_mcp_connection_resilience(self):
        """Test MCP connection handling and resilience."""
        client = E2EMCPClient(self.mcp_url)

        # Test connection
        connection_result = await client.test_connection()
        assert connection_result is True

        # Test multiple connections
        await client.connect()
        await client.disconnect()
        await client.connect()

        # Should be able to use tools after reconnection
        tools = await client.get_available_tools()
        assert len(tools) > 0

        await client.disconnect()

    async def test_mcp_timeout_handling(self, valid_test_image):
        """Test timeout handling for MCP tools."""
        client = E2EMCPClient(self.mcp_url)

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Test with very short timeout (should timeout)
            result = await client.call_tool_with_timeout(
                "stylize_image",
                {
                    "image_base64": valid_test_image,
                    "style_id": "van_gogh",
                    "user_prompt": "timeout test",
                    "session_id": session_id
                },
                timeout_seconds=0.1  # Very short timeout
            )

            # Should timeout
            assert result["success"] is False
            assert result["error"] == "timeout"

            # Test with reasonable timeout (should succeed)
            result2 = await client.call_tool_with_timeout(
                "list_styles",
                {},
                timeout_seconds=10.0
            )

            assert result2["success"] is True
            assert "styles" in result2["result"]

        finally:
            await client.disconnect()


@pytest.mark.integration
@pytest.mark.mcp_only
@pytest.mark.requires_openai
class TestMCPRealIntegration:
    """Test MCP integration with real OpenAI API (requires API key)."""

    async def test_end_to_end_real_generation(self, valid_test_image, test_config):
        """Test complete end-to-end generation with real OpenAI API."""
        if not test_config.openai_api_key:
            pytest.skip("OpenAI API key required for real integration test")

        client = E2EMCPClient(f"{test_config.base_url}/mcp")

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Generate real image
            result = await client.stylize_image(
                image_base64=valid_test_image,
                style_id="van_gogh",
                user_prompt="a beautiful mountain landscape with flowing water",
                session_id=session_id
            )

            # Verify real image was generated
            assert "stylized_image_url" in result
            assert result["stylized_image_url"].startswith("http")

            # Try to access the image URL (basic validation)
            import httpx
            async with httpx.AsyncClient() as http_client:
                response = await http_client.head(result["stylized_image_url"])
                assert response.status_code == 200
                assert "image" in response.headers.get("content-type", "").lower()

        finally:
            await client.disconnect()

    async def test_real_multi_style_generation(self, valid_test_image, test_config):
        """Test real multi-style generation."""
        if not test_config.openai_api_key:
            pytest.skip("OpenAI API key required for real integration test")

        client = E2EMCPClient(f"{test_config.base_url}/mcp")

        try:
            await client.connect()

            # Start trial session
            trial_result = await client.start_trial_session()
            session_id = trial_result["session_id"]

            # Generate multiple styles
            result = await client.stylize_image(
                image_base64=valid_test_image,
                user_prompt="a peaceful garden scene",
                session_id=session_id
            )

            # Verify multiple real images were generated
            assert result["multiple_styles"] is True
            assert len(result["images"]) == 4

            # Verify all images are accessible
            import httpx
            async with httpx.AsyncClient() as http_client:
                for image_data in result["images"]:
                    response = await http_client.head(image_data["stylized_image_url"])
                    assert response.status_code == 200
                    assert "image" in response.headers.get("content-type", "").lower()

        finally:
            await client.disconnect()
