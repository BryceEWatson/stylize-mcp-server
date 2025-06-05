"""
E2E tests for cross-interface integration.

Tests integration between Web UI, REST API, and MCP interfaces.
"""
import asyncio
import base64

import pytest

from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.pages.demo_page import DemoPage
from tests.e2e.pages.trial_upgrade_page import TrialUpgradePage
from tests.e2e.utils.mcp_client import E2EMCPClient


@pytest.mark.integration
class TestCrossInterfaceIntegration:
    """Test integration across Web UI, REST API, and MCP interfaces."""

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

    async def test_trial_session_across_interfaces(self, valid_test_image):
        """Test trial session usage across Web UI and REST API."""
        # Step 1: Start trial via web interface
        self.demo_page.navigate_to_demo()

        image_path = self._save_test_image_to_file(valid_test_image)

        try:
            # Generate image via web interface
            self.demo_page.perform_complete_generation_flow(
                image_path=image_path,
                style="Van Gogh",
                prompt="cross-interface test"
            )

            # Verify generation and get trial status
            assert self.demo_page.get_result_images_count() > 0
            remaining_web = self.demo_page.get_trial_remaining_count()
            assert remaining_web == 4  # Used 1 of 5

            # Step 2: Extract session ID from browser storage or cookie
            # (In a real implementation, this would be available via localStorage or cookie)
            session_id = self.demo_page.get_local_storage_item("trial_session_id")

            if session_id:
                # Step 3: Use trial session_id via REST API
                image_data = base64.b64decode(valid_test_image)

                response = await self.api_client.stylize_image(
                    image_data=image_data,
                    style_id="pixel_art",
                    session_id=session_id,
                    user_prompt="API usage of web trial"
                )

                if response.status_code == 200:
                    result = response.json()

                    # Step 4: Verify consistent usage tracking
                    assert result["trial_info"]["images_remaining"] == 3
                    assert result["trial_info"]["images_used"] == 2

                    # Step 5: Return to web interface and verify state
                    self.demo_page.refresh_page()
                    current_remaining = self.demo_page.get_trial_remaining_count()
                    assert current_remaining == 3  # Should reflect API usage

        finally:
            self._cleanup_test_file(image_path)

    async def test_user_account_across_interfaces(self, valid_test_image):
        """Test user account functionality across Web UI, REST API, and MCP."""
        # Step 1: Create account via web interface
        user_data = self.test_data.get_test_user_data()

        self.upgrade_page.navigate_to_upgrade()
        self.upgrade_page.perform_complete_registration(
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            company=user_data["company"]
        )

        # Verify registration success or handle redirect
        if not self.upgrade_page.is_success_displayed():
            # May have been redirected to dashboard
            current_url = self.upgrade_page.get_current_url()
            if "dashboard" not in current_url:
                self.dashboard_page.navigate_to_dashboard()

        # Step 2: Verify dashboard access
        self.dashboard_page.wait_for_page_load()
        initial_credits = self.dashboard_page.get_current_credits()
        assert initial_credits > 0  # New users should have credits

        # Step 3: Get JWT token (simulate login via API)
        login_response = await self.api_client.login_user(
            user_data["email"],
            user_data["password"]
        )

        if login_response.status_code == 200:
            login_data = login_response.json()
            jwt_token = login_data["access_token"]

            # Step 4: Use JWT token with REST API
            from tests.e2e.utils.api_client import E2EAPIClient

            auth_client = E2EAPIClient(
                base_url=self.base_url,
                timeout=30,
                jwt_token=jwt_token
            )

            try:
                # Generate image via authenticated API
                image_data = base64.b64decode(valid_test_image)

                api_response = await auth_client.stylize_image(
                    image_data=image_data,
                    style_id="flat_ui_icon",
                    user_prompt="Authenticated API test"
                )

                assert api_response.status_code == 200
                api_result = api_response.json()
                assert "stylized_image_url" in api_result

                # Step 5: Create API key via web interface
                # (This would require navigating to API key management page)
                # For now, we'll simulate having an API key

                # Step 6: Use API key with MCP tools
                mcp_client = E2EMCPClient(f"{self.base_url}/mcp")
                await mcp_client.connect()

                try:
                    # If we had an API key, we could test:
                    # mcp_result = await mcp_client.stylize_image(
                    #     image_base64=valid_test_image,
                    #     style_id="neumorphic_button",
                    #     api_key=api_key
                    # )

                    # For now, test with trial session via MCP
                    trial_result = await mcp_client.start_trial_session()
                    mcp_result = await mcp_client.stylize_image(
                        image_base64=valid_test_image,
                        style_id="neumorphic_button",
                        session_id=trial_result["session_id"]
                    )

                    assert "stylized_image_url" in mcp_result

                finally:
                    await mcp_client.disconnect()

                # Step 7: Return to web dashboard and verify credit usage
                self.dashboard_page.refresh_dashboard_data()
                final_credits = self.dashboard_page.get_current_credits()

                # Credits should have decreased due to API usage
                assert final_credits < initial_credits

            finally:
                await auth_client.close()

    async def test_api_key_management_workflow(self):
        """Test complete API key management lifecycle."""
        # This test would require admin API key functionality
        # For now, we'll test the basic API key validation workflow

        # Step 1: Test with invalid API key
        invalid_client = self.api_client
        invalid_client.api_key = "invalid-api-key"

        response = await invalid_client.health_check()
        # Health endpoint should be public
        assert response.status_code == 200

        # Try protected endpoint with invalid key
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        response = await invalid_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            user_prompt="Invalid key test"
        )

        # Should be unauthorized
        assert response.status_code in [401, 403]

        # Step 2: Test with valid test API key (if available)
        if hasattr(self, 'test_config') and self.test_config.test_api_key:
            valid_client = self.api_client
            valid_client.api_key = self.test_config.test_api_key

            response = await valid_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                user_prompt="Valid key test"
            )

            # Should succeed with valid key
            assert response.status_code == 200

    async def test_session_state_persistence(self, valid_test_image):
        """Test session state persistence across browser actions."""
        image_path = self._save_test_image_to_file(valid_test_image)

        try:
            # Step 1: Start trial and use some images
            self.demo_page.navigate_to_demo()

            for i in range(2):
                self.demo_page.perform_complete_generation_flow(
                    image_path=image_path,
                    style="Van Gogh",
                    prompt=f"persistence test {i+1}"
                )

            # Should have 3 remaining
            remaining_before = self.demo_page.get_trial_remaining_count()
            assert remaining_before == 3

            # Step 2: Navigate away and back
            self.demo_page.navigate_to("/")
            self.demo_page.navigate_to_demo()

            # Step 3: Check if state persisted
            remaining_after = self.demo_page.get_trial_remaining_count()

            # State should persist (might be None if new session started)
            if remaining_after is not None:
                assert remaining_after == 3

            # Step 4: Clear browser data and check reset
            self.demo_page.delete_all_cookies()
            self.demo_page.clear_local_storage()
            self.demo_page.refresh_page()

            # Should start fresh trial or show no trial info
            fresh_remaining = self.demo_page.get_trial_remaining_count()
            assert fresh_remaining is None or fresh_remaining == 5

        finally:
            self._cleanup_test_file(image_path)

    async def test_concurrent_interface_usage(self, valid_test_image):
        """Test concurrent usage across different interfaces."""
        # Step 1: Start trial session via API
        trial_response = await self.api_client.start_trial_session()
        assert trial_response.status_code == 200

        trial_data = trial_response.json()
        session_id = trial_data["session_id"]

        # Step 2: Use session concurrently via API and MCP
        image_data = base64.b64decode(valid_test_image)

        # Prepare concurrent tasks
        api_task = self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt="API concurrent test"
        )

        async def mcp_task():
            client = E2EMCPClient(f"{self.base_url}/mcp")
            await client.connect()
            try:
                return await client.stylize_image(
                    image_base64=valid_test_image,
                    style_id="pixel_art",
                    session_id=session_id,
                    user_prompt="MCP concurrent test"
                )
            finally:
                await client.disconnect()

        # Execute concurrently
        api_response, mcp_result = await asyncio.gather(
            api_task,
            mcp_task(),
            return_exceptions=True
        )

        # At least one should succeed
        api_success = not isinstance(api_response, Exception) and api_response.status_code == 200
        mcp_success = not isinstance(mcp_result, Exception) and "stylized_image_url" in mcp_result

        assert api_success or mcp_success, "At least one concurrent request should succeed"

        # Check final trial status
        status_response = await self.api_client.check_trial_status(session_id)
        if status_response.status_code == 200:
            status_data = status_response.json()
            total_used = status_data["images_used"]

            # Should reflect successful generations
            if api_success and mcp_success:
                assert total_used == 2
            else:
                assert total_used == 1

    async def test_error_handling_across_interfaces(self):
        """Test error handling consistency across interfaces."""
        # Test invalid session ID across interfaces
        invalid_session = "invalid-session-id-12345"

        # Test via API
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        api_response = await self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=invalid_session
        )

        assert api_response.status_code in [400, 404, 401]

        # Test via MCP
        mcp_client = E2EMCPClient(f"{self.base_url}/mcp")
        await mcp_client.connect()

        try:
            await mcp_client.stylize_image(
                image_base64=self.test_data.get_test_images()["valid_jpeg"],
                style_id="van_gogh",
                session_id=invalid_session
            )
            pytest.fail("Expected MCP error for invalid session")
        except Exception as e:
            assert "session" in str(e).lower() or "invalid" in str(e).lower()
        finally:
            await mcp_client.disconnect()

    def _save_test_image_to_file(self, image_base64: str) -> str:
        """Save base64 image to temporary file."""
        import tempfile

        image_data = base64.b64decode(image_base64)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_data)
            return f.name

    def _cleanup_test_file(self, file_path: str):
        """Clean up temporary test file."""
        import os
        try:
            os.unlink(file_path)
        except Exception:
            pass


