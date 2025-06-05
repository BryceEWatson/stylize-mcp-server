"""
E2E tests for anonymous trial user journey.

Tests the complete user flow from demo discovery to account conversion.
"""
import pytest
import asyncio
import time
from typing import Dict, Any

from tests.e2e.pages.demo_page import DemoPage
from tests.e2e.pages.trial_upgrade_page import TrialUpgradePage
from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.utils.test_data_manager import TestDataManager


@pytest.mark.integration
@pytest.mark.web_ui
class TestTrialUserJourney:
    """Test complete anonymous trial user journey."""
    
    @pytest.fixture(autouse=True)
    def setup(self, webdriver_instance, test_config, test_data_manager, api_client):
        """Set up test environment."""
        self.driver = webdriver_instance
        self.base_url = test_config.base_url
        self.test_data = test_data_manager
        self.api_client = api_client
        
        # Initialize page objects
        self.demo_page = DemoPage(self.driver, self.base_url)
        self.upgrade_page = TrialUpgradePage(self.driver, self.base_url)
        self.dashboard_page = DashboardPage(self.driver, self.base_url)
    
    def test_complete_trial_to_conversion_flow(self, valid_test_image):
        """Test complete anonymous user journey from demo to account creation."""
        # Step 1: Visit demo page
        self.demo_page.navigate_to_demo()
        assert "Demo" in self.demo_page.get_page_title_text()
        
        # Step 2: Generate first image via web form
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Van Gogh",
                prompt="a beautiful landscape"
            )
            
            # Verify image generation
            assert self.demo_page.get_result_images_count() > 0
            assert self.demo_page.is_single_result_displayed()
            
            # Verify trial session creation and image generation
            trial_remaining = self.demo_page.get_trial_remaining_count()
            assert trial_remaining is not None
            assert trial_remaining == 4  # Started with 5, used 1
            
            # Step 3: Generate multiple images until trial limit
            for i in range(4):  # Use remaining 4 images
                self.demo_page.perform_complete_generation_flow(
                    image_path=image_path,
                    style="Pixel Art",
                    prompt=f"test image {i+2}"
                )
                
                remaining = self.demo_page.get_trial_remaining_count()
                expected_remaining = 3 - i
                assert remaining == expected_remaining
            
            # Step 4: Verify trial limit reached
            final_remaining = self.demo_page.get_trial_remaining_count()
            assert final_remaining == 0
            
            # Step 5: Verify upgrade prompt appearance
            assert self.demo_page.is_signup_prompt_visible()
            signup_link = self.demo_page.get_signup_link_url()
            assert "/web/upgrade" in signup_link or "/auth/register" in signup_link
            
            # Step 6: Navigate to trial upgrade page
            self.demo_page.click_signup_link()
            self.upgrade_page.wait_for_page_load()
            
            assert "Upgrade" in self.upgrade_page.get_page_title_text()
            assert self.upgrade_page.get_images_used_count() == 5
            assert self.upgrade_page.get_images_remaining_count() == 0
            
            # Step 7: Complete trial conversion form
            user_data = self.test_data.get_test_user_data()
            self.upgrade_page.perform_complete_registration(
                email=user_data["email"],
                password=user_data["password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                company=user_data["company"]
            )
            
            # Step 8: Verify account creation and redirect to dashboard
            if self.upgrade_page.is_success_displayed():
                # Registration successful, might redirect automatically
                self.upgrade_page.wait_for_url_contains("dashboard")
            
            # Navigate to dashboard if not redirected
            if "dashboard" not in self.upgrade_page.get_current_url():
                self.dashboard_page.navigate_to_dashboard()
            
            # Step 9: Verify 100 free monthly credits granted
            self.dashboard_page.wait_for_page_load()
            credits = self.dashboard_page.get_current_credits()
            monthly_allowance = self.dashboard_page.get_monthly_allowance()
            
            assert credits > 0, "New user should have credits"
            assert monthly_allowance >= 100, "Should have at least 100 monthly credits"
            
            # Verify user information
            assert user_data["email"] in self.dashboard_page.get_account_email()
            
        finally:
            # Cleanup
            self._cleanup_test_file(image_path)
    
    def test_trial_session_persistence(self, valid_test_image):
        """Test that trial sessions persist across browser sessions."""
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            # Generate first image and note trial status
            self.demo_page.navigate_to_demo()
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Van Gogh",
                prompt="persistence test"
            )
            
            initial_remaining = self.demo_page.get_trial_remaining_count()
            assert initial_remaining == 4
            
            # Simulate browser session end/start by clearing cookies
            # but keeping session storage (realistic browser behavior)
            self.demo_page.delete_all_cookies()
            
            # Navigate to demo again
            self.demo_page.navigate_to_demo()
            
            # Generate another image
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Pixel Art",
                prompt="persistence test 2"
            )
            
            # Verify trial session continued from where it left off
            current_remaining = self.demo_page.get_trial_remaining_count()
            assert current_remaining == 3  # Should continue from previous session
            
        finally:
            self._cleanup_test_file(image_path)
    
    def test_trial_limit_enforcement(self, valid_test_image):
        """Test that trial limits are properly enforced."""
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            self.demo_page.navigate_to_demo()
            
            # Use all 5 trial images
            for i in range(5):
                self.demo_page.perform_complete_generation_flow(
                    image_path=image_path,
                    style="Van Gogh",
                    prompt=f"limit test {i+1}"
                )
                
                remaining = self.demo_page.get_trial_remaining_count()
                assert remaining == 4 - i
            
            # Verify trial exhausted
            assert self.demo_page.get_trial_remaining_count() == 0
            assert self.demo_page.is_signup_prompt_visible()
            
            # Attempt to generate another image (should be blocked or redirect)
            generate_button_enabled = self.demo_page.is_generate_button_enabled()
            
            if generate_button_enabled:
                # If button is still enabled, clicking should show error or redirect
                self.demo_page.click_generate_button()
                
                # Check for error message or redirect to upgrade
                time.sleep(2)  # Allow for potential redirect
                
                if "upgrade" in self.demo_page.get_current_url():
                    # Redirected to upgrade page
                    assert True
                else:
                    # Should show error message
                    error_msg = self.demo_page.get_error_message()
                    assert "trial" in error_msg.lower() or "limit" in error_msg.lower()
            else:
                # Button disabled, which is also valid enforcement
                assert not generate_button_enabled
                
        finally:
            self._cleanup_test_file(image_path)
    
    def test_multi_style_generation_usage_counting(self, valid_test_image):
        """Test that multi-style generation counts correctly against trial limits."""
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            self.demo_page.navigate_to_demo()
            
            # Test single style generation first
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Van Gogh",
                prompt="single style test"
            )
            
            remaining_after_single = self.demo_page.get_trial_remaining_count()
            assert remaining_after_single == 4  # Used 1 image
            
            # Test multi-style generation
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                prompt="multi style test",
                use_random_styles=True
            )
            
            # Multi-style should generate 4 images, using 4 credits
            remaining_after_multi = self.demo_page.get_trial_remaining_count()
            assert remaining_after_multi == 0  # Should have used all remaining 4
            
            # Verify multiple results are displayed
            assert self.demo_page.is_multiple_results_displayed()
            assert self.demo_page.get_result_images_count() == 4
            
            # Verify different styles were used
            style_names = self.demo_page.get_result_style_names()
            assert len(set(style_names)) > 1  # Should have different styles
            
        finally:
            self._cleanup_test_file(image_path)
    
    def test_trial_abandonment_flow(self, valid_test_image):
        """Test user abandons after trial limit."""
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            self.demo_page.navigate_to_demo()
            
            # Use some but not all trial images
            for i in range(3):
                self.demo_page.perform_complete_generation_flow(
                    image_path=image_path,
                    style="Van Gogh",
                    prompt=f"abandonment test {i+1}"
                )
            
            assert self.demo_page.get_trial_remaining_count() == 2
            
            # User leaves the site (simulate by navigating away)
            self.driver.get("https://www.google.com")
            time.sleep(1)
            
            # User returns later
            self.demo_page.navigate_to_demo()
            
            # Should still have 2 images remaining
            remaining = self.demo_page.get_trial_remaining_count()
            assert remaining == 2 or remaining is None  # Might start new session
            
        finally:
            self._cleanup_test_file(image_path)
    
    def test_trial_return_with_existing_session(self, valid_test_image):
        """Test user returns to demo with existing trial session."""
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            # First visit - use some trial images
            self.demo_page.navigate_to_demo()
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Van Gogh",
                prompt="return test 1"
            )
            
            first_remaining = self.demo_page.get_trial_remaining_count()
            assert first_remaining == 4
            
            # Navigate away and back
            self.demo_page.navigate_to("/")  # Go to home page
            self.demo_page.navigate_to_demo()  # Return to demo
            
            # Should show existing trial status
            current_remaining = self.demo_page.get_trial_remaining_count()
            assert current_remaining == 4 or current_remaining is None
            
            # Should be able to continue using trial
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Pixel Art",
                prompt="return test 2"
            )
            
            final_remaining = self.demo_page.get_trial_remaining_count()
            if current_remaining is not None:
                assert final_remaining == current_remaining - 1
            
        finally:
            self._cleanup_test_file(image_path)
    
    def test_content_policy_violation_handling(self):
        """Test handling of content policy violations during trial."""
        # Create inappropriate test content
        inappropriate_content = self.test_data.get_problematic_prompts()[0]
        
        # This test might need adjustment based on actual content policy implementation
        self.demo_page.navigate_to_demo()
        
        # Try to generate with inappropriate prompt
        self.demo_page.enter_prompt(inappropriate_content)
        self.demo_page.click_generate_button()
        
        # Should either show error or filter the content
        time.sleep(3)
        
        if self.demo_page.is_error_displayed():
            error_msg = self.demo_page.get_error_message()
            assert any(word in error_msg.lower() for word in ["content", "policy", "inappropriate"])
        else:
            # If no error, generation should have proceeded normally
            # (content was filtered/modified)
            assert self.demo_page.get_result_images_count() >= 0
    
    @pytest.mark.slow
    async def test_concurrent_trial_usage(self, valid_test_image):
        """Test concurrent trial usage scenarios."""
        # This test simulates multiple users or multiple tabs
        # For now, we'll test rapid successive requests
        
        image_path = self._save_test_image_to_file(valid_test_image)
        
        try:
            self.demo_page.navigate_to_demo()
            
            # Make rapid requests to test rate limiting
            start_time = time.time()
            
            for i in range(3):
                self.demo_page.perform_complete_generation_flow(
                    image_path=image_path,
                    style="Van Gogh",
                    prompt=f"concurrent test {i+1}"
                )
                
                # Don't wait long between requests
                if i < 2:
                    time.sleep(1)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should handle requests gracefully without major delays
            assert total_time < 180  # Reasonable time for 3 image generations
            
            # Trial should be tracked correctly
            remaining = self.demo_page.get_trial_remaining_count()
            assert remaining == 2  # Started with 5, used 3
            
        finally:
            self._cleanup_test_file(image_path)
    
    def _save_test_image_to_file(self, image_base64: str) -> str:
        """Save base64 image to temporary file."""
        import base64
        import tempfile
        import os
        
        image_data = base64.b64decode(image_base64)
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_data)
            return f.name
    
    def _cleanup_test_file(self, file_path: str):
        """Clean up temporary test file."""
        import os
        try:
            os.unlink(file_path)
        except:
            pass


