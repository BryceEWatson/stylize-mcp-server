"""Unit tests for the OpenAI service."""

import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import base64
import io
import pytest
from openai.types import APIError, APIConnectionError, RateLimitError, BadRequestError

from app.openai_service import (
    OpenAIService,
    OpenAIServiceError,
    OpenAIAPIConnectionError,
    OpenAIRateLimitError,
    OpenAIContentPolicyViolationError,
    OpenAIInvalidRequestError
)


class TestOpenAIService(unittest.TestCase):
    """Test suite for the OpenAI service."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a patch for environment variables
        self.env_patcher = patch.dict('os.environ', {
            'OPENAI_API_KEY': 'test_api_key'
        })
        self.env_patcher.start()
        
        # Create a mock for the OpenAI client
        self.mock_openai_client = MagicMock()
        self.client_patcher = patch('app.openai_service.OpenAI', return_value=self.mock_openai_client)
        self.mock_openai = self.client_patcher.start()

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.client_patcher.stop()

    def test_initialization_with_env_var(self):
        """Test initialization with API key from environment variable."""
        service = OpenAIService()
        
        # Verify that the OpenAI client was initialized with the correct API key
        self.mock_openai.assert_called_once_with(api_key='test_api_key')
        
        # Verify that the model is set to dall-e-3
        self.assertEqual(service.model, 'dall-e-3')

    @patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_API_KEY_SECRET_PATH': 'projects/my-project/secrets/openai-api-key'})
    @patch('app.openai_service.secretmanager.SecretManagerServiceClient')
    def test_initialization_with_secret_manager(self, mock_secret_client):
        """Test initialization with API key from Secret Manager."""
        # Mock the secret manager client's access_secret_version method
        mock_secret_instance = MagicMock()
        mock_secret_client.return_value = mock_secret_instance
        
        mock_response = MagicMock()
        mock_response.payload.data.decode.return_value = 'secret_api_key'
        mock_secret_instance.access_secret_version.return_value = mock_response
        
        service = OpenAIService()
        
        # Verify that the secret manager client was called correctly
        mock_secret_instance.access_secret_version.assert_called_once_with(
            name='projects/my-project/secrets/openai-api-key/versions/latest'
        )
        
        # Verify that the OpenAI client was initialized with the correct API key
        self.mock_openai.assert_called_once_with(api_key='secret_api_key')

    @patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_API_KEY_SECRET_PATH': ''})
    def test_initialization_with_missing_env_vars(self):
        """Test initialization with missing environment variables."""
        with self.assertRaises(OpenAIServiceError):
            OpenAIService()

    def test_generate_image_from_prompt_success(self):
        """Test successful image generation from prompt using DALL-E 3."""
        # Mock the image generation response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/generated-image.png'
        mock_image_data.b64_json = None
        
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        
        self.mock_openai_client.images.generate.return_value = mock_response
        
        # Mock the HTTP response for fetching the image
        mock_image_content = b'fake-image-data'
        mock_response = MagicMock()
        mock_response.content = mock_image_content
        
        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_response
            
            service = OpenAIService()
            result = service.generate_image_from_prompt('test prompt')
            
            # Verify that the OpenAI API was called with the correct parameters
            self.mock_openai_client.images.generate.assert_called_once_with(
                model='dall-e-3',
                prompt='test prompt',
                size='1024x1024',
                quality='standard',
                n=1
            )
            
            # Verify that requests.get was called with the correct URL
            mock_get.assert_called_once_with('https://example.com/generated-image.png', timeout=30)
            
            # Verify the result
            self.assertEqual(result, mock_image_content)

    def test_generate_image_from_prompt_with_b64_json(self):
        """Test image generation with base64 encoded response."""
        # Mock the image generation response with b64_json
        mock_image_data = MagicMock()
        mock_image_data.url = None
        mock_image_data.b64_json = 'base64encodeddata'
        
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        
        self.mock_openai_client.images.generate.return_value = mock_response
        
        with patch('app.openai_service.base64.b64decode', return_value=b'decoded-image-data') as mock_b64decode:
            service = OpenAIService()
            result = service.generate_image_from_prompt('test prompt')
            
            # Verify that base64.b64decode was called with the correct data
            mock_b64decode.assert_called_once_with('base64encodeddata')
            
            # Verify the result
            self.assertEqual(result, b'decoded-image-data')

    def test_generate_image_variation_success(self):
        """Test successful image variation generation using DALL-E 2."""
        # Mock the image variation response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/generated-variation.png'
        mock_image_data.b64_json = None
        
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        
        self.mock_openai_client.images.create_variation.return_value = mock_response
        
        # Mock the HTTP response for fetching the image
        mock_image_content = b'fake-variation-image-data'
        mock_http_response = MagicMock()
        mock_http_response.content = mock_image_content
        
        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_http_response
            
            service = OpenAIService()
            reference_image_bytes = b'reference-image-data'
            result = service.generate_image_variation('test variation prompt', reference_image_bytes)
            
            # Verify that the OpenAI API was called with the correct parameters
            self.mock_openai_client.images.create_variation.assert_called_once()
            
            # Get the arguments that were passed to the create_variation method
            call_args = self.mock_openai_client.images.create_variation.call_args[1]
            self.assertEqual(call_args['model'], 'dall-e-2')  # DALL-E 2 is used for variations
            self.assertEqual(call_args['prompt'], 'test variation prompt')
            self.assertEqual(call_args['size'], '1024x1024')
            self.assertEqual(call_args['n'], 1)
            
            # The image parameter should be a BytesIO object with our reference image
            self.assertIsInstance(call_args['image'], io.BytesIO)
            
            # Verify that requests.get was called with the correct URL
            mock_get.assert_called_once_with('https://example.com/generated-variation.png', timeout=30)
            
            # Verify the result
            self.assertEqual(result, mock_image_content)

    def test_generate_image_from_prompt_api_connection_error(self):
        """Test handling of API connection errors."""
        # Mock the OpenAI API to raise an APIConnectionError
        self.mock_openai_client.images.generate.side_effect = APIConnectionError('Connection error')
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIAPIConnectionError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_rate_limit_error(self):
        """Test handling of rate limit errors."""
        # Mock the OpenAI API to raise a RateLimitError
        self.mock_openai_client.images.generate.side_effect = RateLimitError('Rate limit exceeded')
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIRateLimitError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_content_policy_violation(self):
        """Test handling of content policy violations."""
        # Mock the OpenAI API to raise a BadRequestError with content policy violation
        error_message = 'Your request was rejected as a result of our safety system. Your prompt may contain text that is not allowed by our safety system.'
        self.mock_openai_client.images.generate.side_effect = BadRequestError(
            message=error_message,
            code='content_policy_violation'
        )
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIContentPolicyViolationError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_invalid_request(self):
        """Test handling of invalid requests."""
        # Mock the OpenAI API to raise a BadRequestError for an invalid request
        self.mock_openai_client.images.generate.side_effect = BadRequestError(
            message='Invalid request parameters',
            code='invalid_request_error'
        )
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIInvalidRequestError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_api_error(self):
        """Test handling of general API errors."""
        # Mock the OpenAI API to raise an APIError
        self.mock_openai_client.images.generate.side_effect = APIError('API error')
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIServiceError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_variation_api_connection_error(self):
        """Test handling of API connection errors for image variations."""
        # Mock the OpenAI API to raise an APIConnectionError
        self.mock_openai_client.images.create_variation.side_effect = APIConnectionError('Connection error')
        
        service = OpenAIService()
        reference_image_bytes = b'reference-image-data'
        
        with self.assertRaises(OpenAIAPIConnectionError):
            service.generate_image_variation('test prompt', reference_image_bytes)

    def test_empty_response_error(self):
        """Test handling of empty responses from the OpenAI API."""
        # Mock the image generation response with empty data
        mock_response = MagicMock()
        mock_response.data = []
        
        self.mock_openai_client.images.generate.return_value = mock_response
        
        service = OpenAIService()
        
        with self.assertRaises(OpenAIServiceError):
            service.generate_image_from_prompt('test prompt')

    def test_fetch_image_http_error(self):
        """Test handling of HTTP errors when fetching images."""
        # Mock the image generation response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/generated-image.png'
        mock_image_data.b64_json = None
        
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        
        self.mock_openai_client.images.generate.return_value = mock_response
        
        # Mock requests.get to raise an exception
        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.side_effect = Exception('HTTP error')
            
            service = OpenAIService()
            
            with self.assertRaises(OpenAIServiceError):
                service.generate_image_from_prompt('test prompt')

    def test_retry_variation_without_prompt(self):
        """Test retry logic when prompt parameter is not accepted for variations."""
        # Mock a BadRequestError for 'unexpected parameter' on first call
        bad_request_error = BadRequestError(
            message='Unexpected parameter: prompt',
            code='invalid_request_error'
        )
        
        # Create a successful response for the second call
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/retry-variation.png'
        mock_image_data.b64_json = None
        
        mock_response = MagicMock()
        mock_response.data = [mock_image_data]
        
        # Set up the side effect sequence: first call fails, second succeeds
        self.mock_openai_client.images.create_variation.side_effect = [
            bad_request_error,
            mock_response
        ]
        
        # Mock the HTTP response for fetching the image
        mock_image_content = b'retry-variation-image-data'
        mock_http_response = MagicMock()
        mock_http_response.content = mock_image_content
        
        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_http_response
            
            service = OpenAIService()
            reference_image_bytes = b'reference-image-data'
            result = service.generate_image_variation('test prompt', reference_image_bytes)
            
            # Verify the API was called twice
            self.assertEqual(self.mock_openai_client.images.create_variation.call_count, 2)
            
            # Get the arguments for both calls
            first_call_args = self.mock_openai_client.images.create_variation.call_args_list[0][1]
            second_call_args = self.mock_openai_client.images.create_variation.call_args_list[1][1]
            
            # Verify first call had prompt parameter
            self.assertIn('prompt', first_call_args)
            self.assertEqual(first_call_args['prompt'], 'test prompt')
            
            # Verify second call didn't have prompt parameter
            self.assertNotIn('prompt', second_call_args)
            
            # Both calls should have the same model, size, and n parameters
            self.assertEqual(first_call_args['model'], 'dall-e-2')
            self.assertEqual(second_call_args['model'], 'dall-e-2')
            self.assertEqual(first_call_args['size'], '1024x1024')
            self.assertEqual(second_call_args['size'], '1024x1024')
            self.assertEqual(first_call_args['n'], 1)
            self.assertEqual(second_call_args['n'], 1)
            
            # Verify the result was correctly returned
            self.assertEqual(result, mock_image_content)


if __name__ == '__main__':
    unittest.main()
