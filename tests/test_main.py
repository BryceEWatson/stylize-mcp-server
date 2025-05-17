"""Unit tests for the main application module."""

import io
import os
import json
import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import UploadFile

# Add the project root to the Python path to enable imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app, MAX_UPLOAD_SIZE_MB, MAX_UPLOAD_SIZE_BYTES, stylize_image
from app.styles_service import StyleService

# Sample test styles data
TEST_STYLES = [
    {
        "id": "test_style",
        "name": "Test Style",
        "description": "Description for test style",
        "prompt_fragment": "prompt for test style"
    },
    {
        "id": "another_style",
        "name": "Another Style",
        "description": "Description for another style",
        "prompt_fragment": "prompt for another style"
    }
]

# Initialize test client with mocked dependencies
@pytest.fixture(scope="module")
def test_client():
    # Patch the StyleService to return our test styles
    with patch.object(StyleService, "_load_styles"):
        style_service_mock = StyleService()
        style_service_mock.styles = TEST_STYLES
        style_service_mock.styles_by_id = {style["id"]: style for style in TEST_STYLES}
        
        # Patch the main app's style_service with our mock
        with patch("app.main.style_service", style_service_mock):
            yield TestClient(app)

# Test fixtures
@pytest.fixture
def valid_jpeg_image():
    """Create a small valid JPEG image for testing."""
    # Create a minimal valid JPEG image for testing
    # This is much simpler than a real JPEG but sufficient for testing
    # Create a simple valid JPEG for testing
    quant_table = bytes([0] * 64)  # Simple quantization table
    jpeg_data = (
        b'\xff\xd8' +  # SOI marker
        b'\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00' +  # JFIF APP0 segment
        b'\xff\xdb\x00\x43\x00' + quant_table +  # Define Quantization Table marker
        b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00' +  # SOF marker (baseline DCT)
        b'\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +  # Huffman table
        b'\xff\xda\x00\x08\x01\x01\x00\x00\x3f\x00' +  # SOS marker
        b'\x00' +  # 1 byte of image data
        b'\xff\xd9'  # EOI marker
    )
    return io.BytesIO(jpeg_data)

@pytest.fixture
def valid_png_image():
    """Create a small valid PNG image for testing."""
    # This is a minimal valid PNG file (1x1 pixel)
    png_data = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00'
        b'\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xdc\xcc\x59\xe7\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return io.BytesIO(png_data)

@pytest.fixture
def invalid_gif_image():
    """Create a small GIF image for testing invalid format."""
    # This is a minimal valid GIF file (1x1 pixel)
    gif_data = (
        b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00'
        b'\x01\x00\x00\x02\x02D\x01\x00;'
    )
    return io.BytesIO(gif_data)

@pytest.fixture
def large_image():
    """Create an image that exceeds the size limit for testing."""
    # Create a BytesIO object with size slightly larger than the limit
    size = MAX_UPLOAD_SIZE_BYTES + 1024  # 1KB over the limit
    return io.BytesIO(b'\xff' * size)

@pytest.fixture
def exact_size_limit_image():
    """Create an image that is exactly at the size limit for testing."""
    # Create a BytesIO object with size exactly at the limit
    return io.BytesIO(b'\xff' * MAX_UPLOAD_SIZE_BYTES)

# Tests for the stylize_image endpoint
def test_valid_jpeg_image(valid_jpeg_image, test_client):
    """Test that a valid JPEG image is accepted."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data

def test_valid_png_image(valid_png_image, test_client):
    """Test that a valid PNG image is accepted."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.png", valid_png_image, "image/png")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data

def test_missing_image(test_client):
    """Test that a request with missing image file returns a 400 error."""
    response = test_client.post(
        "/stylize_image",
        files={},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Image file is required."}

def test_missing_style_id(valid_jpeg_image, test_client):
    """Test that a request with missing style_id returns a 400 error."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
        data={}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Style ID is required."}

def test_unsupported_image_format(invalid_gif_image, test_client):
    """Test that an unsupported image format returns a 400 error."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.gif", invalid_gif_image, "image/gif")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid image format. Only JPEG and PNG are supported."}

def test_image_exceeding_size_limit(large_image, test_client):
    """Test that an image exceeding the size limit returns a 400 error."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("large.jpg", large_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": f"Image size exceeds the limit of {MAX_UPLOAD_SIZE_MB} MB."}

def test_image_at_size_limit(exact_size_limit_image, test_client):
    """Test that an image exactly at the size limit is accepted."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("exact_size.jpg", exact_size_limit_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data


# Tests for style validation in stylize_image endpoint
def test_invalid_style_id(valid_jpeg_image, test_client):
    """Test that a request with an invalid style_id returns a 400 error."""
    response = test_client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
        data={"style_id": "nonexistent_style"}
    )
    assert response.status_code == 400
    assert "Invalid style_id" in response.json()["error"]
    assert "test_style" in response.json()["error"]


# Tests for the GET /styles endpoint
def test_get_styles(test_client):
    """Test that the styles endpoint returns a 200 OK status and the styles array."""
    response = test_client.get("/styles")
    assert response.status_code == 200
    styles = response.json()
    assert isinstance(styles, list)
    assert len(styles) == 2  # We have 2 test styles
    assert styles[0]["id"] == "test_style"
    assert styles[1]["id"] == "another_style"
    
    # Check that all required fields are present in each style
    for style in styles:
        assert "id" in style
        assert "name" in style
        assert "description" in style
        assert "prompt_fragment" in style


# Tests for prompt templating logic

@pytest.mark.parametrize("user_prompt,expected_final_prompt", [
    ("A beautiful sunset over the mountains", "A beautiful sunset over the mountains, prompt for test style"),  # With user prompt
    ("   ", "prompt for test style"),  # Empty user prompt (whitespace)
    (None, "prompt for test style"),  # No user prompt
])
def test_prompt_templating(valid_jpeg_image, test_client, user_prompt, expected_final_prompt):
    """Test the prompt templating logic under various conditions."""
    style_id = "test_style"
    
    # Prepare request data
    data = {"style_id": style_id}
    if user_prompt is not None:
        data["user_prompt"] = user_prompt
    
    # Mock the styling process to verify the prompt being used
    with patch("app.main.logger.info") as mock_logger:
        response = test_client.post(
            "/stylize_image",
            files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
            data=data
        )
        
        # Verify response
        assert response.status_code == 200
        assert response.json()["style"] == style_id
        
        # Verify the final prompt was logged correctly
        # We need to check if any of the log calls contain our expected prompt
        prompt_logged = False
        for call in mock_logger.call_args_list:
            log_message = call[0][0]  # First arg of the call
            if expected_final_prompt in log_message:
                prompt_logged = True
                break
                
        assert prompt_logged, f"Expected prompt '{expected_final_prompt}' not found in logs"
