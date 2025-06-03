"""Unit tests for the OpenAI service."""

import io
import unittest
from unittest.mock import MagicMock, patch

import requests

# Updated imports for OpenAI SDK v1.79.0+
from openai import APIConnectionError, APIError, BadRequestError, RateLimitError
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from app.openai_service import (
    OpenAIAPIConnectionError,
    OpenAIContentPolicyViolationError,
    OpenAIInvalidRequestError,
    OpenAIRateLimitError,
    OpenAIService,
    OpenAIServiceError,
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

        # Verify that the models are correctly set
        self.assertEqual(service.dalle_model, 'dall-e-3')
        self.assertEqual(service.vision_model, 'gpt-4o')

    @patch.dict('os.environ', {'OPENAI_API_KEY': '', 'OPENAI_API_KEY_SECRET_PATH': 'projects/my-project/secrets/openai-api-key'})
    @patch('app.openai_service.secretmanager.SecretManagerServiceClient')
    def test_initialization_with_secret_manager(self, mock_secret_client):
        """Test initialization with API key from Secret Manager."""
        # Mock the secret manager client's access_secret_version method
        mock_secret_instance = MagicMock()
        mock_secret_client.return_value = mock_secret_instance

        mock_response = MagicMock()
        # The actual implementation accesses response.payload.data as bytes
        mock_response.payload.data = b'secret_api_key'
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
        mock_http_response = MagicMock()
        mock_http_response.content = mock_image_content

        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_http_response

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
        # Mock the image generation response with base64 encoded data
        mock_image_data = MagicMock()
        mock_image_data.url = None
        mock_image_data.b64_json = 'ZmFrZS1pbWFnZS1kYXRhLWJhc2U2NC1lbmNvZGVk'  # base64 encoded string

        mock_response = MagicMock()
        mock_response.data = [mock_image_data]

        self.mock_openai_client.images.generate.return_value = mock_response

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

        # Verify the result is the decoded base64 data
        # We're not verifying the content because it's just a mock, but verifying it's bytes
        self.assertIsInstance(result, bytes)

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
            # Check for prompt parameter - our implementation first tries with prompt
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
        # Create a proper exception side effect
        def api_connection_error(*args, **kwargs):
            # APIConnectionError constructor requires message and request parameters
            # request must be passed as a keyword argument
            raise APIConnectionError(message="Connection error", request={})

        # Set the side effect to raise the exception
        self.mock_openai_client.images.generate.side_effect = api_connection_error

        service = OpenAIService()

        with self.assertRaises(OpenAIAPIConnectionError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_rate_limit_error(self):
        """Test handling of rate limit errors."""
        # Create a proper exception side effect
        def rate_limit_error(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 429
            raise RateLimitError("Rate limit exceeded", response=mock_response, body={})

        # Set the side effect to raise the exception
        self.mock_openai_client.images.generate.side_effect = rate_limit_error

        service = OpenAIService()

        with self.assertRaises(OpenAIRateLimitError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_content_policy_violation(self):
        """Test handling of content policy violations."""
        # Create a proper exception side effect with content policy violation
        def content_policy_violation(*args, **kwargs):
            error_message = 'Your request was rejected as a result of our safety system - content_policy_violation'
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_body = {"error": {"code": "content_policy_violation", "message": error_message}}
            raise BadRequestError(error_message, response=mock_response, body=mock_body)

        # Set the side effect to raise the exception
        self.mock_openai_client.images.generate.side_effect = content_policy_violation

        service = OpenAIService()

        with self.assertRaises(OpenAIContentPolicyViolationError):
            service.generate_image_from_prompt('test prompt containing inappropriate content')

    def test_generate_image_from_prompt_invalid_request(self):
        """Test handling of invalid requests."""
        # Create a proper exception side effect for invalid request
        def invalid_request(*args, **kwargs):
            error_message = 'Invalid request parameters'
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_body = {"error": {"code": "invalid_request_error", "message": error_message}}
            raise BadRequestError(error_message, response=mock_response, body=mock_body)

        # Set the side effect to raise the exception
        self.mock_openai_client.images.generate.side_effect = invalid_request

        service = OpenAIService()

        with self.assertRaises(OpenAIInvalidRequestError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_from_prompt_api_error(self):
        """Test handling of general API errors."""
        # Create a proper exception side effect for API error
        def api_error(*args, **kwargs):
            error_message = 'API error'
            mock_request = {}
            mock_body = {"error": {"message": error_message}}
            raise APIError(error_message, request=mock_request, body=mock_body)

        # Set the side effect to raise the exception
        self.mock_openai_client.images.generate.side_effect = api_error

        service = OpenAIService()

        with self.assertRaises(OpenAIServiceError):
            service.generate_image_from_prompt('test prompt')

    def test_generate_image_variation_api_connection_error(self):
        """Test handling of API connection errors for image variations."""
        # Create a proper exception side effect
        def api_connection_error(*args, **kwargs):
            # APIConnectionError constructor requires message and request parameters
            # request must be passed as a keyword argument
            raise APIConnectionError(message="Connection error", request={})

        # Set the side effect to raise the exception
        self.mock_openai_client.images.create_variation.side_effect = api_connection_error

        service = OpenAIService()
        reference_image_bytes = b'reference-image-data'

        with self.assertRaises(OpenAIAPIConnectionError):
            service.generate_image_variation('test prompt', reference_image_bytes)

    def test_empty_response_error(self):
        """Test handling of empty responses from the OpenAI API."""
        # Mock an empty response
        mock_response = MagicMock()
        mock_response.data = []

        self.mock_openai_client.images.generate.return_value = mock_response

        service = OpenAIService()

        with self.assertRaises(OpenAIServiceError):
            service.generate_image_from_prompt('test prompt')

    def test_fetch_image_http_error(self):
        """Test handling of HTTP errors when fetching images."""
        # Mock a successful image generation response, but a failed HTTP fetch
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/image.png'
        mock_image_data.b64_json = None

        mock_response = MagicMock()
        mock_response.data = [mock_image_data]

        self.mock_openai_client.images.generate.return_value = mock_response

        # Mock an HTTP error when fetching the image
        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException('Failed to fetch image')

            service = OpenAIService()

            with self.assertRaises(OpenAIServiceError):
                service.generate_image_from_prompt('test prompt')

    def test_retry_variation_without_prompt(self):
        """Test retry logic when prompt parameter is not accepted for variations."""
        # Create a proper exception raising function for the first call
        # Create a side effect function that raises an error on first call, then returns mock_response on second call
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error_message = 'Unexpected parameter: prompt'
                mock_err_response = MagicMock()
                mock_err_response.status_code = 400
                mock_body = {"error": {"code": "invalid_request_error", "message": error_message}}
                raise BadRequestError(error_message, response=mock_err_response, body=mock_body)
            else:
                return mock_response

        # Create a successful response for the second call
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/retry-variation.png'
        mock_image_data.b64_json = None

        mock_response = MagicMock()
        mock_response.data = [mock_image_data]

        # Set the side effect function
        self.mock_openai_client.images.create_variation.side_effect = side_effect

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

            # Both calls should have the same size and n parameters
            self.assertEqual(first_call_args['size'], '1024x1024')
            self.assertEqual(second_call_args['size'], '1024x1024')
            self.assertEqual(first_call_args['n'], 1)
            self.assertEqual(second_call_args['n'], 1)

            # Verify the result was correctly returned
            self.assertEqual(result, mock_image_content)

    def test_generate_image_from_prompt_and_reference_success(self):
        """Test successful two-step image generation using GPT-4V analysis and DALL-E 3."""
        # Test data
        reference_image_bytes = b'test-reference-image-data'
        prompt = "Create a logo in watercolor style"
        enhanced_prompt = "A refreshed version of the logo with elegant watercolor style, featuring subtle blue tones and artistic brushstrokes"

        # Step 1: Mock the GPT-4V analysis response
        mock_chat_message = MagicMock()
        mock_chat_message.role = "assistant"
        mock_chat_message.content = enhanced_prompt

        mock_choice = MagicMock()
        mock_choice.message = mock_chat_message
        mock_choice.finish_reason = "stop"
        mock_choice.index = 0

        mock_chat_completion = MagicMock()
        mock_chat_completion.id = "chatcmpl-123"
        mock_chat_completion.choices = [mock_choice]
        mock_chat_completion.created = 1677858242
        mock_chat_completion.model = "gpt-4o"

        # Step 2: Mock the DALL-E 3 image generation response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/generated-image.png'
        mock_image_data.b64_json = None

        mock_image_response = MagicMock()
        mock_image_response.data = [mock_image_data]

        # Set up the side effects for the API calls
        self.mock_openai_client.chat.completions.create.return_value = mock_chat_completion
        self.mock_openai_client.images.generate.return_value = mock_image_response

        # Mock the HTTP response for fetching the image
        mock_image_content = b'fake-image-data'
        mock_http_response = MagicMock()
        mock_http_response.content = mock_image_content

        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_http_response

            # Execute the method under test
            service = OpenAIService()
            result = service.generate_image_from_prompt_and_reference(prompt, reference_image_bytes)

            # Verify GPT-4V was called correctly
            self.mock_openai_client.chat.completions.create.assert_called_once()

            # Verify DALL-E 3 was called with the enhanced prompt
            self.mock_openai_client.images.generate.assert_called_once()
            generate_call_args = self.mock_openai_client.images.generate.call_args[1]
            self.assertEqual(generate_call_args['prompt'], enhanced_prompt)

            # Verify the result
            self.assertEqual(result, mock_image_content)

    def test_get_image_mime_type(self):
        """Test the MIME type detection from image bytes."""
        service = OpenAIService()

        # Test JPEG detection
        jpeg_header = b'\xFF\xD8\xFF' + b'\x00' * 10
        self.assertEqual(service._get_image_mime_type(jpeg_header), 'image/jpeg')

        # Test PNG detection
        png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 10
        self.assertEqual(service._get_image_mime_type(png_header), 'image/png')

        # Test GIF detection
        gif87a_header = b'GIF87a' + b'\x00' * 10
        self.assertEqual(service._get_image_mime_type(gif87a_header), 'image/gif')

        gif89a_header = b'GIF89a' + b'\x00' * 10
        self.assertEqual(service._get_image_mime_type(gif89a_header), 'image/gif')

        # Test fallback for unknown format
        unknown_header = b'\x00\x01\x02\x03'
        self.assertEqual(service._get_image_mime_type(unknown_header), 'image/png')

    def test_analyze_reference_image_with_gpt4v_success(self):
        """Test successful analysis of reference image using GPT-4V."""
        reference_image_bytes = b'test-reference-image-data'
        prompt = "Create a logo in watercolor style"
        enhanced_prompt = "A refreshed version of the logo with elegant watercolor style, featuring subtle blue tones and artistic brushstrokes"

        # Set up mock for the GPT-4V chat completions
        mock_chat_message = MagicMock()
        mock_chat_message.role = "assistant"
        mock_chat_message.content = enhanced_prompt

        # Create a mock choice
        mock_choice = MagicMock()
        mock_choice.message = mock_chat_message
        mock_choice.finish_reason = "stop"
        mock_choice.index = 0

        # Create a mock completion
        mock_chat_completion = MagicMock()
        mock_chat_completion.id = "chatcmpl-123"
        mock_chat_completion.choices = [mock_choice]
        mock_chat_completion.created = 1677858242
        mock_chat_completion.model = "gpt-4o"

        self.mock_openai_client.chat.completions.create.return_value = mock_chat_completion

        service = OpenAIService()
        result = service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)

        # Verify GPT-4V was called correctly
        self.mock_openai_client.chat.completions.create.assert_called_once()
        call_args = self.mock_openai_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args['model'], 'gpt-4o')
        self.assertEqual(len(call_args['messages']), 2)

        # Verify correct system and user messages
        self.assertEqual(call_args['messages'][0]['role'], 'system')
        self.assertEqual(call_args['messages'][1]['role'], 'user')

        # Verify user message contains both text content and image URL
        user_content = call_args['messages'][1]['content']
        self.assertEqual(len(user_content), 2)
        self.assertEqual(user_content[0]['type'], 'text')
        self.assertEqual(user_content[1]['type'], 'image_url')

        # Verify the enhanced prompt was correctly returned
        self.assertEqual(result, enhanced_prompt)

    def test_analyze_reference_image_with_gpt4v_empty_response(self):
        """Test handling of empty responses from GPT-4V analysis."""
        reference_image_bytes = b'test-reference-image-data'
        prompt = "Create a logo in watercolor style"

        # Set up mock for an empty GPT-4V response
        mock_chat_completion = MagicMock(spec=ChatCompletion)
        mock_chat_completion.id = "chatcmpl-123"
        mock_chat_completion.choices = []  # Empty choices list
        mock_chat_completion.created = 1677858242
        mock_chat_completion.model = "gpt-4o"
        self.mock_openai_client.chat.completions.create.return_value = mock_chat_completion

        service = OpenAIService()
        with self.assertRaises(OpenAIServiceError):
            service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)

    def test_analyze_reference_image_api_errors(self):
        """Test handling of API errors during GPT-4V analysis."""
        reference_image_bytes = b'test-reference-image-data'
        prompt = "Create a logo in watercolor style"

        # Test API connection error
        def api_connection_error(*args, **kwargs):
            # APIConnectionError constructor requires message and request parameters
            # request must be passed as a keyword argument
            raise APIConnectionError(message="Connection refused", request={})

        self.mock_openai_client.chat.completions.create.side_effect = api_connection_error
        service = OpenAIService()
        with self.assertRaises(OpenAIAPIConnectionError):
            service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)

        # Test rate limit error
        def rate_limit_error(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 429
            raise RateLimitError("Rate limit exceeded", response=mock_response, body={})

        self.mock_openai_client.chat.completions.create.side_effect = rate_limit_error
        with self.assertRaises(OpenAIRateLimitError):
            service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)

        # Test content policy violation
        def content_policy_violation(*args, **kwargs):
            error_message = 'Request rejected due to content_policy_violation'
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_body = {"error": {"code": "content_policy_violation", "message": error_message}}
            raise BadRequestError(error_message, response=mock_response, body=mock_body)

        self.mock_openai_client.chat.completions.create.side_effect = content_policy_violation
        with self.assertRaises(OpenAIContentPolicyViolationError):
            service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)


    def test_transform_image_with_style_success(self):
        """Test successful image transformation with style."""
        # Mock the chat completion response for GPT-4V analysis
        mock_chat_response = MagicMock(spec=ChatCompletion)
        mock_choice = MagicMock(spec=ChatCompletionChoice)
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.content = "A detailed DALL-E 3 prompt based on the input image with the requested style transformation"
        mock_choice.message = mock_message
        mock_chat_response.choices = [mock_choice]

        self.mock_openai_client.chat.completions.create.return_value = mock_chat_response

        # Mock the image generation response
        mock_image_data = MagicMock()
        mock_image_data.url = 'https://example.com/transformed-image.png'
        mock_image_data.b64_json = None

        mock_response = MagicMock()
        mock_response.data = [mock_image_data]

        self.mock_openai_client.images.generate.return_value = mock_response

        # Mock the HTTP response for fetching the image
        mock_image_content = b'fake-transformed-image-data'
        mock_http_response = MagicMock()
        mock_http_response.content = mock_image_content

        with patch('app.openai_service.requests.get') as mock_get:
            mock_get.return_value = mock_http_response

            service = OpenAIService()
            input_image_bytes = b'input-image-data'
            style_prompt = "transform into watercolor painting style"

            result = service.transform_image_with_style(input_image_bytes, style_prompt)

            # Verify that GPT-4V was called for analysis
            self.mock_openai_client.chat.completions.create.assert_called_once()
            chat_call_args = self.mock_openai_client.chat.completions.create.call_args[1]
            self.assertEqual(chat_call_args['model'], 'gpt-4o')

            # Verify the messages structure
            messages = chat_call_args['messages']
            self.assertEqual(len(messages), 2)
            self.assertEqual(messages[0]['role'], 'system')
            self.assertIn('analyzing images', messages[0]['content'])
            self.assertEqual(messages[1]['role'], 'user')

            # Check user message content
            user_content = messages[1]['content']
            self.assertEqual(len(user_content), 2)
            self.assertEqual(user_content[0]['type'], 'text')
            self.assertIn(style_prompt, user_content[0]['text'])
            self.assertEqual(user_content[1]['type'], 'image_url')

            # Verify that DALL-E 3 was called with the enhanced prompt
            self.mock_openai_client.images.generate.assert_called_once_with(
                model='dall-e-3',
                prompt="A detailed DALL-E 3 prompt based on the input image with the requested style transformation",
                size='1024x1024',
                quality='standard',
                n=1
            )

            # Verify the result
            self.assertEqual(result, mock_image_content)

    def test_transform_image_with_style_gpt4v_error(self):
        """Test error handling when GPT-4V analysis fails."""
        # Make GPT-4V analysis fail with a rate limit error
        def rate_limit_error(*args, **kwargs):
            # Create mock response for RateLimitError
            mock_response = MagicMock()
            mock_response.status_code = 429
            mock_response.headers = {"retry-after": "60"}
            raise RateLimitError("Rate limit exceeded", response=mock_response, body={"error": "rate_limit_exceeded"})

        self.mock_openai_client.chat.completions.create.side_effect = rate_limit_error

        service = OpenAIService()
        input_image_bytes = b'input-image-data'
        style_prompt = "transform into oil painting style"

        with self.assertRaises(OpenAIRateLimitError) as context:
            service.transform_image_with_style(input_image_bytes, style_prompt)

        self.assertIn("Rate limit exceeded", str(context.exception))

    def test_transform_image_with_style_dalle_error(self):
        """Test error handling when DALL-E 3 generation fails."""
        # Mock successful GPT-4V analysis
        mock_chat_response = MagicMock(spec=ChatCompletion)
        mock_choice = MagicMock(spec=ChatCompletionChoice)
        mock_message = MagicMock(spec=ChatCompletionMessage)
        mock_message.content = "Enhanced prompt for DALL-E 3"
        mock_choice.message = mock_message
        mock_chat_response.choices = [mock_choice]

        self.mock_openai_client.chat.completions.create.return_value = mock_chat_response

        # Make DALL-E 3 generation fail
        def api_error(*args, **kwargs):
            # Create mock request for APIError
            mock_request = MagicMock()
            mock_request.method = "POST"
            mock_request.url = "https://api.openai.com/v1/images/generations"
            raise APIError("DALL-E 3 generation failed", request=mock_request, body={"error": "api_error"})

        self.mock_openai_client.images.generate.side_effect = api_error

        service = OpenAIService()
        input_image_bytes = b'input-image-data'
        style_prompt = "transform into sketch style"

        with self.assertRaises(OpenAIServiceError) as context:
            service.transform_image_with_style(input_image_bytes, style_prompt)

        self.assertIn("DALL-E 3 generation failed", str(context.exception))


if __name__ == '__main__':
    unittest.main()
