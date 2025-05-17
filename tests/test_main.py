"""Unit tests for the main application module, focusing on stylize_image endpoint."""

import io
import os
import pytest
from fastapi.testclient import TestClient
from app.main import app, MAX_UPLOAD_SIZE_MB, MAX_UPLOAD_SIZE_BYTES

# Initialize test client
client = TestClient(app)

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
def test_valid_jpeg_image(valid_jpeg_image):
    """Test that a valid JPEG image is accepted."""
    response = client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data

def test_valid_png_image(valid_png_image):
    """Test that a valid PNG image is accepted."""
    response = client.post(
        "/stylize_image",
        files={"image": ("test.png", valid_png_image, "image/png")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data

def test_missing_image():
    """Test that a request with missing image file returns a 400 error."""
    response = client.post(
        "/stylize_image",
        files={},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Image file is required."}

def test_missing_style_id(valid_jpeg_image):
    """Test that a request with missing style_id returns a 400 error."""
    response = client.post(
        "/stylize_image",
        files={"image": ("test.jpg", valid_jpeg_image, "image/jpeg")},
        data={}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Style ID is required."}

def test_unsupported_image_format(invalid_gif_image):
    """Test that an unsupported image format returns a 400 error."""
    response = client.post(
        "/stylize_image",
        files={"image": ("test.gif", invalid_gif_image, "image/gif")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid image format. Only JPEG and PNG are supported."}

def test_image_exceeding_size_limit(large_image):
    """Test that an image exceeding the size limit returns a 400 error."""
    response = client.post(
        "/stylize_image",
        files={"image": ("large.jpg", large_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 400
    assert response.json() == {"error": f"Image size exceeds the limit of {MAX_UPLOAD_SIZE_MB} MB."}

def test_image_at_size_limit(exact_size_limit_image):
    """Test that an image exactly at the size limit is accepted."""
    response = client.post(
        "/stylize_image",
        files={"image": ("exact_size.jpg", exact_size_limit_image, "image/jpeg")},
        data={"style_id": "test_style"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "original_id" in data
    assert data["style"] == "test_style"
    assert "stylized_image_url" in data
