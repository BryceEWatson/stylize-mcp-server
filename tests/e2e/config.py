"""
E2E test configuration management.
"""
import os
from enum import Enum
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional


class TestEnvironment(str, Enum):
    LOCAL = "local"
    STAGING = "staging"
    PRODUCTION = "production"
    E2E_LOCAL = "e2e_local"


class E2ETestConfig(BaseSettings):
    """Configuration for E2E tests."""
    
    # Environment settings
    environment: TestEnvironment = Field(default=TestEnvironment.LOCAL, env="E2E_ENVIRONMENT")
    
    # Application URLs
    base_url: str = Field(default="http://localhost:8080", env="E2E_BASE_URL")
    
    # Browser settings
    browser: str = Field(default="chrome", env="E2E_BROWSER")
    headless: bool = Field(default=True, env="E2E_HEADLESS")
    implicit_wait: int = Field(default=10, env="E2E_IMPLICIT_WAIT")
    page_load_timeout: int = Field(default=30, env="E2E_PAGE_LOAD_TIMEOUT")
    
    # Selenium settings
    selenium_hub_url: Optional[str] = Field(default=None, env="E2E_SELENIUM_HUB_URL")
    selenium_grid: bool = Field(default=False, env="E2E_SELENIUM_GRID")
    
    # Test data settings
    test_images_dir: str = Field(default="tests/e2e/data/images", env="E2E_TEST_IMAGES_DIR")
    generate_test_data: bool = Field(default=True, env="E2E_GENERATE_TEST_DATA")
    
    # API testing settings
    api_timeout: int = Field(default=60, env="E2E_API_TIMEOUT")
    test_api_key: Optional[str] = Field(default=None, env="E2E_TEST_API_KEY")
    
    # OpenAI testing settings (for actual API calls in E2E tests)
    openai_api_key: Optional[str] = Field(default=None, env="E2E_OPENAI_API_KEY")
    openai_test_quota_limit: int = Field(default=50, env="E2E_OPENAI_QUOTA_LIMIT")  # Daily limit for E2E tests
    
    # Performance testing settings
    max_response_time_seconds: int = Field(default=30, env="E2E_MAX_RESPONSE_TIME")
    concurrent_users: int = Field(default=5, env="E2E_CONCURRENT_USERS")
    
    # Security testing settings
    test_security_features: bool = Field(default=True, env="E2E_TEST_SECURITY")
    rate_limit_test_enabled: bool = Field(default=True, env="E2E_RATE_LIMIT_TEST")
    
    # Firestore emulator settings (for local testing)
    firestore_emulator_host: str = Field(default="localhost:8081", env="FIRESTORE_EMULATOR_HOST")
    use_firestore_emulator: bool = Field(default=False, env="E2E_USE_FIRESTORE_EMULATOR")
    
    # Test reporting
    html_report_path: str = Field(default="tests/e2e/reports/report.html", env="E2E_HTML_REPORT_PATH")
    json_report_path: str = Field(default="tests/e2e/reports/report.json", env="E2E_JSON_REPORT_PATH")
    
    # Test execution settings
    parallel_tests: bool = Field(default=True, env="E2E_PARALLEL_TESTS")
    test_timeout: int = Field(default=300, env="E2E_TEST_TIMEOUT")  # 5 minutes per test
    retry_failed_tests: bool = Field(default=True, env="E2E_RETRY_FAILED_TESTS")
    max_retries: int = Field(default=2, env="E2E_MAX_RETRIES")
    
    class Config:
        env_prefix = "E2E_"
        case_sensitive = False


# Global config instance
config = E2ETestConfig()


def get_test_config() -> E2ETestConfig:
    """Get the global test configuration."""
    return config


def get_base_url() -> str:
    """Get the base URL for the application under test."""
    return config.base_url


def get_api_base_url() -> str:
    """Get the API base URL."""
    return f"{config.base_url}"


def get_web_base_url() -> str:
    """Get the web interface base URL."""
    return f"{config.base_url}/web"


def is_local_testing() -> bool:
    """Check if running tests locally."""
    return config.environment in [TestEnvironment.LOCAL, TestEnvironment.E2E_LOCAL]


def is_production_testing() -> bool:
    """Check if running tests against production."""
    return config.environment == TestEnvironment.PRODUCTION


def should_use_real_openai() -> bool:
    """Check if tests should use real OpenAI API."""
    return config.openai_api_key is not None and config.environment != TestEnvironment.E2E_LOCAL


def get_browser_options(browser_name: str) -> dict:
    """Get browser-specific options."""
    options = {
        "headless": config.headless,
        "implicit_wait": config.implicit_wait,
        "page_load_timeout": config.page_load_timeout
    }
    
    if browser_name.lower() == "chrome":
        options.update({
            "chrome_options": [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080"
            ]
        })
    elif browser_name.lower() == "firefox":
        options.update({
            "firefox_options": [
                "--width=1920",
                "--height=1080"
            ]
        })
    
    return options