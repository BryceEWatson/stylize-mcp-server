"""Service for managing Google Cloud Storage operations for the Stylize MCP Server."""

import logging
import os
from datetime import datetime, timedelta
from typing import Optional

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
from google.auth import default
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials

logger = logging.getLogger(__name__)


class GcsServiceError(Exception):
    """Base exception class for GCS service errors."""
    pass


class GcsBucketNotFoundError(GcsServiceError):
    """Exception raised when a GCS bucket cannot be found."""
    pass


class GcsUploadError(GcsServiceError):
    """Exception raised when an upload to GCS fails."""
    pass


class GcsSignedUrlError(GcsServiceError):
    """Exception raised when generating a signed URL fails."""
    pass


class GcsService:
    """Service for interacting with Google Cloud Storage."""

    def __init__(self):
        """Initialize the GCS service.
        
        The service will use Application Default Credentials (ADC) when running
        on Google Cloud Platform. For local development, ensure you have set up
        ADC via gcloud CLI (gcloud auth application-default login).
        
        For signed URL generation on Cloud Run, we use impersonated credentials
        to work around the token-only credential limitation.
        
        Bucket names are derived from environment variables or constructed using
        the project ID if not explicitly set.
        """
        try:
            # Initialize the GCS client
            self.client = storage.Client()
            
            # Get the project ID - used for constructing default bucket names
            self.project_id = os.environ.get('GCP_PROJECT_ID', self.client.project)
            
            # Set up credentials for signed URL generation
            # On Cloud Run, we need to use impersonated credentials for signing
            self._setup_signing_credentials()
            
            # Determine bucket names from environment variables or construct them
            self.originals_bucket_name = os.environ.get(
                'ORIGINALS_BUCKET_NAME', 
                f"stylize-originals-{self.project_id}"
            )
            
            self.variants_bucket_name = os.environ.get(
                'VARIANTS_BUCKET_NAME', 
                f"stylize-variants-{self.project_id}"
            )
            
            logger.info(f"GCS Service initialized with buckets: {self.originals_bucket_name}, {self.variants_bucket_name}")
            
        except Exception as e:
            error_msg = f"Failed to initialize GCS service: {str(e)}"
            logger.error(error_msg)
            raise GcsServiceError(error_msg)

    def _setup_signing_credentials(self):
        """Set up credentials for signed URL generation.
        
        On Cloud Run, we use impersonated credentials to enable signing operations.
        For local development, we try to use the default credentials.
        """
        try:
            # Get default credentials
            credentials, _ = default()
            
            # Check if we're running on Cloud Run (Compute Engine metadata server available)
            if hasattr(credentials, 'service_account_email'):
                # Create impersonated credentials for signing
                service_account_email = f"stylize-mcp-sa@{self.project_id}.iam.gserviceaccount.com"
                self.signing_credentials = ImpersonatedCredentials(
                    source_credentials=credentials,
                    target_principal=service_account_email,
                    target_scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                logger.info(f"Using impersonated credentials for signing: {service_account_email}")
            else:
                # For local development, use default credentials
                self.signing_credentials = credentials
                logger.info("Using default credentials for signing")
                
        except Exception as e:
            logger.warning(f"Could not set up signing credentials: {str(e)}. Signed URLs may not work.")
            self.signing_credentials = None

    async def upload_image(self, bucket_name: str, destination_blob_name: str, 
                           image_bytes: bytes, content_type: str) -> None:
        """Upload an image to a GCS bucket.
        
        Args:
            bucket_name: Name of the GCS bucket
            destination_blob_name: Name/path of the destination blob in the bucket
            image_bytes: Image data to upload
            content_type: MIME type of the image (e.g., 'image/png', 'image/jpeg')
            
        Raises:
            GcsBucketNotFoundError: If the bucket does not exist
            GcsUploadError: If the upload fails
        """
        try:
            # Get the bucket
            bucket = self.client.bucket(bucket_name)
            
            # Check if the bucket exists
            if not bucket.exists():
                error_msg = f"Bucket '{bucket_name}' does not exist"
                logger.error(error_msg)
                raise GcsBucketNotFoundError(error_msg)
            
            # Create a new blob
            blob = bucket.blob(destination_blob_name)
            
            # Upload the image bytes to the blob
            blob.upload_from_string(
                image_bytes,
                content_type=content_type
            )
            
            logger.info(
                f"Successfully uploaded image to {bucket_name}/{destination_blob_name} "
                f"(size: {len(image_bytes)} bytes, content-type: {content_type})"
            )
            
        except GoogleCloudError as e:
            error_msg = f"Google Cloud error during upload to {bucket_name}/{destination_blob_name}: {str(e)}"
            logger.error(error_msg)
            raise GcsUploadError(error_msg)
            
        except Exception as e:
            # Don't catch our own custom exceptions
            if isinstance(e, GcsBucketNotFoundError):
                raise
                
            error_msg = f"Unexpected error during upload to {bucket_name}/{destination_blob_name}: {str(e)}"
            logger.error(error_msg)
            raise GcsUploadError(error_msg)

    async def generate_signed_url(self, bucket_name: str, blob_name: str, 
                                  expiration_hours: int = 1) -> str:
        """Generate a signed URL for a blob in a GCS bucket.
        
        Args:
            bucket_name: Name of the GCS bucket
            blob_name: Name/path of the blob in the bucket
            expiration_hours: Number of hours until the signed URL expires (default: 1)
            
        Returns:
            str: The generated signed URL
            
        Raises:
            GcsBucketNotFoundError: If the bucket does not exist
            GcsSignedUrlError: If generating the signed URL fails
        """
        try:
            # Create a GCS client with signing credentials if available
            if self.signing_credentials:
                signing_client = storage.Client(credentials=self.signing_credentials)
                bucket = signing_client.bucket(bucket_name)
            else:
                bucket = self.client.bucket(bucket_name)
            
            # Check if the bucket exists
            if not bucket.exists():
                error_msg = f"Bucket '{bucket_name}' does not exist"
                logger.error(error_msg)
                raise GcsBucketNotFoundError(error_msg)
            
            # Get the blob
            blob = bucket.blob(blob_name)
            
            # Generate signed URL with version 4 signature
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(hours=expiration_hours),
                method="GET"
            )
            
            logger.info(
                f"Generated signed URL for {bucket_name}/{blob_name} "
                f"(expires in {expiration_hours} hours)"
            )
            
            return signed_url
            
        except GoogleCloudError as e:
            error_msg = f"Google Cloud error generating signed URL for {bucket_name}/{blob_name}: {str(e)}"
            logger.error(error_msg)
            raise GcsSignedUrlError(error_msg)
            
        except Exception as e:
            # Don't catch our own custom exceptions
            if isinstance(e, GcsBucketNotFoundError):
                raise
                
            error_msg = f"Unexpected error generating signed URL for {bucket_name}/{blob_name}: {str(e)}"
            logger.error(error_msg)
            raise GcsSignedUrlError(error_msg)
