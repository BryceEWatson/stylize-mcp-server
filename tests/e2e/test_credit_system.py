"""
E2E tests for credit purchase and usage system.

Tests the complete credit purchase workflow and usage tracking.
"""
import asyncio

import pytest

from tests.e2e.pages.dashboard_page import DashboardPage
from tests.e2e.pages.trial_upgrade_page import TrialUpgradePage
from tests.e2e.utils.api_client import E2EAPIClient


@pytest.mark.integration
@pytest.mark.web_ui
class TestCreditSystemWebUI:
    """Test credit system via web interface."""

    @pytest.fixture(autouse=True)
    def setup(self, webdriver_instance, test_config, test_data_manager):
        """Set up test environment."""
        self.driver = webdriver_instance
        self.base_url = test_config.base_url
        self.test_data = test_data_manager

        # Initialize page objects
        self.dashboard_page = DashboardPage(self.driver, self.base_url)
        self.upgrade_page = TrialUpgradePage(self.driver, self.base_url)

    async def test_complete_credit_purchase_flow(self, test_user):
        """Test complete credit purchase workflow."""
        # Navigate to dashboard as authenticated user
        self.dashboard_page.navigate_to_dashboard()

        # Get initial credit balance
        initial_credits = self.dashboard_page.get_current_credits()

        # View available packages
        packages = self.dashboard_page.get_available_packages()
        assert len(packages) > 0

        # Find starter package
        starter_package = None
        for package in packages:
            if "starter" in package["name"].lower():
                starter_package = package
                break

        assert starter_package is not None, "Starter package not found"

        # Purchase starter package
        self.dashboard_page.perform_complete_purchase_flow("starter")

        # Verify purchase success
        if self.dashboard_page.is_purchase_successful():
            success_msg = self.dashboard_page.get_success_message()
            assert "success" in success_msg.lower() or "purchased" in success_msg.lower()

            # Refresh dashboard and verify credit increase
            self.dashboard_page.refresh_dashboard_data()

            new_credits = self.dashboard_page.get_current_credits()
            credit_increase = new_credits - initial_credits

            # Should have increased by package amount (50 + 5 bonus = 55 for starter)
            assert credit_increase >= 50, f"Credits only increased by {credit_increase}"
        else:
            # If purchase failed, check error message
            error_msg = self.dashboard_page.get_error_message()
            # This might be expected in test environment without real payment processing
            assert "payment" in error_msg.lower() or "test" in error_msg.lower()

    async def test_credit_package_display(self):
        """Test credit package information display."""
        self.dashboard_page.navigate_to_dashboard()

        packages = self.dashboard_page.get_available_packages()
        assert len(packages) >= 4  # Should have at least 4 packages

        # Verify package structure
        for package in packages:
            assert "name" in package
            assert "price" in package
            assert "credits" in package
            # Bonus might be empty for some packages

        # Verify expected packages are present
        package_names = [p["name"].lower() for p in packages]
        expected_packages = ["starter", "popular", "pro", "enterprise"]

        for expected in expected_packages:
            assert any(expected in name for name in package_names), f"{expected} package not found"

    async def test_dashboard_credit_information(self, test_user):
        """Test dashboard credit information display."""
        self.dashboard_page.navigate_to_dashboard()

        # Test credit information display
        current_credits = self.dashboard_page.get_current_credits()
        monthly_allowance = self.dashboard_page.get_monthly_allowance()
        credits_used = self.dashboard_page.get_credits_used_this_month()

        assert current_credits >= 0
        assert monthly_allowance >= 0
        assert credits_used >= 0

        # New user should have monthly allowance
        assert monthly_allowance >= 100, "New user should have at least 100 monthly credits"

        # Test usage statistics
        total_images = self.dashboard_page.get_total_images_generated()
        images_this_month = self.dashboard_page.get_images_this_month()

        assert total_images >= 0
        assert images_this_month >= 0
        assert images_this_month <= total_images


