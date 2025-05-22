#!/usr/bin/env python3
"""
Test script for deployed Stylize MCP Server
Tests all endpoints with various scenarios
"""

import requests
import json
import base64
import sys
import time
from typing import Dict, Any, Optional
from io import BytesIO
from PIL import Image
import os

# Configuration
BASE_URL = os.getenv("STYLIZE_BASE_URL", "https://stylize-mcp-server-997481449751.us-central1.run.app")
TIMEOUT = 60  # seconds

# Test image data (1x1 pixel PNG)
TEST_IMAGE_BASE64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

class TestResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.response_time = 0
        self.response_data = None
    
    def __str__(self):
        status = "✅ PASS" if self.passed else "❌ FAIL"
        return f"{status} {self.test_name} ({self.response_time:.2f}s) - {self.message}"

class StylizeMCPTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.results = []
        self.session = requests.Session()
    
    def create_test_image(self) -> bytes:
        """Create a simple test image"""
        img = Image.new('RGB', (100, 100), color='red')
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        return buffer.getvalue()
    
    def run_test(self, test_name: str, test_func) -> TestResult:
        """Run a single test and capture results"""
        result = TestResult(test_name)
        print(f"\nRunning: {test_name}")
        
        try:
            start_time = time.time()
            test_func(result)
            result.response_time = time.time() - start_time
        except Exception as e:
            result.passed = False
            result.message = f"Exception: {str(e)}"
            result.response_time = time.time() - start_time
        
        self.results.append(result)
        print(result)
        return result
    
    def test_health_endpoint(self, result: TestResult):
        """Test GET /health"""
        response = self.session.get(f"{self.base_url}/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            result.response_data = data
            if data.get("status") == "healthy":
                result.passed = True
                result.message = f"Service is healthy: {data}"
            else:
                result.passed = False
                result.message = f"Service not healthy: {data}"
        else:
            result.passed = False
            result.message = f"HTTP {response.status_code}: {response.text}"
    
    def test_styles_endpoint(self, result: TestResult):
        """Test GET /styles"""
        response = self.session.get(f"{self.base_url}/styles", timeout=TIMEOUT)
        
        if response.status_code == 200:
            styles = response.json()
            result.response_data = styles
            
            if isinstance(styles, list) and len(styles) > 0:
                # Verify style structure
                required_fields = {"id", "name", "description"}
                first_style = styles[0]
                
                if all(field in first_style for field in required_fields):
                    result.passed = True
                    result.message = f"Found {len(styles)} styles with valid structure"
                else:
                    result.passed = False
                    result.message = f"Style missing required fields. Got: {first_style.keys()}"
            else:
                result.passed = False
                result.message = f"No styles returned or invalid format"
        else:
            result.passed = False
            result.message = f"HTTP {response.status_code}: {response.text}"
    
    def test_stylize_basic(self, result: TestResult):
        """Test POST /stylize_image with basic parameters"""
        image_data = self.create_test_image()
        
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'style_id': 'van_gogh',
            'user_prompt': 'A peaceful landscape'
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            response_data = response.json()
            result.response_data = response_data
            
            # Check required fields
            required_fields = {"stylized_image_url", "prompt_used", "style_applied"}
            if all(field in response_data for field in required_fields):
                result.passed = True
                result.message = f"Successfully stylized image with URL: {response_data['stylized_image_url']}"
            else:
                result.passed = False
                result.message = f"Missing required fields in response: {response_data.keys()}"
        else:
            result.passed = False
            result.message = f"HTTP {response.status_code}: {response.text}"
    
    def test_stylize_with_context(self, result: TestResult):
        """Test POST /stylize_image with project context"""
        image_data = self.create_test_image()
        
        project_context = {
            "project_name": "Test App",
            "project_description": "A test application for API testing",
            "keywords": ["test", "api", "automation"],
            "brand_colors": ["#FF0000", "#00FF00"],
            "artistic_mood": "professional",
            "target_audience": "developers"
        }
        
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'style_id': 'flat_ui_icon',
            'user_prompt': 'A modern app icon',
            'project_context_str': json.dumps(project_context)
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            response_data = response.json()
            result.response_data = response_data
            
            if "stylized_image_url" in response_data:
                result.passed = True
                result.message = f"Successfully stylized with context. URL: {response_data['stylized_image_url']}"
            else:
                result.passed = False
                result.message = f"Missing stylized_image_url in response"
        else:
            result.passed = False
            result.message = f"HTTP {response.status_code}: {response.text}"
    
    def test_stylize_with_reference_logo(self, result: TestResult):
        """Test POST /stylize_image with project context including reference logo"""
        image_data = self.create_test_image()
        
        project_context = {
            "project_name": "Logo Refresh Test",
            "project_description": "Testing logo refresh functionality",
            "keywords": ["logo", "refresh", "modern"],
            "brand_colors": ["#0052CC", "#FFFFFF"],
            "artistic_mood": "sleek and modern",
            "target_audience": "enterprise clients",
            "reference_logo_image_base64": TEST_IMAGE_BASE64
        }
        
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'style_id': 'neumorphic_button',
            'user_prompt': 'Refresh this logo design',
            'project_context_str': json.dumps(project_context)
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            response_data = response.json()
            result.response_data = response_data
            
            if "stylized_image_url" in response_data:
                result.passed = True
                result.message = f"Successfully stylized with reference logo. Context analysis: {response_data.get('context_analysis', 'N/A')[:100]}..."
            else:
                result.passed = False
                result.message = f"Missing stylized_image_url in response"
        else:
            result.passed = False
            result.message = f"HTTP {response.status_code}: {response.text}"
    
    def test_invalid_style_id(self, result: TestResult):
        """Test POST /stylize_image with invalid style_id"""
        image_data = self.create_test_image()
        
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'style_id': 'invalid_style_xyz',
            'user_prompt': 'Test prompt'
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 400:
            result.passed = True
            result.message = f"Correctly rejected invalid style_id with 400 error"
        else:
            result.passed = False
            result.message = f"Expected 400 error, got HTTP {response.status_code}: {response.text}"
    
    def test_missing_required_fields(self, result: TestResult):
        """Test POST /stylize_image with missing required fields"""
        # Test with only user_prompt (missing both image and style_id)
        data = {
            'user_prompt': 'Test prompt'
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            data=data,
            timeout=TIMEOUT
        )
        
        # The deployed version returns 400 for "Image file is required"
        # The new code would return 422 for "Style ID is required"
        if response.status_code in [400, 422]:
            result.passed = True
            result.message = f"Correctly rejected missing required fields with {response.status_code} error"
        else:
            result.passed = False
            result.message = f"Expected 400 or 422 error, got HTTP {response.status_code}: {response.text}"
    
    def test_invalid_project_context_json(self, result: TestResult):
        """Test POST /stylize_image with invalid project context JSON"""
        image_data = self.create_test_image()
        
        files = {
            'image': ('test.png', image_data, 'image/png')
        }
        data = {
            'style_id': 'flat_ui_icon',
            'user_prompt': 'Test prompt',
            'project_context_str': 'invalid json {{'
        }
        
        response = self.session.post(
            f"{self.base_url}/stylize_image",
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        
        if response.status_code == 400:
            result.passed = True
            result.message = f"Correctly rejected invalid JSON with 400 error"
        else:
            result.passed = False
            result.message = f"Expected 400 error, got HTTP {response.status_code}: {response.text}"
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n🧪 Starting Stylize MCP Server tests")
        print(f"📍 Base URL: {self.base_url}")
        print("=" * 80)
        
        # Service health tests
        self.run_test("Health Check", self.test_health_endpoint)
        self.run_test("Get Available Styles", self.test_styles_endpoint)
        
        # Basic stylization tests
        self.run_test("Basic Image Stylization", self.test_stylize_basic)
        self.run_test("Stylization with Project Context", self.test_stylize_with_context)
        self.run_test("Stylization with Reference Logo", self.test_stylize_with_reference_logo)
        
        # Error handling tests
        self.run_test("Invalid Style ID", self.test_invalid_style_id)
        self.run_test("Missing Required Fields", self.test_missing_required_fields)
        self.run_test("Invalid Project Context JSON", self.test_invalid_project_context_json)
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 Test Summary")
        print("=" * 80)
        
        passed = sum(1 for r in self.results if r.passed)
        failed = len(self.results) - passed
        
        print(f"\nTotal tests: {len(self.results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total time: {sum(r.response_time for r in self.results):.2f}s")
        
        if failed > 0:
            print("\n❌ Failed tests:")
            for result in self.results:
                if not result.passed:
                    print(f"  - {result.test_name}: {result.message}")
        
        return failed == 0

def main():
    """Main entry point"""
    # Check if custom base URL provided
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL
    
    tester = StylizeMCPTester(base_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()