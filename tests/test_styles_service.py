"""Tests for the styles_service module."""

import json
from unittest.mock import mock_open, patch

import pytest

from app.styles_service import StyleService

# Sample test styles data
TEST_STYLES = [
    {
        "id": "test_style_1",
        "name": "Test Style 1",
        "description": "Description for test style 1",
        "prompt_fragment": "prompt for test style 1"
    },
    {
        "id": "test_style_2",
        "name": "Test Style 2",
        "description": "Description for test style 2",
        "prompt_fragment": "prompt for test style 2"
    }
]


def test_load_styles_success():
    """Test successful loading of styles.json."""
    # Mock the open function
    mock_data = json.dumps(TEST_STYLES)
    with patch("builtins.open", mock_open(read_data=mock_data)):
        service = StyleService("mock_path")

        assert len(service.styles) == 2
        assert service.styles[0]["id"] == "test_style_1"
        assert service.styles[1]["id"] == "test_style_2"
        assert "test_style_1" in service.styles_by_id
        assert "test_style_2" in service.styles_by_id


def test_load_styles_file_not_found():
    """Test handling of a missing styles.json file."""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        with pytest.raises(FileNotFoundError):
            StyleService("nonexistent_path")


def test_load_styles_invalid_json():
    """Test handling of an invalid/corrupt styles.json file."""
    with patch("builtins.open", mock_open(read_data="{invalid json}")):
        with pytest.raises(json.JSONDecodeError):
            StyleService("invalid_json_path")


def test_get_all_styles():
    """Test get_all_styles method."""
    with patch.object(StyleService, "_load_styles"):
        service = StyleService()
        service.styles = TEST_STYLES

        styles = service.get_all_styles()
        assert styles == TEST_STYLES


def test_is_valid_style_id():
    """Test is_valid_style_id method."""
    with patch.object(StyleService, "_load_styles"):
        service = StyleService()
        service.styles_by_id = {"valid_id": {}, "another_valid_id": {}}

        assert service.is_valid_style_id("valid_id") is True
        assert service.is_valid_style_id("another_valid_id") is True
        assert service.is_valid_style_id("invalid_id") is False
        assert service.is_valid_style_id("") is False
        assert service.is_valid_style_id(None) is False


def test_get_available_style_ids():
    """Test get_available_style_ids method."""
    with patch.object(StyleService, "_load_styles"):
        service = StyleService()
        service.styles_by_id = {"style1": {}, "style2": {}, "style3": {}}

        style_ids = service.get_available_style_ids()
        assert set(style_ids) == {"style1", "style2", "style3"}
        assert len(style_ids) == 3
