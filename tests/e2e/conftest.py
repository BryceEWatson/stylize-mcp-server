"""
Pytest configuration and fixtures for E2E tests.
"""
import asyncio
import shutil
import tempfile

import httpx
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from tests.e2e.config import (
    get_api_base_url,
    get_base_url,
    get_browser_options,
    get_test_config,
)
from tests.e2e.utils.api_client import E2EAPIClient
from tests.e2e.utils.mcp_client import E2EMCPClient
from tests.e2e.utils.test_data_manager import TestDataManager


@pytest.fixture(scope="session")
def test_config():
    """Provide test configuration."""
    return get_test_config()


@pytest.fixture(scope="session")
def test_data_manager():
    """Provide test data manager."""
    return TestDataManager()


@pytest.fixture(scope="session")
def temp_test_dir():
    """Create temporary directory for test files."""
    temp_dir = tempfile.mkdtemp(prefix="e2e_test_")
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


# Browser fixtures
@pytest.fixture(scope="session")
def browser_options(test_config):
    """Get browser options based on configuration."""
    return get_browser_options(test_config.browser)


@pytest.fixture(scope="function")
def webdriver_instance(test_config, browser_options):
    """Create WebDriver instance for browser testing."""
    browser_name = test_config.browser.lower()

    if browser_name == "chrome":
        options = webdriver.ChromeOptions()
        if browser_options["headless"]:
            options.add_argument("--headless")
        for option in browser_options.get("chrome_options", []):
            options.add_argument(option)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

    elif browser_name == "firefox":
        options = webdriver.FirefoxOptions()
        if browser_options["headless"]:
            options.add_argument("--headless")
        for option in browser_options.get("firefox_options", []):
            options.add_argument(option)

        service = FirefoxService(GeckoDriverManager().install())
        driver = webdriver.Firefox(service=service, options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    # Configure timeouts
    driver.implicitly_wait(browser_options["implicit_wait"])
    driver.set_page_load_timeout(browser_options["page_load_timeout"])

    yield driver

    # Cleanup
    driver.quit()


# API client fixtures
@pytest.fixture(scope="session")
async def http_client():
    """Provide async HTTP client for API testing."""
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        yield client


@pytest.fixture(scope="session")
async def api_client(test_config):
    """Provide E2E API client."""
    client = E2EAPIClient(
        base_url=get_api_base_url(),
        timeout=test_config.api_timeout,
        api_key=test_config.test_api_key
    )
    yield client
    await client.close()


# MCP client fixtures
@pytest.fixture(scope="session")
async def mcp_client(test_config):
    """Provide MCP client for testing MCP tools."""
    mcp_url = f"{get_base_url()}/mcp"
    client = E2EMCPClient(mcp_url)
    await client.connect()
    yield client
    await client.disconnect()


# Authentication fixtures
@pytest.fixture(scope="function")
async def trial_session(api_client):
    """Create a trial session for testing."""
    response = await api_client.start_trial_session()
    session_data = response.json()
    yield session_data
    # Cleanup if needed


@pytest.fixture(scope="function")
async def test_user(api_client, test_data_manager):
    """Create a test user account."""
    user_data = test_data_manager.get_test_user_data()

    # Create trial session first
    trial_response = await api_client.start_trial_session()
    trial_data = trial_response.json()

    # Convert trial to user account
    conversion_data = {
        "session_id": trial_data["session_id"],
        **user_data
    }

    response = await api_client.convert_trial_to_user(conversion_data)
    user_account = response.json()

    yield {
        "user_data": user_data,
        "account_data": user_account,
        "trial_data": trial_data
    }

    # Cleanup user account if needed


@pytest.fixture(scope="function")
async def authenticated_api_client(test_user, test_config):
    """Provide API client authenticated with test user."""
    user_account = test_user["account_data"]

    client = E2EAPIClient(
        base_url=get_api_base_url(),
        timeout=test_config.api_timeout,
        jwt_token=user_account.get("access_token")
    )

    yield client
    await client.close()


# Test data fixtures
@pytest.fixture(scope="session")
def test_images(test_data_manager):
    """Provide test images for image processing tests."""
    return test_data_manager.get_test_images()


@pytest.fixture(scope="session")
def project_contexts(test_data_manager):
    """Provide test project contexts."""
    return test_data_manager.get_project_contexts()


@pytest.fixture(scope="function")
def valid_test_image(test_images):
    """Provide a single valid test image."""
    return test_images["valid_jpeg"]


@pytest.fixture(scope="function")
def invalid_test_image(test_images):
    """Provide an invalid test image."""
    return test_images["corrupted"]


# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_metrics():
    """Collect performance metrics during test execution."""
    metrics = {
        "start_time": None,
        "end_time": None,
        "response_times": [],
        "memory_usage": [],
        "api_calls": []
    }

    import time
    metrics["start_time"] = time.time()

    yield metrics

    metrics["end_time"] = time.time()
    metrics["total_duration"] = metrics["end_time"] - metrics["start_time"]


# Error injection fixtures for testing error scenarios
@pytest.fixture(scope="function")
def mock_openai_failure(monkeypatch):
    """Mock OpenAI API failure for error testing."""
    def mock_openai_error(*args, **kwargs):
        raise Exception("Simulated OpenAI API failure")

    monkeypatch.setattr("app.openai_service.generate_image", mock_openai_error)
    yield


@pytest.fixture(scope="function")
def mock_gcs_failure(monkeypatch):
    """Mock GCS failure for error testing."""
    def mock_gcs_error(*args, **kwargs):
        raise Exception("Simulated GCS failure")

    monkeypatch.setattr("app.gcs_service.upload_image", mock_gcs_error)
    yield


# Cleanup fixtures
@pytest.fixture(scope="session", autouse=True)
def cleanup_test_data():
    """Cleanup test data after test session."""
    yield
    # Perform any necessary cleanup of test data


# Pytest configuration
def pytest_configure(config):
    """Configure pytest for E2E tests."""
    # Add custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "security: marks tests as security tests")
    config.addinivalue_line("markers", "performance: marks tests as performance tests")
    config.addinivalue_line("markers", "web_ui: marks tests that require browser")
    config.addinivalue_line("markers", "api_only: marks tests that only test API")
    config.addinivalue_line("markers", "mcp_only: marks tests that only test MCP")
    config.addinivalue_line("markers", "requires_openai: marks tests that require real OpenAI API")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
            item.add_marker(pytest.mark.slow)

        if "test_security" in str(item.fspath):
            item.add_marker(pytest.mark.security)

        if "web_ui" in str(item.fspath) or "pages" in str(item.fspath):
            item.add_marker(pytest.mark.web_ui)

        if "mcp" in str(item.fspath):
            item.add_marker(pytest.mark.mcp_only)


# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Skip conditions for different environments
def pytest_runtest_setup(item):
    """Setup function to skip tests based on environment."""
    test_config = get_test_config()

    # Skip OpenAI tests if no API key provided
    if item.get_closest_marker("requires_openai"):
        if not test_config.openai_api_key:
            pytest.skip("OpenAI API key not provided")

    # Skip security tests if security testing disabled
    if item.get_closest_marker("security"):
        if not test_config.test_security_features:
            pytest.skip("Security testing disabled")

    # Skip performance tests in some environments
    if item.get_closest_marker("performance"):
        if test_config.environment == "e2e_local":
            pytest.skip("Performance tests skipped in local environment")