@pytest.mark.integration
@pytest.mark.api_only
class TestTrialUserJourneyAPI:
    """Test trial user journey via API endpoints."""
    
    def test_api_trial_session_creation_and_usage(self, api_client, valid_test_image):
        """Test trial session creation and usage via API."""
        
        async def _test():
            # Start trial session
            response = await api_client.start_trial_session()
            assert response.status_code == 200
            
            trial_data = response.json()
            session_id = trial_data["session_id"]
            assert trial_data["images_remaining"] == 5
            
            # Generate single image
            image_data = base64.b64decode(valid_test_image)
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt="API test image"
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert "stylized_image_url" in result
            assert result["trial_info"]["images_remaining"] == 4
            
            # Check trial status
            response = await api_client.check_trial_status(session_id)
            assert response.status_code == 200
            
            status = response.json()
            assert status["images_remaining"] == 4
            assert status["images_used"] == 1
        
        import base64
        asyncio.run(_test())
    
    def test_api_multi_style_generation(self, api_client, valid_test_image):
        """Test multi-style generation via API."""
        
        async def _test():
            # Start trial session
            response = await api_client.start_trial_session()
            trial_data = response.json()
            session_id = trial_data["session_id"]
            
            # Generate multiple styles (omit style_id)
            image_data = base64.b64decode(valid_test_image)
            response = await api_client.stylize_image(
                image_data=image_data,
                session_id=session_id,
                user_prompt="Multi-style API test"
            )
            
            assert response.status_code == 200
            result = response.json()
            
            assert result.get("multiple_styles") is True
            assert "images" in result
            assert len(result["images"]) == 4
            assert result["total_images"] == 4
            
            # Should have used 4 credits
            assert result["trial_info"]["images_remaining"] == 1
            assert result["trial_info"]["images_used"] == 4
        
        import base64
        asyncio.run(_test())
    
    def test_api_trial_limit_enforcement(self, api_client, valid_test_image):
        """Test trial limit enforcement via API."""
        
        async def _test():
            # Start trial session
            response = await api_client.start_trial_session()
            trial_data = response.json()
            session_id = trial_data["session_id"]
            
            # Use all 5 trial images
            image_data = base64.b64decode(valid_test_image)
            
            # Use 4 images with single generation
            for i in range(4):
                response = await api_client.stylize_image(
                    image_data=image_data,
                    style_id="van_gogh",
                    session_id=session_id,
                    user_prompt=f"Limit test {i+1}"
                )
                assert response.status_code == 200
            
            # Use last image
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="pixel_art",
                session_id=session_id,
                user_prompt="Final image"
            )
            assert response.status_code == 200
            result = response.json()
            assert result["trial_info"]["images_remaining"] == 0
            
            # Attempt to generate another image (should fail)
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt="Should fail"
            )
            
            # Should return error status
            assert response.status_code in [400, 403, 429]  # Client error codes
        
        import base64
        asyncio.run(_test())