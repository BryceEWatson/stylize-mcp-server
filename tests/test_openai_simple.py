"""Simplified test for the OpenAI service to verify SDK compatibility."""

import unittest
from unittest.mock import MagicMock, patch

# OpenAI SDK v1.79.0 imports
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from app.openai_service import (
    OpenAIService,
)


class TestOpenAISimple(unittest.TestCase):
    """Simple test suite for the OpenAI service."""

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

    def test_initialization(self):
        """Test basic initialization of the OpenAI service."""
        service = OpenAIService()

        # Verify that the OpenAI client was initialized with the correct API key
        self.mock_openai.assert_called_once_with(api_key='test_api_key')

        # Verify that the models are correctly set
        self.assertEqual(service.dalle_model, 'dall-e-3')
        self.assertEqual(service.vision_model, 'gpt-4o')

    def test_gpt4v_analysis(self):
        """Test the GPT-4V analysis functionality with proper SDK v1.79.0 mocking."""
        # Test data
        reference_image_bytes = b'test-reference-image-data'
        prompt = "Create a logo in watercolor style"
        enhanced_prompt = "A refreshed version of the logo with elegant watercolor style"

        # Set up mock for the GPT-4V chat completions
        mock_chat_message = ChatCompletionMessage(role="assistant", content=enhanced_prompt)

        # Create a mock choice with correct structure for SDK v1.79.0
        mock_choice = ChatCompletionChoice(
            index=0,
            message=mock_chat_message,
            finish_reason="stop",
            logprobs=None
        )

        # Create a mock completion with correct structure for SDK v1.79.0
        mock_chat_completion = ChatCompletion(
            id="chatcmpl-123",
            choices=[mock_choice],
            created=1677858242,
            model="gpt-4o",
            object="chat.completion",
            system_fingerprint=None,
            usage=None
        )

        # Set up the mock response
        self.mock_openai_client.chat.completions.create.return_value = mock_chat_completion

        # Mock the _get_image_mime_type method to avoid issues with the test image bytes
        with patch.object(OpenAIService, '_get_image_mime_type', return_value='image/png'):
            service = OpenAIService()
            result = service._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)

            # Verify the result
            self.assertEqual(result, enhanced_prompt)

            # Verify that the chat completions API was called
            self.mock_openai_client.chat.completions.create.assert_called_once()


if __name__ == '__main__':
    unittest.main()