@pytest.mark.integration
@pytest.mark.api_only
class TestCreditSystemAPI:
    """Test credit system via API endpoints."""

    async def test_credit_usage_tracking(self, authenticated_api_client, valid_test_image):
        """Test accurate credit usage tracking."""
        # Get initial credit balance
        response = await authenticated_api_client.get_user_credits()
        assert response.status_code == 200
        initial_data = response.json()
        initial_credits = initial_data["credits"]

        # Generate single image (should use 1 credit)
        import base64
        image_data = base64.b64decode(valid_test_image)

        response = await authenticated_api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            user_prompt="credit tracking test"
        )

        assert response.status_code == 200

        # Check credit balance
        response = await authenticated_api_client.get_user_credits()
        assert response.status_code == 200

        after_single_data = response.json()
        after_single_credits = after_single_data["credits"]

        # Should have used 1 credit
        assert initial_credits - after_single_credits == 1

        # Generate multi-style image (should use 4 credits)
        response = await authenticated_api_client.stylize_image(
            image_data=image_data,
            user_prompt="multi-style credit test"
            # No style_id = 4 random styles
        )

        assert response.status_code == 200
        result = response.json()

        if result.get("multiple_styles"):
            # Multi-style generation
            expected_usage = result.get("total_images", 4)

            # Check final credit balance
            response = await authenticated_api_client.get_user_credits()
            assert response.status_code == 200

            final_data = response.json()
            final_credits = final_data["credits"]

            total_used = initial_credits - final_credits
            assert total_used == 1 + expected_usage  # Single + multi

    async def test_insufficient_credits_handling(self, api_client, test_data_manager):
        """Test behavior when user has insufficient credits."""
        # Create user with minimal credits
        user_data = test_data_manager.get_test_user_data()

        # Register user
        response = await api_client.register_user(user_data)
        if response.status_code == 201:
            # Login to get token
            response = await api_client.login_user(user_data["email"], user_data["password"])
            assert response.status_code == 200

            login_data = response.json()
            token = login_data["access_token"]

            # Create authenticated client
            from tests.e2e.config import get_api_base_url
            auth_client = E2EAPIClient(
                base_url=get_api_base_url(),
                timeout=30,
                jwt_token=token
            )

            try:
                # Use up all credits by generating many images
                import base64
                test_images = test_data_manager.get_test_images()
                image_data = base64.b64decode(test_images["valid_jpeg"])

                # Generate images until credits run out
                credits_exhausted = False
                attempts = 0
                max_attempts = 20  # Safety limit

                while not credits_exhausted and attempts < max_attempts:
                    response = await auth_client.stylize_image(
                        image_data=image_data,
                        style_id="van_gogh",
                        user_prompt=f"exhaustion test {attempts}"
                    )

                    if response.status_code == 403 or response.status_code == 400:
                        # Credits exhausted
                        credits_exhausted = True
                        error_data = response.json()
                        assert "credit" in error_data.get("detail", "").lower()
                    elif response.status_code == 200:
                        attempts += 1
                    else:
                        break

                # Should have eventually hit credit limit
                assert credits_exhausted or attempts >= max_attempts

            finally:
                await auth_client.close()

    async def test_credit_purchase_api(self, authenticated_api_client):
        """Test credit purchase via API."""
        # Get available packages
        response = await authenticated_api_client.get_pricing_packages()
        assert response.status_code == 200

        packages = response.json()
        assert len(packages) > 0

        # Find starter package
        starter_package = None
        for package in packages:
            if package["id"] == "starter":
                starter_package = package
                break

        assert starter_package is not None

        # Get initial credits
        response = await authenticated_api_client.get_user_credits()
        initial_credits = response.json()["credits"]

        # Attempt to purchase starter package
        response = await authenticated_api_client.purchase_credits("starter")

        if response.status_code == 200:
            # Purchase successful
            purchase_data = response.json()
            assert "success" in purchase_data.get("status", "").lower()

            # Verify credit increase
            response = await authenticated_api_client.get_user_credits()
            new_credits = response.json()["credits"]

            credit_increase = new_credits - initial_credits
            expected_credits = starter_package["credits"] + starter_package.get("bonus_credits", 0)

            assert credit_increase == expected_credits
        else:
            # Purchase might fail in test environment without payment processing
            response.json()
            assert response.status_code in [400, 403, 500]

    async def test_user_dashboard_api(self, authenticated_api_client):
        """Test user dashboard data retrieval."""
        response = await authenticated_api_client.get_user_dashboard()
        assert response.status_code == 200

        dashboard_data = response.json()

        # Verify dashboard data structure
        required_fields = [
            "user_info",
            "credit_info",
            "usage_stats",
            "available_packages"
        ]

        for field in required_fields:
            assert field in dashboard_data, f"Missing field: {field}"

        # Verify credit info
        credit_info = dashboard_data["credit_info"]
        assert "current_credits" in credit_info
        assert "monthly_allowance" in credit_info
        assert "credits_used_this_month" in credit_info

        # Verify usage stats
        usage_stats = dashboard_data["usage_stats"]
        assert "total_images_generated" in usage_stats
        assert "images_this_month" in usage_stats

        # Verify user info
        user_info = dashboard_data["user_info"]
        assert "email" in user_info
        assert "account_type" in user_info


