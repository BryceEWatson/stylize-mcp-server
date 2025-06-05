"""
Trial upgrade page object for E2E testing.
"""
from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage


class TrialUpgradePage(BasePage):
    """Page object for the trial upgrade page (/web/upgrade)."""

    # Page URL
    PAGE_PATH = "/web/upgrade"

    # Locators
    PAGE_TITLE = (By.TAG_NAME, "h1")
    SUBTITLE = (By.CLASS_NAME, "subtitle")

    # Trial status section
    TRIAL_STATUS_SECTION = (By.ID, "trial-status")
    IMAGES_USED = (By.ID, "images-used")
    IMAGES_REMAINING = (By.ID, "images-remaining")
    TRIAL_MESSAGE = (By.CLASS_NAME, "trial-message")

    # Benefits section
    BENEFITS_SECTION = (By.ID, "benefits-section")
    BENEFIT_ITEMS = (By.CSS_SELECTOR, ".benefit-item")
    FREE_ACCOUNT_BENEFITS = (By.ID, "free-benefits")
    CREDIT_PACKAGE_BENEFITS = (By.ID, "credit-benefits")

    # Registration form
    REGISTRATION_FORM = (By.ID, "registration-form")
    EMAIL_INPUT = (By.ID, "email")
    PASSWORD_INPUT = (By.ID, "password")
    CONFIRM_PASSWORD_INPUT = (By.ID, "confirm-password")
    FIRST_NAME_INPUT = (By.ID, "first-name")
    LAST_NAME_INPUT = (By.ID, "last-name")
    COMPANY_INPUT = (By.ID, "company")

    # Form validation
    EMAIL_ERROR = (By.ID, "email-error")
    PASSWORD_ERROR = (By.ID, "password-error")
    CONFIRM_PASSWORD_ERROR = (By.ID, "confirm-password-error")
    FIRST_NAME_ERROR = (By.ID, "first-name-error")
    LAST_NAME_ERROR = (By.ID, "last-name-error")
    FORM_ERRORS = (By.CSS_SELECTOR, ".field-error")

    # Terms and privacy
    TERMS_CHECKBOX = (By.ID, "terms")
    TERMS_LABEL = (By.CSS_SELECTOR, "label[for='terms']")
    TERMS_LINK = (By.CSS_SELECTOR, "a[href*='terms']")
    PRIVACY_LINK = (By.CSS_SELECTOR, "a[href*='privacy']")

    # Submit button
    SUBMIT_BUTTON = (By.ID, "submit-btn")
    SUBMIT_STATUS = (By.ID, "submit-status")

    # Success/Error messages
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    GENERAL_ERROR = (By.ID, "general-error")

    # Alternative options
    ALREADY_HAVE_ACCOUNT = (By.ID, "already-have-account")
    LOGIN_LINK = (By.CSS_SELECTOR, "a[href*='login']")
    CONTINUE_TRIAL_LINK = (By.ID, "continue-trial")
    VIEW_PRICING_LINK = (By.CSS_SELECTOR, "a[href*='pricing']")

    # Loading states
    LOADING_SPINNER = (By.CLASS_NAME, "loading-spinner")
    FORM_DISABLED_OVERLAY = (By.CLASS_NAME, "form-disabled")

    def navigate_to_upgrade(self):
        """Navigate to trial upgrade page."""
        return self.navigate_to(self.PAGE_PATH)

    def get_page_title_text(self) -> str:
        """Get page title text."""
        return self.get_text(self.PAGE_TITLE)

    def get_images_used_count(self) -> int:
        """Get number of images used in trial."""
        text = self.get_text(self.IMAGES_USED)
        import re
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0

    def get_images_remaining_count(self) -> int:
        """Get number of images remaining in trial."""
        text = self.get_text(self.IMAGES_REMAINING)
        import re
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0

    def get_trial_message(self) -> str:
        """Get trial status message."""
        return self.get_text(self.TRIAL_MESSAGE)

    def get_benefit_items(self) -> list:
        """Get list of benefit items."""
        elements = self.find_elements(self.BENEFIT_ITEMS)
        return [element.text for element in elements]

    def fill_registration_form(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company: str = "",
        confirm_password: str = None
    ):
        """Fill out the registration form."""
        self.type_text(self.EMAIL_INPUT, email)
        self.type_text(self.PASSWORD_INPUT, password)

        if confirm_password is None:
            confirm_password = password
        self.type_text(self.CONFIRM_PASSWORD_INPUT, confirm_password)

        self.type_text(self.FIRST_NAME_INPUT, first_name)
        self.type_text(self.LAST_NAME_INPUT, last_name)

        if company:
            self.type_text(self.COMPANY_INPUT, company)

        return self

    def enter_email(self, email: str):
        """Enter email address."""
        self.type_text(self.EMAIL_INPUT, email)
        return self

    def enter_password(self, password: str):
        """Enter password."""
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def enter_confirm_password(self, password: str):
        """Enter password confirmation."""
        self.type_text(self.CONFIRM_PASSWORD_INPUT, password)
        return self

    def enter_first_name(self, first_name: str):
        """Enter first name."""
        self.type_text(self.FIRST_NAME_INPUT, first_name)
        return self

    def enter_last_name(self, last_name: str):
        """Enter last name."""
        self.type_text(self.LAST_NAME_INPUT, last_name)
        return self

    def enter_company(self, company: str):
        """Enter company name."""
        self.type_text(self.COMPANY_INPUT, company)
        return self

    def accept_terms(self):
        """Check the terms acceptance checkbox."""
        if not self.is_element_selected(self.TERMS_CHECKBOX):
            self.click_element(self.TERMS_CHECKBOX)
        return self

    def is_terms_accepted(self) -> bool:
        """Check if terms checkbox is selected."""
        return self.is_element_selected(self.TERMS_CHECKBOX)

    def click_terms_link(self):
        """Click terms of service link."""
        self.click_element(self.TERMS_LINK)
        return self

    def click_privacy_link(self):
        """Click privacy policy link."""
        self.click_element(self.PRIVACY_LINK)
        return self

    def submit_form(self):
        """Submit the registration form."""
        self.click_element(self.SUBMIT_BUTTON)
        return self

    def is_submit_button_enabled(self) -> bool:
        """Check if submit button is enabled."""
        return self.is_element_enabled(self.SUBMIT_BUTTON)

    def wait_for_form_submission(self, timeout: int = 30):
        """Wait for form submission to complete."""
        # Wait for loading to start and finish
        try:
            self.wait_for_element_visible(self.LOADING_SPINNER, timeout=5)
            self.wait_for_element_to_disappear(self.LOADING_SPINNER, timeout=timeout)
        except:
            pass  # Might be very fast
        return self

    def get_submit_status(self) -> str:
        """Get form submission status."""
        if self.is_element_present(self.SUBMIT_STATUS):
            return self.get_text(self.SUBMIT_STATUS)
        return ""

    def is_form_loading(self) -> bool:
        """Check if form is in loading state."""
        return self.is_element_visible(self.LOADING_SPINNER)

    def get_email_error(self) -> str:
        """Get email validation error."""
        if self.is_element_present(self.EMAIL_ERROR):
            return self.get_text(self.EMAIL_ERROR)
        return ""

    def get_password_error(self) -> str:
        """Get password validation error."""
        if self.is_element_present(self.PASSWORD_ERROR):
            return self.get_text(self.PASSWORD_ERROR)
        return ""

    def get_confirm_password_error(self) -> str:
        """Get password confirmation error."""
        if self.is_element_present(self.CONFIRM_PASSWORD_ERROR):
            return self.get_text(self.CONFIRM_PASSWORD_ERROR)
        return ""

    def get_first_name_error(self) -> str:
        """Get first name validation error."""
        if self.is_element_present(self.FIRST_NAME_ERROR):
            return self.get_text(self.FIRST_NAME_ERROR)
        return ""

    def get_last_name_error(self) -> str:
        """Get last name validation error."""
        if self.is_element_present(self.LAST_NAME_ERROR):
            return self.get_text(self.LAST_NAME_ERROR)
        return ""

    def get_all_form_errors(self) -> list:
        """Get all form validation errors."""
        error_elements = self.find_elements(self.FORM_ERRORS)
        return [element.text for element in error_elements if element.text]

    def has_validation_errors(self) -> bool:
        """Check if form has any validation errors."""
        return len(self.find_elements(self.FORM_ERRORS)) > 0

    def get_success_message(self) -> str:
        """Get success message."""
        if self.is_element_present(self.SUCCESS_MESSAGE):
            return self.get_text(self.SUCCESS_MESSAGE)
        return ""

    def get_error_message(self) -> str:
        """Get general error message."""
        if self.is_element_present(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        elif self.is_element_present(self.GENERAL_ERROR):
            return self.get_text(self.GENERAL_ERROR)
        return ""

    def is_success_displayed(self) -> bool:
        """Check if success message is displayed."""
        return self.is_element_visible(self.SUCCESS_MESSAGE)

    def is_error_displayed(self) -> bool:
        """Check if error message is displayed."""
        return (self.is_element_visible(self.ERROR_MESSAGE) or
                self.is_element_visible(self.GENERAL_ERROR))

    def click_login_link(self):
        """Click login link."""
        self.click_element(self.LOGIN_LINK)
        return self

    def click_continue_trial(self):
        """Click continue trial link."""
        self.click_element(self.CONTINUE_TRIAL_LINK)
        return self

    def click_view_pricing(self):
        """Click view pricing link."""
        self.click_element(self.VIEW_PRICING_LINK)
        return self

    def perform_complete_registration(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        company: str = "",
        accept_terms: bool = True
    ):
        """Perform complete registration flow."""
        self.fill_registration_form(email, password, first_name, last_name, company)

        if accept_terms:
            self.accept_terms()

        self.submit_form()
        self.wait_for_form_submission()

        return self

    def clear_form(self):
        """Clear all form fields."""
        self.type_text(self.EMAIL_INPUT, "", clear_first=True)
        self.type_text(self.PASSWORD_INPUT, "", clear_first=True)
        self.type_text(self.CONFIRM_PASSWORD_INPUT, "", clear_first=True)
        self.type_text(self.FIRST_NAME_INPUT, "", clear_first=True)
        self.type_text(self.LAST_NAME_INPUT, "", clear_first=True)
        self.type_text(self.COMPANY_INPUT, "", clear_first=True)
        return self

    def get_form_values(self) -> dict:
        """Get current form field values."""
        return {
            "email": self.get_attribute(self.EMAIL_INPUT, "value"),
            "password": self.get_attribute(self.PASSWORD_INPUT, "value"),
            "confirm_password": self.get_attribute(self.CONFIRM_PASSWORD_INPUT, "value"),
            "first_name": self.get_attribute(self.FIRST_NAME_INPUT, "value"),
            "last_name": self.get_attribute(self.LAST_NAME_INPUT, "value"),
            "company": self.get_attribute(self.COMPANY_INPUT, "value"),
            "terms_accepted": self.is_terms_accepted()
        }

    def get_page_state(self) -> dict:
        """Get current page state for debugging."""
        return {
            "title": self.get_page_title_text(),
            "images_used": self.get_images_used_count(),
            "images_remaining": self.get_images_remaining_count(),
            "trial_message": self.get_trial_message(),
            "form_values": self.get_form_values(),
            "validation_errors": self.get_all_form_errors(),
            "success_message": self.get_success_message(),
            "error_message": self.get_error_message(),
            "submit_button_enabled": self.is_submit_button_enabled(),
            "is_loading": self.is_form_loading()
        }
