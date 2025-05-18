"""Unit tests for the data models."""

import pytest
from app.models import ProjectContext


class TestProjectContext:
    """Tests for the ProjectContext model."""
    
    def test_empty_context(self):
        """Test that an empty context is valid."""
        context = ProjectContext()
        assert context.project_name is None
        assert context.project_description is None
        assert context.target_audience is None
        assert context.keywords is None
        assert context.brand_colors is None
        assert context.desired_elements is None
        assert context.avoid_elements is None
        assert context.artistic_mood is None
        assert context.reference_logo_image_base64 is None
    
    def test_full_context(self):
        """Test that a complete context is properly constructed."""
        context = ProjectContext(
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
        
        assert context.project_name == "Test Project"
        assert context.project_description == "A test project description"
        assert context.target_audience == "Developers"
        assert context.keywords == ["test", "project", "context"]
        assert context.brand_colors == ["#FF0000", "#00FF00", "#0000FF"]
        assert context.desired_elements == ["logo", "text", "background"]
        assert context.avoid_elements == ["crowds", "text-heavy design"]
        assert context.artistic_mood == "professional"
        assert context.reference_logo_image_base64 == "SGVsbG8gV29ybGQ="
    
    def test_partial_context(self):
        """Test that a partial context is properly constructed."""
        context = ProjectContext(
            project_name="Test Project",
            brand_colors=["#FF0000"],
            artistic_mood="professional"
        )
        
        assert context.project_name == "Test Project"
        assert context.project_description is None
        assert context.target_audience is None
        assert context.keywords is None
        assert context.brand_colors == ["#FF0000"]
        assert context.desired_elements is None
        assert context.avoid_elements is None
        assert context.artistic_mood == "professional"
        assert context.reference_logo_image_base64 is None
    
    def test_invalid_base64(self):
        """Test that invalid base64 for reference_logo_image_base64 raises a validation error."""
        with pytest.raises(ValueError) as excinfo:
            ProjectContext(
                project_name="Test Project",
                reference_logo_image_base64="Invalid Base64!"
            )
        
        error_msg = str(excinfo.value)
        assert any(msg in error_msg for msg in [
            "Invalid base64",     # Generic check
            "Invalid characters",  # Character validation
            "Base64 decode failed" # Decode attempt failure
        ]), f"Unexpected error message: {error_msg}"
    
    def test_valid_base64(self):
        """Test that valid base64 for reference_logo_image_base64 is accepted."""
        context = ProjectContext(
            reference_logo_image_base64="SGVsbG8gV29ybGQ="  # "Hello World" in base64
        )
        
        assert context.reference_logo_image_base64 == "SGVsbG8gV29ybGQ="
    
    def test_brand_colors_limit(self):
        """Test that brand_colors is limited to 3 colors."""
        context = ProjectContext(
            brand_colors=["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF"]
        )
        
        assert len(context.brand_colors) == 3
        assert context.brand_colors == ["#FF0000", "#00FF00", "#0000FF"]
    
    def test_invalid_color_format(self):
        """Test that invalid color format raises a validation error."""
        with pytest.raises(ValueError) as excinfo:
            ProjectContext(
                brand_colors=["FF0000", "#00FF00", "#0000FF"]
            )
        
        assert "Invalid color format" in str(excinfo.value)
