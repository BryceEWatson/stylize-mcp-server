"""
Base page class for Page Object Model.
"""
import time

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    """Base page class with common functionality."""

    def __init__(self, driver: WebDriver, base_url: str):
        self.driver = driver
        self.base_url = base_url.rstrip("/")
        self.wait = WebDriverWait(driver, 10)
        self.long_wait = WebDriverWait(driver, 30)

    def navigate_to(self, path: str = ""):
        """Navigate to a specific path."""
        url = f"{self.base_url}{path}"
        self.driver.get(url)
        return self

    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.driver.current_url

    def get_page_title(self) -> str:
        """Get page title."""
        return self.driver.title

    def wait_for_element(self, locator: tuple[str, str], timeout: int = 10):
        """Wait for element to be present."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located(locator))

    def wait_for_element_clickable(self, locator: tuple[str, str], timeout: int = 10):
        """Wait for element to be clickable."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.element_to_be_clickable(locator))

    def wait_for_element_visible(self, locator: tuple[str, str], timeout: int = 10):
        """Wait for element to be visible."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_for_text_in_element(self, locator: tuple[str, str], text: str, timeout: int = 10):
        """Wait for specific text to appear in element."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.text_to_be_present_in_element(locator, text))

    def wait_for_url_contains(self, text: str, timeout: int = 10):
        """Wait for URL to contain specific text."""
        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.url_contains(text))

    def find_element(self, locator: tuple[str, str]):
        """Find single element."""
        return self.driver.find_element(*locator)

    def find_elements(self, locator: tuple[str, str]):
        """Find multiple elements."""
        return self.driver.find_elements(*locator)

    def is_element_present(self, locator: tuple[str, str]) -> bool:
        """Check if element is present."""
        try:
            self.driver.find_element(*locator)
            return True
        except NoSuchElementException:
            return False

    def is_element_visible(self, locator: tuple[str, str]) -> bool:
        """Check if element is visible."""
        try:
            element = self.driver.find_element(*locator)
            return element.is_displayed()
        except NoSuchElementException:
            return False

    def click_element(self, locator: tuple[str, str]):
        """Click element after waiting for it to be clickable."""
        element = self.wait_for_element_clickable(locator)
        element.click()
        return self

    def type_text(self, locator: tuple[str, str], text: str, clear_first: bool = True):
        """Type text into element."""
        element = self.wait_for_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        return self

    def get_text(self, locator: tuple[str, str]) -> str:
        """Get text from element."""
        element = self.wait_for_element(locator)
        return element.text

    def get_attribute(self, locator: tuple[str, str], attribute: str) -> str:
        """Get attribute value from element."""
        element = self.wait_for_element(locator)
        return element.get_attribute(attribute)

    def scroll_to_element(self, locator: tuple[str, str]):
        """Scroll to element."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)  # Allow scroll to complete
        return self

    def hover_over_element(self, locator: tuple[str, str]):
        """Hover over element."""
        element = self.wait_for_element(locator)
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()
        return self

    def upload_file(self, file_input_locator: tuple[str, str], file_path: str):
        """Upload file to file input element."""
        file_input = self.wait_for_element(file_input_locator)
        file_input.send_keys(file_path)
        return self

    def select_dropdown_option(self, dropdown_locator: tuple[str, str], option_text: str):
        """Select option from dropdown by text."""
        from selenium.webdriver.support.ui import Select
        dropdown = self.wait_for_element(dropdown_locator)
        select = Select(dropdown)
        select.select_by_visible_text(option_text)
        return self

    def wait_for_page_load(self, timeout: int = 30):
        """Wait for page to fully load."""
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        return self

    def wait_for_ajax_complete(self, timeout: int = 30):
        """Wait for AJAX requests to complete (if jQuery is present)."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(lambda driver: driver.execute_script("return jQuery.active == 0"))
        except:
            pass  # jQuery might not be present
        return self

    def take_screenshot(self, filename: str = None) -> str:
        """Take screenshot and return filename."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"screenshot_{timestamp}.png"

        self.driver.save_screenshot(filename)
        return filename

    def execute_javascript(self, script: str, *args):
        """Execute JavaScript code."""
        return self.driver.execute_script(script, *args)

    def refresh_page(self):
        """Refresh current page."""
        self.driver.refresh()
        return self

    def go_back(self):
        """Go back to previous page."""
        self.driver.back()
        return self

    def switch_to_window(self, window_handle: str):
        """Switch to specific window."""
        self.driver.switch_to.window(window_handle)
        return self

    def get_window_handles(self) -> list[str]:
        """Get all window handles."""
        return self.driver.window_handles

    def close_current_window(self):
        """Close current window."""
        self.driver.close()
        return self

    def switch_to_frame(self, frame_locator: tuple[str, str]):
        """Switch to frame."""
        frame = self.wait_for_element(frame_locator)
        self.driver.switch_to.frame(frame)
        return self

    def switch_to_default_content(self):
        """Switch back to main content."""
        self.driver.switch_to.default_content()
        return self

    def get_cookies(self):
        """Get all cookies."""
        return self.driver.get_cookies()

    def add_cookie(self, cookie_dict: dict):
        """Add cookie."""
        self.driver.add_cookie(cookie_dict)
        return self

    def delete_cookie(self, cookie_name: str):
        """Delete specific cookie."""
        self.driver.delete_cookie(cookie_name)
        return self

    def delete_all_cookies(self):
        """Delete all cookies."""
        self.driver.delete_all_cookies()
        return self

    def get_local_storage_item(self, key: str):
        """Get item from local storage."""
        return self.driver.execute_script(f"return localStorage.getItem('{key}');")

    def set_local_storage_item(self, key: str, value: str):
        """Set item in local storage."""
        self.driver.execute_script(f"localStorage.setItem('{key}', '{value}');")
        return self

    def clear_local_storage(self):
        """Clear local storage."""
        self.driver.execute_script("localStorage.clear();")
        return self

    def wait_for_element_count(self, locator: tuple[str, str], count: int, timeout: int = 10):
        """Wait for specific number of elements to be present."""
        wait = WebDriverWait(self.driver, timeout)
        wait.until(lambda driver: len(driver.find_elements(*locator)) == count)
        return self

    def wait_for_element_to_disappear(self, locator: tuple[str, str], timeout: int = 10):
        """Wait for element to disappear."""
        wait = WebDriverWait(self.driver, timeout)
        wait.until(EC.invisibility_of_element_located(locator))
        return self

    def get_element_css_property(self, locator: tuple[str, str], property_name: str) -> str:
        """Get CSS property value from element."""
        element = self.wait_for_element(locator)
        return element.value_of_css_property(property_name)

    def is_element_enabled(self, locator: tuple[str, str]) -> bool:
        """Check if element is enabled."""
        try:
            element = self.find_element(locator)
            return element.is_enabled()
        except NoSuchElementException:
            return False

    def is_element_selected(self, locator: tuple[str, str]) -> bool:
        """Check if element is selected (for checkboxes, radio buttons)."""
        try:
            element = self.find_element(locator)
            return element.is_selected()
        except NoSuchElementException:
            return False
