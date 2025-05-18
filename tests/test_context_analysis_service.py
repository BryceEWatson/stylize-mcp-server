"""Unit tests for the context analysis service."""

import pytest
import base64
from app.models import ProjectContext
from app.context_analysis_service import ContextAnalysisService


class TestContextAnalysisService:
    """Tests for the ContextAnalysisService class."""
    
    @pytest.fixture
    def service(self):
        """Create a ContextAnalysisService instance for testing."""
        return ContextAnalysisService()
    
    @pytest.fixture
    def full_context(self):
        """Create a fully populated ProjectContext for testing."""
        return ProjectContext(
            project_name="Test Project",
            project_description="A test project description",
            target_audience="Developers",
            keywords=["test", "project", "context"],
            brand_colors=["#FF0000", "#00FF00", "#0000FF"],
            desired_elements=["logo", "text", "background"],
            avoid_elements=["crowds", "text-heavy design"],
            artistic_mood="professional",
            reference_logo_image_base64="SGVsbG8gV29ybGQ="  # "Hello World" in base64
        )
    
    @pytest.fixture
    def partial_context(self):
        """Create a partially populated ProjectContext for testing."""
        return ProjectContext(
            project_name="Test Project",
            brand_colors=["#FF0000"],
            artistic_mood="professional"
        )
    
    @pytest.fixture
    def empty_context(self):
        """Create an empty ProjectContext for testing."""
        return ProjectContext()
    
    def test_analyze_full_context(self, service, full_context):
        """Test analyzing a fully populated context."""
        result = service.analyze(full_context)
        
        # Verify all expected keys are present in the result
        assert "context_summary_string" in result
        assert "brand_colors_list" in result
        assert "decoded_reference_logo_bytes" in result
        assert "avoid_elements_list" in result
        
        # Check content of result
        assert "Test Project" in result["context_summary_string"]
        assert "A test project description" in result["context_summary_string"]
        assert "for Developers" in result["context_summary_string"]
        assert "with elements of test, project, context" in result["context_summary_string"]
        assert "including logo, text, background" in result["context_summary_string"]
        assert "in a professional style" in result["context_summary_string"]
        
        assert result["brand_colors_list"] == ["#FF0000", "#00FF00", "#0000FF"]
        assert result["decoded_reference_logo_bytes"] == b"Hello World"
        assert result["avoid_elements_list"] == ["crowds", "text-heavy design"]
    
    def test_analyze_partial_context(self, service, partial_context):
        """Test analyzing a partially populated context."""
        result = service.analyze(partial_context)
        
        # Check content of result
        assert "Test Project" in result["context_summary_string"]
        assert "in a professional style" in result["context_summary_string"]
        assert "A test project description" not in result["context_summary_string"]
        
        assert result["brand_colors_list"] == ["#FF0000"]
        assert result["decoded_reference_logo_bytes"] is None
        assert result["avoid_elements_list"] == []
    
    def test_analyze_empty_context(self, service, empty_context):
        """Test analyzing an empty context."""
        result = service.analyze(empty_context)
        
        # Check content of result
        assert result["context_summary_string"] == ""
        assert result["brand_colors_list"] == []
        assert result["decoded_reference_logo_bytes"] is None
        assert result["avoid_elements_list"] == []
    
    def test_generate_context_summary(self, service, full_context):
        """Test the _generate_context_summary method."""
        summary = service._generate_context_summary(full_context)
        
        # Check that all relevant context parts are included in the summary
        assert "Test Project" in summary
        assert "A test project description" in summary
        assert "for Developers" in summary
        assert "with elements of test, project, context" in summary
        assert "including logo, text, background" in summary
        assert "in a professional style" in summary
        
        # Check that parts are separated by commas
        assert ", " in summary
