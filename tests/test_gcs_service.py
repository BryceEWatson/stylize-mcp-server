"""Unit tests for the GCS service."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import timedelta
import os

from app.gcs_service import (
    GcsService,
    GcsServiceError,
    GcsBucketNotFoundError,
    GcsUploadError,
    GcsSignedUrlError
)
from google.cloud.exceptions import GoogleCloudError


@pytest.fixture
def mock_storage_client():
    """Fixture for mocking Google Cloud Storage client."""
    with patch('app.gcs_service.storage.Client') as mock_client:
        # Setup mock bucket
        mock_bucket = MagicMock()
        mock_bucket.exists.return_value = True
        
        # Setup mock blob
        mock_blob = MagicMock()
        mock_bucket.blob.return_value = mock_blob
        
        # Setup client to return mock bucket
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_client.return_value.project = 'test-project'
        
        yield {
            'client': mock_client.return_value,
            'bucket': mock_bucket,
            'blob': mock_blob
        }


class TestGcsService:
    """Tests for the GcsService class."""
    
    def test_init_with_defaults(self, mock_storage_client):
        """Test GcsService initialization with default values."""
        with patch.dict(os.environ, {}, clear=True):
            service = GcsService()
            
            # Verify client initialization
            assert service.client == mock_storage_client['client']
            
            # Verify default bucket names construction
            assert service.project_id == 'test-project'
            assert service.originals_bucket_name == f"stylize-originals-{service.project_id}"
            assert service.variants_bucket_name == f"stylize-variants-{service.project_id}"
    
    def test_init_with_env_vars(self, mock_storage_client):
        """Test GcsService initialization with environment variables."""
        with patch.dict(os.environ, {
            'GCP_PROJECT_ID': 'env-project',
            'ORIGINALS_BUCKET_NAME': 'env-originals',
            'VARIANTS_BUCKET_NAME': 'env-variants'
        }):
            service = GcsService()
            
            # Verify bucket names from environment variables
            assert service.project_id == 'env-project'
            assert service.originals_bucket_name == 'env-originals'
            assert service.variants_bucket_name == 'env-variants'
    
    def test_init_error(self):
        """Test exception handling during initialization."""
        with patch('app.gcs_service.storage.Client', side_effect=Exception('Test error')):
            with pytest.raises(GcsServiceError, match='Failed to initialize GCS service'):
                GcsService()
    
    @pytest.mark.asyncio
    async def test_upload_image_success(self, mock_storage_client):
        """Test successful image upload."""
        service = GcsService()
        
        image_bytes = b'test image data'
        content_type = 'image/png'
        
        await service.upload_image(
            'test-bucket',
            'test-blob.png',
            image_bytes,
            content_type
        )
        
        # Verify bucket was accessed
        mock_storage_client['client'].bucket.assert_called_once_with('test-bucket')
        
        # Verify bucket existence was checked
        mock_storage_client['bucket'].exists.assert_called_once()
        
        # Verify blob was created
        mock_storage_client['bucket'].blob.assert_called_once_with('test-blob.png')
        
        # Verify upload was performed with correct parameters
        mock_storage_client['blob'].upload_from_string.assert_called_once_with(
            image_bytes,
            content_type=content_type
        )
    
    @pytest.mark.asyncio
    async def test_upload_image_bucket_not_found(self, mock_storage_client):
        """Test upload to non-existent bucket."""
        service = GcsService()
        
        # Configure mock to indicate bucket does not exist
        mock_storage_client['bucket'].exists.return_value = False
        
        with pytest.raises(GcsBucketNotFoundError, match="Bucket 'test-bucket' does not exist"):
            await service.upload_image(
                'test-bucket',
                'test-blob.png',
                b'test image data',
                'image/png'
            )
    
    @pytest.mark.asyncio
    async def test_upload_image_google_cloud_error(self, mock_storage_client):
        """Test handling of GoogleCloudError during upload."""
        service = GcsService()
        
        # Configure mock to raise GoogleCloudError during upload
        mock_storage_client['blob'].upload_from_string.side_effect = GoogleCloudError('Test cloud error')
        
        with pytest.raises(GcsUploadError, match="Google Cloud error during upload"):
            await service.upload_image(
                'test-bucket',
                'test-blob.png',
                b'test image data',
                'image/png'
            )
    
    @pytest.mark.asyncio
    async def test_upload_image_unexpected_error(self, mock_storage_client):
        """Test handling of unexpected errors during upload."""
        service = GcsService()
        
        # Configure mock to raise unexpected exception during upload
        mock_storage_client['blob'].upload_from_string.side_effect = Exception('Test unexpected error')
        
        with pytest.raises(GcsUploadError, match="Unexpected error during upload"):
            await service.upload_image(
                'test-bucket',
                'test-blob.png',
                b'test image data',
                'image/png'
            )
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_success(self, mock_storage_client):
        """Test successful signed URL generation."""
        service = GcsService()
        
        # Configure mock to return a test signed URL
        expected_url = 'https://storage.googleapis.com/test-bucket/test-blob.png?signature=abc123'
        mock_storage_client['blob'].generate_signed_url.return_value = expected_url
        
        # Test with default expiration
        url = await service.generate_signed_url('test-bucket', 'test-blob.png')
        
        # Verify the result
        assert url == expected_url
        
        # Verify bucket was accessed
        mock_storage_client['client'].bucket.assert_called_with('test-bucket')
        
        # Verify bucket existence was checked
        mock_storage_client['bucket'].exists.assert_called()
        
        # Verify blob was retrieved
        mock_storage_client['bucket'].blob.assert_called_with('test-blob.png')
        
        # Verify generate_signed_url was called with correct parameters
        mock_storage_client['blob'].generate_signed_url.assert_called_with(
            version="v4",
            expiration=timedelta(hours=1),
            method="GET"
        )
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_custom_expiration(self, mock_storage_client):
        """Test signed URL generation with custom expiration."""
        service = GcsService()
        
        # Configure mock to return a test signed URL
        expected_url = 'https://storage.googleapis.com/test-bucket/test-blob.png?signature=abc123'
        mock_storage_client['blob'].generate_signed_url.return_value = expected_url
        
        # Test with custom expiration
        expiration_hours = 24
        url = await service.generate_signed_url('test-bucket', 'test-blob.png', expiration_hours)
        
        # Verify the result
        assert url == expected_url
        
        # Verify generate_signed_url was called with custom expiration
        mock_storage_client['blob'].generate_signed_url.assert_called_with(
            version="v4",
            expiration=timedelta(hours=expiration_hours),
            method="GET"
        )
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_bucket_not_found(self, mock_storage_client):
        """Test signed URL generation for non-existent bucket."""
        service = GcsService()
        
        # Configure mock to indicate bucket does not exist
        mock_storage_client['bucket'].exists.return_value = False
        
        with pytest.raises(GcsBucketNotFoundError, match="Bucket 'test-bucket' does not exist"):
            await service.generate_signed_url('test-bucket', 'test-blob.png')
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_google_cloud_error(self, mock_storage_client):
        """Test handling of GoogleCloudError during signed URL generation."""
        service = GcsService()
        
        # Configure mock to raise GoogleCloudError during signed URL generation
        mock_storage_client['blob'].generate_signed_url.side_effect = GoogleCloudError('Test cloud error')
        
        with pytest.raises(GcsSignedUrlError, match="Google Cloud error generating signed URL"):
            await service.generate_signed_url('test-bucket', 'test-blob.png')
    
    @pytest.mark.asyncio
    async def test_generate_signed_url_unexpected_error(self, mock_storage_client):
        """Test handling of unexpected errors during signed URL generation."""
        service = GcsService()
        
        # Configure mock to raise unexpected exception during signed URL generation
        mock_storage_client['blob'].generate_signed_url.side_effect = Exception('Test unexpected error')
        
        with pytest.raises(GcsSignedUrlError, match="Unexpected error generating signed URL"):
            await service.generate_signed_url('test-bucket', 'test-blob.png')
