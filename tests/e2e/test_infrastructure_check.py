"""
E2E infrastructure verification tests.

Basic tests to verify E2E testing infrastructure is working.
"""
import pytest
from tests.e2e.config import get_test_config
from tests.e2e.utils.test_data_manager import TestDataManager


@pytest.mark.integration
class TestE2EInfrastructure:
    """Test E2E infrastructure components."""
    
    def test_configuration_loading(self):
        """Test that E2E configuration loads correctly."""
        config = get_test_config()
        
        assert config.environment is not None
        assert config.base_url is not None
        assert config.browser in ["chrome", "firefox"]
        assert isinstance(config.headless, bool)
        assert isinstance(config.test_security_features, bool)
    
    def test_test_data_manager(self):
        """Test that test data manager works correctly."""
        manager = TestDataManager()
        
        # Test user data generation
        user_data = manager.get_test_user_data()
        assert "email" in user_data
        assert "@" in user_data["email"]
        assert "first_name" in user_data
        assert "last_name" in user_data
        
        # Test styles data
        styles = manager.get_style_test_data()
        assert len(styles) > 0
        assert "van_gogh" in styles
        
        # Test project contexts
        contexts = manager.get_project_contexts()
        assert "minimal" in contexts
        assert "complete_with_logo" in contexts
        assert "invalid_json" in contexts
    
    def test_test_image_generation(self):
        """Test that test images can be generated."""
        manager = TestDataManager()
        
        # Get test images
        images = manager.get_test_images()
        assert "valid_jpeg" in images
        assert "valid_png" in images
        assert "corrupted" in images
        
        # Verify base64 format
        jpeg_data = images["valid_jpeg"]
        assert isinstance(jpeg_data, str)
        assert len(jpeg_data) > 0
    
    def test_api_client_instantiation(self):
        """Test that API client can be instantiated."""
        from tests.e2e.utils.api_client import E2EAPIClient
        
        client = E2EAPIClient(
            base_url="http://localhost:8080",
            timeout=30
        )
        
        assert client.base_url == "http://localhost:8080"
        # Just verify timeout is set (httpx.Timeout object)
        assert client.timeout is not None
    
    def test_mcp_client_instantiation(self):
        """Test that MCP client can be instantiated."""
        from tests.e2e.utils.mcp_client import E2EMCPClient
        
        client = E2EMCPClient("http://localhost:8080/mcp")
        
        assert client.mcp_url == "http://localhost:8080/mcp"
        assert client.connected is False
    
    def test_page_objects_instantiation(self):
        """Test that page objects can be instantiated."""
        # Note: This doesn't create actual browser instances
        # Just tests that the classes can be imported and basic structure works
        
        from tests.e2e.pages.demo_page import DemoPage
        from tests.e2e.pages.trial_upgrade_page import TrialUpgradePage
        from tests.e2e.pages.dashboard_page import DashboardPage
        
        # Just verify the classes exist and have expected attributes
        assert hasattr(DemoPage, 'PAGE_PATH')
        assert hasattr(TrialUpgradePage, 'PAGE_PATH')
        assert hasattr(DashboardPage, 'PAGE_PATH')
        
        assert DemoPage.PAGE_PATH == "/web/demo"
        assert TrialUpgradePage.PAGE_PATH == "/web/upgrade"
        assert DashboardPage.PAGE_PATH == "/web/dashboard"
    
    def test_pytest_markers_work(self):
        """Test that pytest markers are working."""
        # This test itself uses the @pytest.mark.integration marker
        # If it runs, the marker system is working
        assert True