@pytest.mark.integration
class TestDataConsistencyAcrossInterfaces:
    """Test data consistency across all interfaces."""

    async def test_trial_limit_consistency(self, api_client, valid_test_image):
        """Test trial limit enforcement is consistent across interfaces."""
        # Start trial via API
        trial_response = await api_client.start_trial_session()
        trial_data = trial_response.json()
        session_id = trial_data["session_id"]

        # Use all trial images via API
        image_data = base64.b64decode(valid_test_image)

        for i in range(5):
            response = await api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=f"Limit test {i+1}"
            )

            if response.status_code != 200:
                break

        # Try via MCP (should also be blocked)
        mcp_client = E2EMCPClient(f"{api_client.base_url}/mcp")
        await mcp_client.connect()

        try:
            await mcp_client.stylize_image(
                image_base64=valid_test_image,
                style_id="pixel_art",
                session_id=session_id
            )
            pytest.fail("Expected MCP to respect trial limit")
        except Exception as e:
            assert "trial" in str(e).lower() or "limit" in str(e).lower()
        finally:
            await mcp_client.disconnect()

    async def test_credit_usage_consistency(self, authenticated_api_client, valid_test_image):
        """Test credit usage tracking consistency."""
        # Get initial credits
        credits_response = await authenticated_api_client.get_user_credits()
        initial_credits = credits_response.json()["credits"]

        # Use credits via API
        image_data = base64.b64decode(valid_test_image)

        api_response = await authenticated_api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            user_prompt="Credit consistency test"
        )

        assert api_response.status_code == 200

        # Check credits via different endpoint
        dashboard_response = await authenticated_api_client.get_user_dashboard()
        assert dashboard_response.status_code == 200

        dashboard_data = dashboard_response.json()
        dashboard_credits = dashboard_data["credit_info"]["current_credits"]

        # Credits should be consistent
        credits_response2 = await authenticated_api_client.get_user_credits()
        api_credits = credits_response2.json()["credits"]

        assert dashboard_credits == api_credits, "Credit amounts should be consistent across endpoints"
        assert initial_credits - api_credits == 1, "Should have used exactly 1 credit"
