"""Service for interacting with OpenAI DALL-E 3 API for image generation."""

import logging
import os
import base64
import io
import requests
from typing import Optional, Dict, Any, Union

from openai import OpenAI
from openai.types.images import ImageGenerationResponse
from openai.types import APIError, APIConnectionError, RateLimitError, BadRequestError
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
    """Service for interacting with the OpenAI DALL-E 3 API."""

    def __init__(self):
        """Initialize the OpenAI service with API key from Secret Manager."""
        # Get the API key from Secret Manager or environment variable
        self.api_key = self._get_api_key()
        self.client = OpenAI(api_key=self.api_key)
        self.model = "dall-e-3"  # Using the DALL-E 3 model
        logger.info("OpenAI service initialized with DALL-E 3 model")

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
                model=self.model,
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

    def generate_image_variation(self, prompt: str, reference_image_bytes: bytes) -> bytes:
        """Generate an image variation based on a reference image and prompt.
        
        Note: DALL-E 3 does not directly support image variations/edits. This method uses DALL-E 2
        for image variations which is the only model currently supported by the OpenAI API for this purpose.
        
        Args:
            prompt: The text prompt to guide the variation generation
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
            logger.info(f"Generating image variation using reference image with prompt: {prompt[:100]}...")
            
            # DALL-E 3 does not support image variations/edits, so we have two options:
            # 1. Use DALL-E 2 for create_variation or edit (which supports reference images)
            # 2. Use DALL-E 3 for text-to-image with a detailed prompt about the reference image
            
            # For MVP, we'll use DALL-E 2 with create_variation since it's more reliable for this use case
            # Create a temporary file-like object from bytes
            image_file = io.BytesIO(reference_image_bytes)
            
            # Use DALL-E 2 for image variation (the only model supported for variations)
            logger.info("Using DALL-E 2 for image variation (DALL-E 3 doesn't support image variations)")
            response = self.client.images.create_variation(
                image=image_file,
                prompt=prompt,  # Note: The create_variation endpoint might not use the prompt parameter
                model="dall-e-2",  # DALL-E 2 is the only supported model for variations
                size="1024x1024",
                n=1
            )
            
            return self._get_image_data_from_response(response)
            
        except BadRequestError as e:
            # If the API doesn't accept the prompt parameter for create_variation
            # try again without it (standard OpenAI variation approach)
            if "unexpected parameter" in str(e).lower() and "prompt" in str(e).lower():
                logger.info("Retrying variation without prompt parameter")
                try:
                    # Reset the file pointer
                    image_file.seek(0)
                    
                    # Try again without the prompt parameter
                    response = self.client.images.create_variation(
                        image=image_file,
                        model="dall-e-2",
                        size="1024x1024",
                        n=1
                    )
                    
                    return self._get_image_data_from_response(response)
                    
                except Exception as inner_e:
                    # If this also fails, continue to the error handling below
                    logger.error(f"Error in retry attempt: {str(inner_e)}")
                    error_msg = f"Failed to generate image variation: {str(inner_e)}"
                    raise OpenAIServiceError(error_msg)
            
            # Check if this is a content policy violation
            if "content_policy_violation" in str(e).lower():
                error_msg = f"Content policy violation: {str(e)}"
                logger.error(error_msg)
                raise OpenAIContentPolicyViolationError(error_msg)
            else:
                error_msg = f"Invalid request to OpenAI API: {str(e)}"
                logger.error(error_msg)
                raise OpenAIInvalidRequestError(error_msg)
                
        except APIConnectionError as e:
            error_msg = f"Connection error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIAPIConnectionError(error_msg)
            
        except RateLimitError as e:
            error_msg = f"OpenAI API rate limit exceeded: {str(e)}"
            logger.error(error_msg)
            raise OpenAIRateLimitError(error_msg)
            
        except APIError as e:
            error_msg = f"OpenAI API error: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error with OpenAI API: {str(e)}"
            logger.error(error_msg)
            raise OpenAIServiceError(error_msg)

    def _get_image_data_from_response(self, response: ImageGenerationResponse) -> bytes:
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
