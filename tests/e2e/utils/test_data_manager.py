"""
Test data management for E2E tests.
"""
import base64
import io
import os
import random
import string
from datetime import datetime
from typing import Any

from PIL import Image, ImageDraw


class TestDataManager:
    """Manages test data for E2E tests."""

    def __init__(self, data_dir: str = "tests/e2e/data"):
        self.data_dir = data_dir
        self.images_dir = os.path.join(data_dir, "images")
        self.contexts_dir = os.path.join(data_dir, "contexts")

        # Ensure directories exist
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.contexts_dir, exist_ok=True)

        self._test_images: dict[str, Any] | None = None
        self._project_contexts: dict[str, Any] | None = None

    def get_test_images(self) -> dict[str, Any]:
        """Get test images, generating them if they don't exist."""
        if self._test_images is None:
            self._test_images = self._load_or_generate_test_images()
        return self._test_images

    def get_project_contexts(self) -> dict[str, Any]:
        """Get test project contexts."""
        if self._project_contexts is None:
            self._project_contexts = self._load_or_generate_project_contexts()
        return self._project_contexts

    def get_test_user_data(self) -> dict[str, Any]:
        """Generate test user data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        return {
            "email": f"test_user_{timestamp}_{random_suffix}@example.com",
            "password": "TestPassword123!",
            "first_name": "Test",
            "last_name": "User",
            "company": "Test Company Inc."
        }

    def _load_or_generate_test_images(self) -> dict[str, Any]:
        """Load existing test images or generate new ones."""
        images = {}

        # Valid JPEG image
        jpeg_path = os.path.join(self.images_dir, "valid_test.jpg")
        if not os.path.exists(jpeg_path):
            self._generate_valid_jpeg(jpeg_path)
        images["valid_jpeg"] = self._load_image_as_base64(jpeg_path)

        # Valid PNG image
        png_path = os.path.join(self.images_dir, "valid_test.png")
        if not os.path.exists(png_path):
            self._generate_valid_png(png_path)
        images["valid_png"] = self._load_image_as_base64(png_path)

        # Large image (for size testing)
        large_path = os.path.join(self.images_dir, "large_test.jpg")
        if not os.path.exists(large_path):
            self._generate_large_image(large_path)
        images["large_image"] = self._load_image_as_base64(large_path)

        # Oversized image (should be rejected)
        oversized_path = os.path.join(self.images_dir, "oversized_test.jpg")
        if not os.path.exists(oversized_path):
            self._generate_oversized_image(oversized_path)
        images["oversized_image"] = self._load_image_as_base64(oversized_path)

        # Corrupted image
        corrupted_path = os.path.join(self.images_dir, "corrupted_test.jpg")
        if not os.path.exists(corrupted_path):
            self._generate_corrupted_image(corrupted_path)
        images["corrupted"] = self._load_file_as_base64(corrupted_path)

        # Logo-style image (for project context testing)
        logo_path = os.path.join(self.images_dir, "test_logo.png")
        if not os.path.exists(logo_path):
            self._generate_logo_image(logo_path)
        images["test_logo"] = self._load_image_as_base64(logo_path)

        return images

    def _load_or_generate_project_contexts(self) -> dict[str, Any]:
        """Load existing project contexts or generate new ones."""
        contexts = {}

        # Minimal context
        contexts["minimal"] = {
            "brand_colors": ["#007ACC"],
            "mood": "professional"
        }

        # Complete context with logo
        test_images = self.get_test_images()
        contexts["complete_with_logo"] = {
            "brand_colors": ["#007ACC", "#FF6B35"],
            "mood": "modern and professional",
            "target_audience": "tech professionals",
            "brand_guidelines": "Clean, minimal design with bold typography",
            "reference_logo": test_images["test_logo"]
        }

        # Complex context
        contexts["complex"] = {
            "brand_colors": ["#1F2937", "#3B82F6", "#EF4444", "#10B981"],
            "mood": "energetic and innovative",
            "target_audience": "young entrepreneurs",
            "brand_guidelines": "Bold, vibrant design with modern aesthetics",
            "style_preferences": ["flat design", "gradients", "sans-serif fonts"],
            "avoid": ["dark themes", "serif fonts", "vintage styles"],
            "keywords": ["innovation", "growth", "technology", "future"]
        }

        # Invalid contexts for error testing
        contexts["invalid_json"] = "invalid json string"
        contexts["empty"] = {}
        contexts["oversized"] = {
            "description": "x" * 10000,  # Very long description
            "brand_colors": ["#" + "".join(random.choices("0123456789ABCDEF", k=6)) for _ in range(100)]
        }

        return contexts

    def _generate_valid_jpeg(self, path: str, width: int = 300, height: int = 300):
        """Generate a valid JPEG test image."""
        image = Image.new("RGB", (width, height), color="lightblue")
        draw = ImageDraw.Draw(image)

        # Add some content to make it more realistic
        draw.rectangle([50, 50, width-50, height-50], outline="darkblue", width=3)
        draw.text((width//2-30, height//2-10), "TEST", fill="darkblue")

        image.save(path, "JPEG", quality=85)

    def _generate_valid_png(self, path: str, width: int = 300, height: int = 300):
        """Generate a valid PNG test image."""
        image = Image.new("RGBA", (width, height), color=(173, 216, 230, 128))
        draw = ImageDraw.Draw(image)

        # Add some content with transparency
        draw.ellipse([50, 50, width-50, height-50], fill=(0, 0, 139, 200), outline=(0, 0, 139, 255), width=3)
        draw.text((width//2-30, height//2-10), "TEST", fill=(0, 0, 139, 255))

        image.save(path, "PNG")

    def _generate_large_image(self, path: str, width: int = 1920, height: int = 1080):
        """Generate a large but acceptable test image."""
        image = Image.new("RGB", (width, height), color="lightgray")
        draw = ImageDraw.Draw(image)

        # Add grid pattern
        grid_size = 100
        for x in range(0, width, grid_size):
            draw.line([(x, 0), (x, height)], fill="darkgray", width=1)
        for y in range(0, height, grid_size):
            draw.line([(0, y), (width, y)], fill="darkgray", width=1)

        # Add center text
        draw.text((width//2-50, height//2-10), "LARGE TEST", fill="black")

        image.save(path, "JPEG", quality=85)

    def _generate_oversized_image(self, path: str, width: int = 4000, height: int = 4000):
        """Generate an oversized test image that should be rejected."""
        image = Image.new("RGB", (width, height), color="red")
        draw = ImageDraw.Draw(image)
        draw.text((width//2-100, height//2-10), "OVERSIZED TEST", fill="white")
        image.save(path, "JPEG", quality=95)

    def _generate_corrupted_image(self, path: str):
        """Generate a corrupted image file."""
        with open(path, "wb") as f:
            f.write(b"This is not a valid image file content")

    def _generate_logo_image(self, path: str, width: int = 200, height: int = 200):
        """Generate a logo-style test image."""
        image = Image.new("RGBA", (width, height), color=(255, 255, 255, 0))
        draw = ImageDraw.Draw(image)

        # Create a simple logo design
        center_x, center_y = width // 2, height // 2

        # Background circle
        draw.ellipse(
            [center_x - 80, center_y - 80, center_x + 80, center_y + 80],
            fill=(0, 122, 204, 255),  # Blue background
            outline=(0, 100, 180, 255),
            width=3
        )

        # Inner design
        draw.ellipse(
            [center_x - 40, center_y - 40, center_x + 40, center_y + 40],
            fill=(255, 255, 255, 255),  # White inner circle
        )

        # Text
        draw.text((center_x - 15, center_y - 10), "TC", fill=(0, 122, 204, 255))

        image.save(path, "PNG")

    def _load_image_as_base64(self, path: str) -> str:
        """Load image file and convert to base64."""
        with open(path, "rb") as f:
            image_data = f.read()
        return base64.b64encode(image_data).decode("utf-8")

    def _load_file_as_base64(self, path: str) -> str:
        """Load any file and convert to base64."""
        with open(path, "rb") as f:
            file_data = f.read()
        return base64.b64encode(file_data).decode("utf-8")

    def create_random_test_image(self, width: int = 300, height: int = 300) -> str:
        """Create a random test image and return as base64."""
        # Generate random colors
        r = random.randint(100, 255)
        g = random.randint(100, 255)
        b = random.randint(100, 255)

        image = Image.new("RGB", (width, height), color=(r, g, b))
        draw = ImageDraw.Draw(image)

        # Add some random shapes
        for _ in range(5):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)

            shape_color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255)
            )

            if random.choice([True, False]):
                draw.rectangle([x1, y1, x2, y2], fill=shape_color)
            else:
                draw.ellipse([x1, y1, x2, y2], fill=shape_color)

        # Convert to base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG")
        image_data = buffer.getvalue()
        return base64.b64encode(image_data).decode("utf-8")

    def get_style_test_data(self) -> list[str]:
        """Get list of style IDs for testing."""
        return ["van_gogh", "pixel_art", "flat_ui_icon", "neumorphic_button", "glassmorphic_card"]

    def get_invalid_style_ids(self) -> list[str]:
        """Get list of invalid style IDs for error testing."""
        return ["nonexistent_style", "invalid-style-id", "", "null", "undefined"]

    def get_test_prompts(self) -> list[str]:
        """Get list of test prompts for image generation."""
        return [
            "a beautiful sunset over mountains",
            "a modern office building",
            "a cute robot character",
            "abstract geometric patterns",
            "a cozy coffee shop interior",
            "a futuristic car design",
            "a fantasy castle in the clouds",
            "a minimalist logo design"
        ]

    def get_problematic_prompts(self) -> list[str]:
        """Get list of prompts that might cause issues."""
        return [
            "",  # Empty prompt
            "x" * 1000,  # Very long prompt
            "🎨🎭🎪🎨🎭🎪" * 50,  # Many emojis
            "SELECT * FROM users;",  # SQL injection attempt
            "<script>alert('xss')</script>",  # XSS attempt
            "../../etc/passwd",  # Path traversal attempt
        ]

    def cleanup_generated_files(self):
        """Clean up generated test files."""
        import shutil
        if os.path.exists(self.data_dir):
            shutil.rmtree(self.data_dir)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.contexts_dir, exist_ok=True)