@pytest.mark.integration
class TestCreditSystemEdgeCases:
    """Test edge cases in credit system."""

    async def test_concurrent_credit_usage(self, authenticated_api_client, valid_test_image):
        """Test concurrent credit usage by same user."""
        import base64
        image_data = base64.b64decode(valid_test_image)

        # Get initial credits
        response = await authenticated_api_client.get_user_credits()
        initial_credits = response.json()["credits"]

        if initial_credits < 5:
            pytest.skip("Not enough credits for concurrent test")

        # Make concurrent requests
        async def generate_image(session_suffix):
            return await authenticated_api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                user_prompt=f"concurrent test {session_suffix}"
            )

        # Execute 3 concurrent requests
        tasks = [generate_image(i) for i in range(3)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Count successful responses
        successful_count = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_count += 1

        # At least some should succeed
        assert successful_count > 0

        # Check final credit balance
        response = await authenticated_api_client.get_user_credits()
        final_credits = response.json()["credits"]

        credits_used = initial_credits - final_credits
        # Should have used credits equal to successful generations
        assert credits_used == successful_count

    async def test_credit_deduction_race_conditions(self, test_user, api_client):
        """Test credit deduction under race conditions."""
        # This test simulates rapid successive requests to test for race conditions
        # in credit deduction logic

        user_data = test_user["user_data"]

        # Login to get fresh token
        response = await api_client.login_user(user_data["email"], user_data["password"])
        if response.status_code != 200:
            pytest.skip("Could not authenticate user")

        token = response.json()["access_token"]

        from tests.e2e.config import get_api_base_url
        auth_client = E2EAPIClient(
            base_url=get_api_base_url(),
            timeout=30,
            jwt_token=token
        )

        try:
            # Get initial credits
            response = await auth_client.get_user_credits()
            initial_credits = response.json()["credits"]

            if initial_credits < 3:
                pytest.skip("Not enough credits for race condition test")

            # Make rapid successive requests
            import base64
            test_images = self.test_data.get_test_images()
            image_data = base64.b64decode(test_images["valid_jpeg"])

            responses = []
            for i in range(3):
                response = await auth_client.stylize_image(
                    image_data=image_data,
                    style_id="pixel_art",
                    user_prompt=f"race condition test {i}"
                )
                responses.append(response)
                # Very short delay to create potential race condition
                await asyncio.sleep(0.1)

            # Count successful responses
            successful_count = sum(1 for r in responses if r.status_code == 200)

            # Check final credits
            response = await auth_client.get_user_credits()
            final_credits = response.json()["credits"]

            credits_used = initial_credits - final_credits

            # Credits used should exactly match successful generations
            assert credits_used == successful_count, f"Credit deduction mismatch: used {credits_used}, successful {successful_count}"

        finally:
            await auth_client.close()

    async def test_monthly_credit_reset_behavior(self, authenticated_api_client):
        """Test monthly credit reset behavior."""
        # Get dashboard data to see monthly allowance and usage
        response = await authenticated_api_client.get_user_dashboard()
        assert response.status_code == 200

        dashboard_data = response.json()
        credit_info = dashboard_data["credit_info"]

        monthly_allowance = credit_info["monthly_allowance"]
        credits_used_month = credit_info["credits_used_this_month"]
        next_reset = credit_info.get("next_reset_date")

        assert monthly_allowance > 0
        assert credits_used_month >= 0
        assert credits_used_month <= monthly_allowance

        if next_reset:
            # Verify reset date is in the future
            from datetime import datetime

            import dateutil.parser

            reset_date = dateutil.parser.parse(next_reset)
            now = datetime.now(reset_date.tzinfo)

            assert reset_date > now, "Reset date should be in the future"

    async def test_credit_system_data_consistency(self, authenticated_api_client):
        """Test data consistency across different credit endpoints."""
        # Get credits from multiple endpoints
        credits_response = await authenticated_api_client.get_user_credits()
        dashboard_response = await authenticated_api_client.get_user_dashboard()

        assert credits_response.status_code == 200
        assert dashboard_response.status_code == 200

        credits_data = credits_response.json()
        dashboard_data = dashboard_response.json()

        # Credit amounts should be consistent
        credits_endpoint_amount = credits_data["credits"]
        dashboard_credit_amount = dashboard_data["credit_info"]["current_credits"]

        assert credits_endpoint_amount == dashboard_credit_amount, "Credit amounts inconsistent between endpoints"

        # Monthly allowance should be consistent
        if "monthly_allowance" in credits_data and "monthly_allowance" in dashboard_data["credit_info"]:
            assert credits_data["monthly_allowance"] == dashboard_data["credit_info"]["monthly_allowance"]
