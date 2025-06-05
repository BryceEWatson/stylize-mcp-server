"""
Demo page object for E2E testing.
"""
from selenium.webdriver.common.by import By
from typing import List, Optional
from tests.e2e.pages.base_page import BasePage


class DemoPage(BasePage):
    """Page object for the demo page (/web/demo)."""
    
    # Page URL
    PAGE_PATH = "/web/demo"
    
    # Locators
    PAGE_TITLE = (By.TAG_NAME, "h1")
    SUBTITLE = (By.CLASS_NAME, "subtitle")
    
    # Image upload section
    UPLOAD_SECTION = (By.ID, "upload-section")
    FILE_INPUT = (By.ID, "image-upload")
    UPLOAD_BUTTON = (By.ID, "upload-btn")
    UPLOAD_PREVIEW = (By.ID, "upload-preview")
    UPLOAD_STATUS = (By.ID, "upload-status")
    
    # Style selection section
    STYLE_SECTION = (By.ID, "style-section")
    STYLE_SELECTOR = (By.ID, "style-selector")
    STYLE_OPTIONS = (By.CSS_SELECTOR, "#style-selector option")
    RANDOM_STYLES_CHECKBOX = (By.ID, "random-styles")
    RANDOM_STYLES_LABEL = (By.CSS_SELECTOR, "label[for='random-styles']")
    
    # Prompt section
    PROMPT_SECTION = (By.ID, "prompt-section")
    PROMPT_INPUT = (By.ID, "user-prompt")
    PROMPT_PLACEHOLDER = (By.CSS_SELECTOR, "#user-prompt::placeholder")
    
    # Generate button and status
    GENERATE_BUTTON = (By.ID, "generate-btn")
    GENERATION_STATUS = (By.ID, "generation-status")
    LOADING_SPINNER = (By.CLASS_NAME, "loading-spinner")
    
    # Results section
    RESULTS_SECTION = (By.ID, "results-section")
    RESULT_IMAGES = (By.CSS_SELECTOR, ".result-image")
    SINGLE_RESULT = (By.ID, "single-result")
    MULTIPLE_RESULTS = (By.ID, "multiple-results")
    RESULT_STYLE_NAME = (By.CLASS_NAME, "style-name")
    RESULT_IMAGE_URL = (By.CSS_SELECTOR, ".result-image img")
    DOWNLOAD_LINKS = (By.CSS_SELECTOR, ".download-link")
    
    # Trial information section
    TRIAL_INFO_SECTION = (By.ID, "trial-info")
    TRIAL_REMAINING = (By.ID, "trial-remaining")
    TRIAL_MESSAGE = (By.CLASS_NAME, "trial-message")
    SIGNUP_PROMPT = (By.CLASS_NAME, "signup-prompt")
    SIGNUP_LINK = (By.CSS_SELECTOR, ".signup-prompt a")
    
    # Error messages
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    ERROR_ALERT = (By.CSS_SELECTOR, ".alert-error")
    WARNING_MESSAGE = (By.CLASS_NAME, "warning-message")
    
    # Navigation elements
    NAV_BAR = (By.TAG_NAME, "nav")
    LOGO = (By.CLASS_NAME, "logo")
    NAV_LINKS = (By.CSS_SELECTOR, "nav a")
    UPGRADE_LINK = (By.CSS_SELECTOR, "a[href*='upgrade']")
    
    def navigate_to_demo(self):
        """Navigate to demo page."""
        return self.navigate_to(self.PAGE_PATH)
    
    def get_page_title_text(self) -> str:
        """Get page title text."""
        return self.get_text(self.PAGE_TITLE)
    
    def upload_image(self, image_path: str):
        """Upload an image file."""
        self.upload_file(self.FILE_INPUT, image_path)
        return self
    
    def click_upload_button(self):
        """Click upload button."""
        self.click_element(self.UPLOAD_BUTTON)
        return self
    
    def get_upload_status(self) -> str:
        """Get upload status message."""
        return self.get_text(self.UPLOAD_STATUS)
    
    def is_upload_preview_visible(self) -> bool:
        """Check if upload preview is visible."""
        return self.is_element_visible(self.UPLOAD_PREVIEW)
    
    def select_style(self, style_name: str):
        """Select a specific style from dropdown."""
        self.select_dropdown_option(self.STYLE_SELECTOR, style_name)
        return self
    
    def get_available_styles(self) -> List[str]:
        """Get list of available style options."""
        style_elements = self.find_elements(self.STYLE_OPTIONS)
        return [element.text for element in style_elements if element.text]
    
    def enable_random_styles(self):
        """Enable random styles checkbox."""
        checkbox = self.find_element(self.RANDOM_STYLES_CHECKBOX)
        if not checkbox.is_selected():
            self.click_element(self.RANDOM_STYLES_CHECKBOX)
        return self
    
    def disable_random_styles(self):
        """Disable random styles checkbox."""
        checkbox = self.find_element(self.RANDOM_STYLES_CHECKBOX)
        if checkbox.is_selected():
            self.click_element(self.RANDOM_STYLES_CHECKBOX)
        return self
    
    def is_random_styles_enabled(self) -> bool:
        """Check if random styles is enabled."""
        return self.is_element_selected(self.RANDOM_STYLES_CHECKBOX)
    
    def enter_prompt(self, prompt: str):
        """Enter user prompt."""
        self.type_text(self.PROMPT_INPUT, prompt)
        return self
    
    def get_prompt_value(self) -> str:
        """Get current prompt value."""
        return self.get_attribute(self.PROMPT_INPUT, "value")
    
    def click_generate_button(self):
        """Click generate button."""
        self.click_element(self.GENERATE_BUTTON)
        return self
    
    def is_generate_button_enabled(self) -> bool:
        """Check if generate button is enabled."""
        return self.is_element_enabled(self.GENERATE_BUTTON)
    
    def wait_for_generation_complete(self, timeout: int = 60):
        """Wait for image generation to complete."""
        # Wait for loading spinner to appear and then disappear
        try:
            self.wait_for_element_visible(self.LOADING_SPINNER, timeout=5)
            self.wait_for_element_to_disappear(self.LOADING_SPINNER, timeout=timeout)
        except:
            pass  # Spinner might not appear for fast responses
        
        # Wait for results section to be visible
        self.wait_for_element_visible(self.RESULTS_SECTION, timeout=timeout)
        return self
    
    def get_generation_status(self) -> str:
        """Get generation status message."""
        if self.is_element_present(self.GENERATION_STATUS):
            return self.get_text(self.GENERATION_STATUS)
        return ""
    
    def is_loading(self) -> bool:
        """Check if generation is in progress."""
        return self.is_element_visible(self.LOADING_SPINNER)
    
    def get_result_images_count(self) -> int:
        """Get number of result images."""
        return len(self.find_elements(self.RESULT_IMAGES))
    
    def get_result_image_urls(self) -> List[str]:
        """Get URLs of result images."""
        img_elements = self.find_elements(self.RESULT_IMAGE_URL)
        return [img.get_attribute("src") for img in img_elements]
    
    def get_result_style_names(self) -> List[str]:
        """Get style names from results."""
        style_elements = self.find_elements(self.RESULT_STYLE_NAME)
        return [element.text for element in style_elements]
    
    def is_single_result_displayed(self) -> bool:
        """Check if single result is displayed."""
        return self.is_element_visible(self.SINGLE_RESULT)
    
    def is_multiple_results_displayed(self) -> bool:
        """Check if multiple results are displayed."""
        return self.is_element_visible(self.MULTIPLE_RESULTS)
    
    def click_download_link(self, index: int = 0):
        """Click download link for result image."""
        download_links = self.find_elements(self.DOWNLOAD_LINKS)
        if index < len(download_links):
            download_links[index].click()
        return self
    
    def get_trial_remaining_count(self) -> Optional[int]:
        """Get remaining trial image count."""
        if self.is_element_present(self.TRIAL_REMAINING):
            text = self.get_text(self.TRIAL_REMAINING)
            # Extract number from text like "3 images remaining"
            import re
            match = re.search(r'(\d+)', text)
            return int(match.group(1)) if match else None
        return None
    
    def get_trial_message(self) -> str:
        """Get trial status message."""
        if self.is_element_present(self.TRIAL_MESSAGE):
            return self.get_text(self.TRIAL_MESSAGE)
        return ""
    
    def is_signup_prompt_visible(self) -> bool:
        """Check if signup prompt is visible."""
        return self.is_element_visible(self.SIGNUP_PROMPT)
    
    def click_signup_link(self):
        """Click signup link."""
        self.click_element(self.SIGNUP_LINK)
        return self
    
    def get_signup_link_url(self) -> str:
        """Get signup link URL."""
        return self.get_attribute(self.SIGNUP_LINK, "href")
    
    def get_error_message(self) -> str:
        """Get error message if present."""
        if self.is_element_present(self.ERROR_MESSAGE):
            return self.get_text(self.ERROR_MESSAGE)
        elif self.is_element_present(self.ERROR_ALERT):
            return self.get_text(self.ERROR_ALERT)
        return ""
    
    def is_error_displayed(self) -> bool:
        """Check if error message is displayed."""
        return (self.is_element_visible(self.ERROR_MESSAGE) or 
                self.is_element_visible(self.ERROR_ALERT))
    
    def get_warning_message(self) -> str:
        """Get warning message if present."""
        if self.is_element_present(self.WARNING_MESSAGE):
            return self.get_text(self.WARNING_MESSAGE)
        return ""
    
    def click_upgrade_link(self):
        """Click upgrade link in navigation."""
        self.click_element(self.UPGRADE_LINK)
        return self
    
    def perform_complete_generation_flow(
        self,
        image_path: str,
        style: Optional[str] = None,
        prompt: str = "",
        use_random_styles: bool = False
    ):
        """Perform complete image generation flow."""
        # Upload image
        self.upload_image(image_path)
        
        # Select style or enable random styles
        if use_random_styles:
            self.enable_random_styles()
        elif style:
            self.disable_random_styles()
            self.select_style(style)
        
        # Enter prompt if provided
        if prompt:
            self.enter_prompt(prompt)
        
        # Generate image
        self.click_generate_button()
        self.wait_for_generation_complete()
        
        return self
    
    def get_page_state(self) -> dict:
        """Get current page state for debugging."""
        return {
            "title": self.get_page_title_text(),
            "upload_status": self.get_upload_status(),
            "generation_status": self.get_generation_status(),
            "is_loading": self.is_loading(),
            "error_message": self.get_error_message(),
            "trial_remaining": self.get_trial_remaining_count(),
            "trial_message": self.get_trial_message(),
            "result_count": self.get_result_images_count(),
            "available_styles": self.get_available_styles(),
            "random_styles_enabled": self.is_random_styles_enabled(),
            "generate_button_enabled": self.is_generate_button_enabled()
        }