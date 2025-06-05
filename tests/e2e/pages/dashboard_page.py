"""
Dashboard page object for E2E testing.
"""

from selenium.webdriver.common.by import By

from tests.e2e.pages.base_page import BasePage


class DashboardPage(BasePage):
    """Page object for the user dashboard page (/web/dashboard)."""

    # Page URL
    PAGE_PATH = "/web/dashboard"

    # Locators
    PAGE_TITLE = (By.TAG_NAME, "h1")
    WELCOME_MESSAGE = (By.CLASS_NAME, "welcome-message")
    USER_NAME = (By.ID, "user-name")

    # Navigation
    NAV_BAR = (By.TAG_NAME, "nav")
    LOGOUT_LINK = (By.CSS_SELECTOR, "a[href*='logout']")
    PROFILE_LINK = (By.CSS_SELECTOR, "a[href*='profile']")

    # Credit information section
    CREDITS_SECTION = (By.ID, "credits-section")
    CURRENT_CREDITS = (By.ID, "current-credits")
    CREDITS_USED_THIS_MONTH = (By.ID, "credits-used-month")
    MONTHLY_ALLOWANCE = (By.ID, "monthly-allowance")
    NEXT_RESET_DATE = (By.ID, "next-reset")
    CREDIT_HISTORY_LINK = (By.CSS_SELECTOR, "a[href*='credit-history']")

    # Usage statistics
    USAGE_SECTION = (By.ID, "usage-section")
    TOTAL_IMAGES_GENERATED = (By.ID, "total-images")
    IMAGES_THIS_MONTH = (By.ID, "images-this-month")
    FAVORITE_STYLE = (By.ID, "favorite-style")
    RECENT_ACTIVITY_LIST = (By.ID, "recent-activity")
    ACTIVITY_ITEMS = (By.CSS_SELECTOR, "#recent-activity .activity-item")

    # Credit purchase section
    PURCHASE_SECTION = (By.ID, "purchase-section")
    PURCHASE_TITLE = (By.CSS_SELECTOR, "#purchase-section h2")
    CREDIT_PACKAGES = (By.CSS_SELECTOR, ".credit-package")
    PACKAGE_NAMES = (By.CSS_SELECTOR, ".package-name")
    PACKAGE_PRICES = (By.CSS_SELECTOR, ".package-price")
    PACKAGE_CREDITS = (By.CSS_SELECTOR, ".package-credits")
    PACKAGE_BONUSES = (By.CSS_SELECTOR, ".package-bonus")
    PURCHASE_BUTTONS = (By.CSS_SELECTOR, ".purchase-btn")

    # Specific packages (based on common package names)
    STARTER_PACKAGE = (By.CSS_SELECTOR, "[data-package='starter']")
    POPULAR_PACKAGE = (By.CSS_SELECTOR, "[data-package='popular']")
    PRO_PACKAGE = (By.CSS_SELECTOR, "[data-package='pro']")
    ENTERPRISE_PACKAGE = (By.CSS_SELECTOR, "[data-package='enterprise']")

    # Purchase modal/form
    PURCHASE_MODAL = (By.ID, "purchase-modal")
    MODAL_PACKAGE_NAME = (By.ID, "modal-package-name")
    MODAL_PACKAGE_PRICE = (By.ID, "modal-package-price")
    MODAL_PACKAGE_CREDITS = (By.ID, "modal-package-credits")
    CONFIRM_PURCHASE_BUTTON = (By.ID, "confirm-purchase")
    CANCEL_PURCHASE_BUTTON = (By.ID, "cancel-purchase")
    PURCHASE_FORM = (By.ID, "purchase-form")

    # Payment information (if implemented)
    PAYMENT_SECTION = (By.ID, "payment-section")
    CARD_NUMBER_INPUT = (By.ID, "card-number")
    EXPIRY_INPUT = (By.ID, "card-expiry")
    CVV_INPUT = (By.ID, "card-cvv")
    BILLING_NAME_INPUT = (By.ID, "billing-name")

    # Purchase status and messages
    PURCHASE_STATUS = (By.ID, "purchase-status")
    SUCCESS_MESSAGE = (By.CLASS_NAME, "success-message")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    PROCESSING_MESSAGE = (By.CLASS_NAME, "processing-message")

    # Account information
    ACCOUNT_SECTION = (By.ID, "account-section")
    ACCOUNT_EMAIL = (By.ID, "account-email")
    ACCOUNT_TYPE = (By.ID, "account-type")
    MEMBER_SINCE = (By.ID, "member-since")
    ACCOUNT_STATUS = (By.ID, "account-status")

    # Quick actions
    QUICK_ACTIONS = (By.ID, "quick-actions")
    GENERATE_IMAGE_LINK = (By.CSS_SELECTOR, "a[href*='demo']")
    API_KEYS_LINK = (By.CSS_SELECTOR, "a[href*='api-keys']")
    SETTINGS_LINK = (By.CSS_SELECTOR, "a[href*='settings']")

    # Loading states
    LOADING_SPINNER = (By.CLASS_NAME, "loading-spinner")
    CREDITS_LOADING = (By.ID, "credits-loading")
    PURCHASE_LOADING = (By.ID, "purchase-loading")

    def navigate_to_dashboard(self):
        """Navigate to dashboard page."""
        return self.navigate_to(self.PAGE_PATH)

    def get_page_title_text(self) -> str:
        """Get page title text."""
        return self.get_text(self.PAGE_TITLE)

    def get_welcome_message(self) -> str:
        """Get welcome message."""
        return self.get_text(self.WELCOME_MESSAGE)

    def get_user_name(self) -> str:
        """Get displayed user name."""
        return self.get_text(self.USER_NAME)

    def click_logout(self):
        """Click logout link."""
        self.click_element(self.LOGOUT_LINK)
        return self

    def click_profile(self):
        """Click profile link."""
        self.click_element(self.PROFILE_LINK)
        return self

    # Credit information methods
    def get_current_credits(self) -> int:
        """Get current credit balance."""
        text = self.get_text(self.CURRENT_CREDITS)
        import re
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else 0

    def get_credits_used_this_month(self) -> int:
        """Get credits used this month."""
        text = self.get_text(self.CREDITS_USED_THIS_MONTH)
        import re
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else 0

    def get_monthly_allowance(self) -> int:
        """Get monthly credit allowance."""
        text = self.get_text(self.MONTHLY_ALLOWANCE)
        import re
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else 0

    def get_next_reset_date(self) -> str:
        """Get next credit reset date."""
        return self.get_text(self.NEXT_RESET_DATE)

    def click_credit_history(self):
        """Click credit history link."""
        self.click_element(self.CREDIT_HISTORY_LINK)
        return self

    # Usage statistics methods
    def get_total_images_generated(self) -> int:
        """Get total images generated."""
        text = self.get_text(self.TOTAL_IMAGES_GENERATED)
        import re
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else 0

    def get_images_this_month(self) -> int:
        """Get images generated this month."""
        text = self.get_text(self.IMAGES_THIS_MONTH)
        import re
        match = re.search(r'(\d+)', text.replace(',', ''))
        return int(match.group(1)) if match else 0

    def get_favorite_style(self) -> str:
        """Get favorite style."""
        return self.get_text(self.FAVORITE_STYLE)

    def get_recent_activities(self) -> list[str]:
        """Get list of recent activities."""
        activity_elements = self.find_elements(self.ACTIVITY_ITEMS)
        return [element.text for element in activity_elements]

    # Credit package methods
    def get_available_packages(self) -> list[dict]:
        """Get list of available credit packages."""
        packages = []
        package_elements = self.find_elements(self.CREDIT_PACKAGES)

        for package in package_elements:
            try:
                name = package.find_element(By.CSS_SELECTOR, ".package-name").text
                price = package.find_element(By.CSS_SELECTOR, ".package-price").text
                credits = package.find_element(By.CSS_SELECTOR, ".package-credits").text

                # Extract bonus if present
                bonus = ""
                try:
                    bonus = package.find_element(By.CSS_SELECTOR, ".package-bonus").text
                except:
                    pass

                packages.append({
                    "name": name,
                    "price": price,
                    "credits": credits,
                    "bonus": bonus
                })
            except:
                continue

        return packages

    def click_purchase_package(self, package_name: str):
        """Click purchase button for specific package."""
        packages = self.find_elements(self.CREDIT_PACKAGES)

        for package in packages:
            try:
                name_element = package.find_element(By.CSS_SELECTOR, ".package-name")
                if package_name.lower() in name_element.text.lower():
                    purchase_btn = package.find_element(By.CSS_SELECTOR, ".purchase-btn")
                    purchase_btn.click()
                    return self
            except:
                continue

        raise ValueError(f"Package '{package_name}' not found")

    def click_starter_package(self):
        """Click purchase button for starter package."""
        return self.click_purchase_package("starter")

    def click_popular_package(self):
        """Click purchase button for popular package."""
        return self.click_purchase_package("popular")

    def click_pro_package(self):
        """Click purchase button for pro package."""
        return self.click_purchase_package("pro")

    def click_enterprise_package(self):
        """Click purchase button for enterprise package."""
        return self.click_purchase_package("enterprise")

    # Purchase modal methods
    def is_purchase_modal_visible(self) -> bool:
        """Check if purchase modal is visible."""
        return self.is_element_visible(self.PURCHASE_MODAL)

    def get_modal_package_details(self) -> dict:
        """Get package details from modal."""
        return {
            "name": self.get_text(self.MODAL_PACKAGE_NAME),
            "price": self.get_text(self.MODAL_PACKAGE_PRICE),
            "credits": self.get_text(self.MODAL_PACKAGE_CREDITS)
        }

    def confirm_purchase(self):
        """Confirm purchase in modal."""
        self.click_element(self.CONFIRM_PURCHASE_BUTTON)
        return self

    def cancel_purchase(self):
        """Cancel purchase in modal."""
        self.click_element(self.CANCEL_PURCHASE_BUTTON)
        return self

    def wait_for_purchase_completion(self, timeout: int = 30):
        """Wait for purchase to complete."""
        try:
            self.wait_for_element_visible(self.PROCESSING_MESSAGE, timeout=5)
            self.wait_for_element_to_disappear(self.PROCESSING_MESSAGE, timeout=timeout)
        except:
            pass  # Might be very fast
        return self

    # Purchase status methods
    def get_purchase_status(self) -> str:
        """Get purchase status message."""
        if self.is_element_present(self.PURCHASE_STATUS):
            return self.get_text(self.PURCHASE_STATUS)
        return ""

    def get_success_message(self) -> str:
        """Get success message."""
        if self.is_element_present(self.SUCCESS_MESSAGE):
            return self.get_text(self.SUCCESS_MESSAGE)
        return ""

    def get_error_message(self) -> str:
        """Get error message."""
        if self.is_element_present(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        return ""

    def is_purchase_successful(self) -> bool:
        """Check if purchase was successful."""
        return self.is_element_visible(self.SUCCESS_MESSAGE)

    def is_purchase_error(self) -> bool:
        """Check if purchase had an error."""
        return self.is_element_visible(self.ERROR_MESSAGE)

    def is_purchase_processing(self) -> bool:
        """Check if purchase is processing."""
        return self.is_element_visible(self.PROCESSING_MESSAGE)

    # Account information methods
    def get_account_email(self) -> str:
        """Get account email."""
        return self.get_text(self.ACCOUNT_EMAIL)

    def get_account_type(self) -> str:
        """Get account type."""
        return self.get_text(self.ACCOUNT_TYPE)

    def get_member_since(self) -> str:
        """Get member since date."""
        return self.get_text(self.MEMBER_SINCE)

    def get_account_status(self) -> str:
        """Get account status."""
        return self.get_text(self.ACCOUNT_STATUS)

    # Quick actions
    def click_generate_image(self):
        """Click generate image link."""
        self.click_element(self.GENERATE_IMAGE_LINK)
        return self

    def click_api_keys(self):
        """Click API keys link."""
        self.click_element(self.API_KEYS_LINK)
        return self

    def click_settings(self):
        """Click settings link."""
        self.click_element(self.SETTINGS_LINK)
        return self

    def perform_complete_purchase_flow(self, package_name: str):
        """Perform complete credit purchase flow."""
        # Click package purchase button
        self.click_purchase_package(package_name)

        # Wait for modal to appear
        self.wait_for_element_visible(self.PURCHASE_MODAL)

        # Confirm purchase
        self.confirm_purchase()

        # Wait for completion
        self.wait_for_purchase_completion()

        return self

    def refresh_dashboard_data(self):
        """Refresh dashboard data."""
        self.refresh_page()
        self.wait_for_page_load()
        return self

    def get_dashboard_summary(self) -> dict:
        """Get complete dashboard summary."""
        return {
            "user_name": self.get_user_name(),
            "current_credits": self.get_current_credits(),
            "credits_used_month": self.get_credits_used_this_month(),
            "monthly_allowance": self.get_monthly_allowance(),
            "total_images": self.get_total_images_generated(),
            "images_this_month": self.get_images_this_month(),
            "favorite_style": self.get_favorite_style(),
            "account_email": self.get_account_email(),
            "account_type": self.get_account_type(),
            "recent_activities": self.get_recent_activities(),
            "available_packages": self.get_available_packages()
        }

    def get_page_state(self) -> dict:
        """Get current page state for debugging."""
        return {
            "title": self.get_page_title_text(),
            "welcome_message": self.get_welcome_message(),
            "dashboard_summary": self.get_dashboard_summary(),
            "purchase_modal_visible": self.is_purchase_modal_visible(),
            "success_message": self.get_success_message(),
            "error_message": self.get_error_message(),
            "purchase_status": self.get_purchase_status()
        }
