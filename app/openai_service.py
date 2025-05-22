"""Service for interacting with OpenAI GPT-4V and DALL-E 3 APIs for image generation."""

import logging
import os
import base64
import io
import requests
import mimetypes
from typing import Optional, Dict, Any, Union, List, Tuple

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, BadRequestError, Image
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice as ChatCompletionChoice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from typing import Any
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
    """Base exception class for OpenAI service errors."""
    pass


class OpenAIAPIConnectionError(OpenAIServiceError):
    """Exception raised for OpenAI API connection errors."""
    pass


class OpenAIRateLimitError(OpenAIServiceError):
    """Exception raised for OpenAI API rate limit errors."""
    pass


class OpenAIContentPolicyViolationError(OpenAIServiceError):
    """Exception raised for content policy violations."""
    pass


class OpenAIInvalidRequestError(OpenAIServiceError):
    """Exception raised for invalid requests."""
    pass


class OpenAIService:
    """Service for interacting with the OpenAI GPT-4V and DALL-E 3 APIs."""

    def __init__(self):
        """Initialize the OpenAI service with API key from Secret Manager."""
        # Get the API key from Secret Manager or environment variable
        self.api_key = self._get_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.dalle_model = "dall-e-3"  # Using the DALL-E 3 model
        self.vision_model = "gpt-4o"    # Using GPT-4o with vision capabilities
        logger.info(f"OpenAI service initialized with {self.dalle_model} for image generation and {self.vision_model} for vision analysis")

    def _get_api_key(self) -> str:
        """Retrieve the OpenAI API key from Secret Manager or environment variable.
        
        Returns:
            str: The OpenAI API key
        
        Raises:
            OpenAIServiceError: If the API key cannot be retrieved
        """
        # First check if the API key is directly available in environment variables
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            logger.info("Using OpenAI API key from environment variable")
            return api_key
        
        # Otherwise, try to get it from Secret Manager
        secret_path = os.environ.get("OPENAI_API_KEY_SECRET_PATH")
        if not secret_path:
            error_msg = "OPENAI_API_KEY_SECRET_PATH environment variable not set"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        try:
            # Extract project_id and secret_id from the path
            # Path format is expected to be: projects/{project_id}/secrets/{secret_id}/versions/{version}
            # or projects/{project_id}/secrets/{secret_id}
            parts = secret_path.split('/')
            if len(parts) < 4:
                error_msg = f"Invalid secret path format: {secret_path}"
                logger.error(error_msg)
                raise OpenAIServiceError(error_msg)
                
            project_id = parts[1]
            secret_id = parts[3]
            version = "latest" if len(parts) <= 5 else parts[5]
            
            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()
            resource_name = f"projects/{project_id}/secrets/{secret_id}/versions/{version}"
            
            # Access the secret
            response = client.access_secret_version(name=resource_name)
            api_key = response.payload.data.decode("UTF-8")
            
            logger.info(f"Successfully retrieved OpenAI API key from Secret Manager")
            return api_key
            
        except Exception as e:
            error_msg = f"Failed to retrieve OpenAI API key from Secret Manager: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def generate_image_from_prompt(self, prompt: str) -> bytes:
        """Generate an image from a text prompt using DALL-E 3.
        
        Args:
            prompt: The text prompt to guide image generation
            
        Returns:
            bytes: The generated image data as bytes
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the prompt violates content policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            logger.info(f"Generating image from prompt: {prompt[:100]}...")
            
            response = self.client.images.generate(
                model=self.dalle_model,
                prompt=prompt,
                size="1024x1024",  # Standard size for DALL-E 3
                quality="standard",
                n=1  # Generate a single image
            )
            
            return self._get_image_data_from_response(response)
            
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except BadRequestError as e:
            # Check if this is a content policy violation
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def generate_image_from_prompt_and_reference(self, prompt: str, reference_image_bytes: bytes) -> bytes:
        """Generate an image using a two-step process: GPT-4V to analyze the reference image and create an
        enhanced prompt, followed by DALL-E 3 to generate a new image based on that prompt.
        
        Args:
            prompt: The base text prompt to guide the image generation
            reference_image_bytes: The reference image as bytes
            
        Returns:
            bytes: The generated image data as bytes
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the prompt violates content policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            logger.info(f"Starting two-step process: GPT-4V analysis + DALL-E 3 generation with reference image and prompt: {prompt[:100]}...")
            
            # STEP 1: Use GPT-4V to analyze the reference image and enhance the prompt
            logger.info("STEP 1: Analyzing reference image with GPT-4V")
            enhanced_prompt = self._analyze_reference_image_with_gpt4v(prompt, reference_image_bytes)
            
            # STEP 2: Use DALL-E 3 with the enhanced prompt to generate a new image
            logger.info("STEP 2: Using DALL-E 3 with enhanced prompt to generate new image")
            logger.info(f"Enhanced prompt: {enhanced_prompt[:150]}...")
            
            # Call the standard generate_image_from_prompt method with the enhanced prompt
            return self.generate_image_from_prompt(enhanced_prompt)
            
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except BadRequestError as e:
            # Check if this is a content policy violation
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except OpenAIServiceError:
            # Re-raise any of our custom exceptions without wrapping
            raise
            
        except Exception as e:
            error_msg = f"Unexpected error in reference image processing: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def _analyze_reference_image_with_gpt4v(self, prompt: str, reference_image_bytes: bytes) -> str:
        """Use GPT-4V to analyze the reference image and create an enhanced prompt for DALL-E 3.
        
        Args:
            prompt: The base text prompt to guide the image generation
            reference_image_bytes: The reference image as bytes
            
        Returns:
            str: The enhanced prompt optimized for DALL-E 3
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the prompt violates content policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            # Determine the image MIME type or default to PNG
            mime_type = self._get_image_mime_type(reference_image_bytes)
            
            # Encode image to base64
            base64_image = base64.b64encode(reference_image_bytes).decode('utf-8')
            
            # Format image in the required data URL format for the API
            image_url = f"data:{mime_type};base64,{base64_image}"
            
            # Create the system prompt instructing GPT-4V how to analyze the image
            system_prompt = """You are an AI visual consultant tasked with analyzing reference images to generate optimized text prompts for DALL-E 3. 
            Your job is to carefully examine the provided reference image and the user's textual context/style information, 
            then create a detailed, purely textual prompt for DALL-E 3 to generate a refreshed version or new interpretation 
            of the reference image in the specified style. Focus on visual elements, composition, colors, and style 
            while incorporating the user's style preferences. Provide ONLY the final prompt for DALL-E 3, 
            with no explanations, introductions, or additional commentary."""
            
            # Create a precise user prompt that includes both the reference image and the context
            user_prompt = f"""Analyze this reference image and create an enhanced, detailed prompt for DALL-E 3 that would 
            generate a refreshed version of this image in the specified style. 
            
            Style and Context Information: {prompt}
            
            Provide just the enhanced prompt text with no additional explanation or formatting. Your output will be sent directly to DALL-E 3."""
            
            # Call the Chat Completions API with the vision-capable model
            logger.info(f"Calling GPT-4V ({self.vision_model}) to analyze reference image and generate enhanced prompt")
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            # Extract the enhanced prompt from the response
            if not response.choices or not response.choices[0].message or not response.choices[0].message.content:
                raise OpenAIServiceError("GPT-4V returned an empty or invalid response")
                
            enhanced_prompt = response.choices[0].message.content.strip()
            logger.info(f"GPT-4V analysis complete. Generated enhanced prompt: {enhanced_prompt[:100]}...")
            
            return enhanced_prompt
            
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except BadRequestError as e:
            # Check if this is a content policy violation
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error in reference image analysis: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def _get_image_data_from_response(self, response: Any) -> bytes:
        """Extract image data from an OpenAI image generation response.
        
        Args:
            response: The OpenAI image generation response
            
        Returns:
            bytes: The image data as bytes
            
        Raises:
            OpenAIServiceError: If the image data cannot be retrieved
        """
        try:
            # Check if we have a response with data
            if not response.data or len(response.data) == 0:
                error_msg = "OpenAI API returned an empty response"
                logger.error(error_msg)
                raise OpenAIServiceError(error_msg)
                
            # Get the first generated image
            image_data = response.data[0]
            
            # Check if we have a URL or a base64 string
            if image_data.url:
                # Fetch the image data from the URL
                logger.info(f"Fetching image data from URL: {image_data.url}")
                return self._fetch_image_from_url(image_data.url)
                
            elif image_data.b64_json:
                # Decode the base64 encoded image
                logger.info("Decoding base64 image data")
                return base64.b64decode(image_data.b64_json)
                
            else:
                error_msg = "OpenAI API response did not contain image URL or base64 data"
                logger.error(error_msg)
                raise OpenAIServiceError(error_msg)
                
        except Exception as e:
            error_msg = f"Error extracting image data from OpenAI response: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def _fetch_image_from_url(self, url: str) -> bytes:
        """Fetch image data from a URL.
        
        Args:
            url: The URL of the image
            
        Returns:
            bytes: The image data as bytes
            
        Raises:
            OpenAIServiceError: If the image data cannot be fetched
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # Raise exception for HTTP errors
            
            return response.content
            
        except requests.RequestException as e:
            error_msg = f"Error fetching image from URL {url}: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
    def generate_image_variation(self, prompt: str, reference_image_bytes: bytes) -> bytes:
        """Generate a variation of an existing image using DALL-E.
        
        Args:
            prompt: Optional text prompt to guide the variation generation
            reference_image_bytes: The reference image as bytes
            
        Returns:
            bytes: The generated image data as bytes
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the prompt violates content policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            # Prepare the image for the API
            image_file = io.BytesIO(reference_image_bytes)
            
            # First try with prompt parameter (some OpenAI API versions support it)
            try:
                logger.info(f"Generating image variation with prompt: {prompt}")
                response = self.client.images.create_variation(
                    image=image_file,
                    n=1,
                    size="1024x1024",
                    prompt=prompt
                )
            except BadRequestError as e:
                # If 'prompt' parameter is not accepted, retry without it
                if "unexpected parameter" in str(e).lower() and "prompt" in str(e).lower():
                    logger.info("Retrying image variation generation without prompt parameter")
                    image_file.seek(0)  # Reset the file pointer
                    response = self.client.images.create_variation(
                        image=image_file,
                        n=1,
                        size="1024x1024"
                    )
                else:
                    # If it's another type of BadRequestError, re-raise it
                    raise
                    
            # Extract and return the generated image
            return self._get_image_data_from_response(response)
            
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except BadRequestError as e:
            # Check if this is a content policy violation
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error in image variation generation: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
    def transform_image_with_style(self, input_image_bytes: bytes, style_prompt: str) -> bytes:
        """Transform an input image by applying a style using GPT-4V analysis and DALL-E 3 generation.
        
        This method uses a two-step process:
        1. GPT-4V analyzes the input image to understand its content
        2. DALL-E 3 generates a new image based on the analysis and style prompt
        
        Args:
            input_image_bytes: The input image to transform as bytes
            style_prompt: The style prompt describing how to transform the image
            
        Returns:
            bytes: The transformed image data as bytes
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the content violates policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            logger.info(f"Transforming image with style prompt: {style_prompt[:100]}...")
            
            # Use GPT-4V to analyze the input image and create an enhanced prompt
            enhanced_prompt = self._analyze_input_image_for_transformation(input_image_bytes, style_prompt)
            
            # Use DALL-E 3 to generate a new image based on the enhanced prompt
            logger.info(f"Generating transformed image with enhanced prompt: {enhanced_prompt[:150]}...")
            return self.generate_image_from_prompt(enhanced_prompt)
            
        except OpenAIServiceError:
            # Re-raise any of our custom exceptions without wrapping
            raise
        except Exception as e:
            error_msg = f"Unexpected error in image transformation: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
    
    def _analyze_input_image_for_transformation(self, input_image_bytes: bytes, style_prompt: str) -> str:
        """Use GPT-4V to analyze the input image and create an enhanced prompt for transformation.
        
        Args:
            input_image_bytes: The input image as bytes
            style_prompt: The style prompt describing how to transform the image
            
        Returns:
            str: The enhanced prompt optimized for DALL-E 3
            
        Raises:
            OpenAIAPIConnectionError: If there's a connection error with the OpenAI API
            OpenAIRateLimitError: If rate limits are exceeded
            OpenAIContentPolicyViolationError: If the content violates policies
            OpenAIInvalidRequestError: If the request is invalid
            OpenAIServiceError: For other OpenAI API errors
        """
        try:
            # Encode the image to base64
            base64_image = base64.b64encode(input_image_bytes).decode('utf-8')
            
            # Determine the MIME type of the image
            mime_type = self._get_image_mime_type(input_image_bytes)
            
            # Create a message for GPT-4V with the input image
            messages = [
                {
                    "role": "system",
                    "content": "You are an expert at analyzing images and creating detailed prompts for DALL-E 3. "
                               "Your task is to analyze the provided input image and create a prompt that will "
                               "generate a new image with the requested style transformation while preserving "
                               "the essential elements and composition of the original."
                },
                {
                    "role": "user", 
                    "content": [
                        {
                            "type": "text",
                            "text": f"Analyze this image and create a DALL-E 3 prompt that transforms it according to this style: {style_prompt}. "
                                    f"The prompt should maintain the core subject matter and composition while applying the requested style. "
                                    f"Be specific about visual elements, colors, textures, and artistic techniques."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            logger.info("Analyzing input image with GPT-4V for transformation")
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=messages,
                max_tokens=300  # Enough for a detailed prompt
            )
            
            enhanced_prompt = response.choices[0].message.content.strip()
            logger.info(f"GPT-4V analysis complete. Generated transformation prompt: {enhanced_prompt[:100]}...")
            
            return enhanced_prompt
            
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except BadRequestError as e:
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error in input image analysis: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def _get_image_mime_type(self, image_bytes: bytes) -> str:
        """Determine the MIME type of an image from its bytes.
        
        Args:
            image_bytes: The image data as bytes
            
        Returns:
            str: The MIME type of the image (e.g., 'image/jpeg', 'image/png')
        """
        try:
            # Create a BytesIO object from the image bytes
            image_file = io.BytesIO(image_bytes)
            
            # Read the first few bytes to determine the file type
            header = image_file.read(8)  # Usually enough bytes to identify common image formats
            image_file.seek(0)  # Reset the file pointer to the beginning
            
            # Check for common image format signatures
            if header.startswith(b'\xFF\xD8'):  # JPEG signature
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):  # PNG signature
                return 'image/png'
            elif header.startswith(b'GIF87a') or header.startswith(b'GIF89a'):  # GIF signature
                return 'image/gif'
            elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':  # WebP signature
                return 'image/webp'
            else:
                # Fallback: use Python's mimetypes module to guess
                mime_type, _ = mimetypes.guess_type('image.png')  # Default to PNG if uncertain
                return mime_type or 'image/png'
        except Exception as e:
            logger.warning(f"Error determining MIME type: {str(e)}. Defaulting to 'image/png'.")
            return 'image/png'
