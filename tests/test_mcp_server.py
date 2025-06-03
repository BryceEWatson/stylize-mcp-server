from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from app.mcp_server import check_trial_status, start_trial_session, stylize_image
from app.models import TrialSession


@pytest.fixture
def mock_trial_service():
    """Create a mock TrialService."""
    mock_service = Mock()
    mock_service.get_or_create_trial_session.return_value = TrialSession(
        client_ip="192.168.1.1",
        images_generated=2,
        session_limit=5,
        created_at=datetime.utcnow(),
        last_used=datetime.utcnow()
    )
    mock_service.check_trial_usage.return_value = (True, 3)
    mock_service.increment_trial_usage.return_value = None
    return mock_service


@pytest.fixture
def mock_user_service():
    """Create a mock UserService."""
    mock_service = Mock()
    mock_service.verify_api_key.return_value = "test_user_id"
    mock_service.check_usage_limit.return_value = (True, 50)
    mock_service.increment_usage.return_value = None
    return mock_service


@pytest.fixture
def mock_services():
    """Mock all service dependencies."""
    with patch('app.mcp_server.get_style_service') as mock_style, \
         patch('app.mcp_server.get_context_analysis_service') as mock_context, \
         patch('app.mcp_server.get_openai_service') as mock_openai, \
         patch('app.mcp_server.get_gcs_service') as mock_gcs, \
         patch('app.mcp_server.get_trial_service') as mock_trial, \
         patch('app.mcp_server.get_user_service') as mock_user:

        # Configure style service
        mock_style.return_value.is_valid_style_id.return_value = True
        mock_style.return_value.get_style_by_id.return_value = {
            'id': 'test_style',
            'name': 'Test Style',
            'prompt_fragment': 'test style prompt'
        }

        # Configure OpenAI service
        mock_openai.return_value.generate_image_from_prompt.return_value = b'fake-image-data'
        mock_openai.return_value.transform_image_with_style.return_value = b'fake-transformed-data'

        # Configure GCS service
        async def mock_upload(*args, **kwargs):
            return None
        async def mock_signed_url(*args, **kwargs):
            return 'https://storage.googleapis.com/test-bucket/test-image.png'

        mock_gcs.return_value.upload_image = mock_upload
        mock_gcs.return_value.generate_signed_url = mock_signed_url

        # Configure trial service
        mock_trial.return_value.get_or_create_trial_session.return_value = TrialSession(
            client_ip="192.168.1.1",
            images_generated=2,
            session_limit=5,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )
        mock_trial.return_value.check_trial_usage.return_value = (True, 3)
        mock_trial.return_value.increment_trial_usage.return_value = None

        # Configure user service
        mock_user.return_value.verify_api_key.return_value = "test_user_id"
        mock_user.return_value.check_usage_limit.return_value = (True, 50)
        mock_user.return_value.increment_usage.return_value = None

        yield {
            'style': mock_style.return_value,
            'context': mock_context.return_value,
            'openai': mock_openai.return_value,
            'gcs': mock_gcs.return_value,
            'trial': mock_trial.return_value,
            'user': mock_user.return_value
        }


class TestMCPStyleizeImage:

    @pytest.mark.asyncio
    async def test_stylize_image_with_api_key(self, mock_services):
        """Test MCP stylize_image with API key authentication."""
        result = await stylize_image(
            style_id="test_style",
            api_key="valid_api_key",
            user_prompt="Test prompt"
        )

        assert result.success is True
        assert result.style_id == "test_style"
        assert result.original_id is not None
        assert result.stylized_image_url.startswith("https://")
        assert result.trial_info is None  # No trial info for API key users

    @pytest.mark.asyncio
    async def test_stylize_image_with_session_id(self, mock_services):
        """Test MCP stylize_image with trial session_id."""
        result = await stylize_image(
            style_id="test_style",
            session_id="test_session",
            user_prompt="Test prompt"
        )

        assert result.success is True
        assert result.style_id == "test_style"
        assert result.original_id is not None
        assert result.stylized_image_url.startswith("https://")
        assert result.trial_info is not None
        assert result.trial_info.remaining_images == 2  # 3 remaining - 1 used
        assert "upgrade" in result.trial_info.message.lower()

    @pytest.mark.asyncio
    async def test_stylize_image_no_auth(self, mock_services):
        """Test MCP stylize_image with no authentication."""
        result = await stylize_image(
            style_id="test_style",
            user_prompt="Test prompt"
        )

        assert result.success is False
        assert "authentication required" in result.error.lower()

    @pytest.mark.asyncio
    async def test_stylize_image_trial_limit_exceeded(self, mock_services):
        """Test MCP stylize_image when trial limit is exceeded."""
        # Mock trial usage exceeded
        mock_services['trial'].check_trial_usage.return_value = (False, 0)

        result = await stylize_image(
            style_id="test_style",
            session_id="test_session",
            user_prompt="Test prompt"
        )

        assert result.success is False
        assert "trial limit" in result.error.lower()

    @pytest.mark.asyncio
    async def test_stylize_image_invalid_style(self, mock_services):
        """Test MCP stylize_image with invalid style_id."""
        mock_services['style'].is_valid_style_id.return_value = False

        result = await stylize_image(
            style_id="invalid_style",
            api_key="valid_api_key",
            user_prompt="Test prompt"
        )

        assert result.success is False
        assert "invalid style_id" in result.error.lower()

    @pytest.mark.asyncio
    async def test_stylize_image_with_uploaded_image(self, mock_services):
        """Test MCP stylize_image with uploaded image data."""
        # Create fake base64 image data
        fake_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        result = await stylize_image(
            style_id="test_style",
            api_key="valid_api_key",
            uploaded_image_base64=fake_image_base64
        )

        assert result.success is True
        assert result.style_id == "test_style"
        assert result.stylized_image_url.startswith("https://")
        # Verify transform method was called instead of generate
        mock_services['openai'].transform_image_with_style.assert_called_once()


class TestMCPTrialManagement:

    @pytest.mark.asyncio
    async def test_start_trial_session(self, mock_services):
        """Test MCP start_trial_session."""
        result = await start_trial_session()

        assert result.success is True
        assert result.session_id is not None
        assert result.images_generated == 2
        assert result.session_limit == 5
        assert result.remaining_images == 3
        assert "trial session" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_trial_status(self, mock_services):
        """Test MCP check_trial_status."""
        result = await check_trial_status(session_id="test_session")

        assert result.success is True
        assert result.session_id == "test_session"
        assert result.images_generated == 2
        assert result.session_limit == 5
        assert result.remaining_images == 3
        assert result.can_generate is True

    @pytest.mark.asyncio
    async def test_check_trial_status_limit_exceeded(self, mock_services):
        """Test MCP check_trial_status when limit is exceeded."""
        # Mock trial usage exceeded
        mock_services['trial'].check_trial_usage.return_value = (False, 0)
        mock_services['trial'].get_or_create_trial_session.return_value = TrialSession(
            client_ip="192.168.1.1",
            images_generated=5,
            session_limit=5,
            created_at=datetime.utcnow(),
            last_used=datetime.utcnow()
        )

        result = await check_trial_status(session_id="test_session")

        assert result.success is True
        assert result.images_generated == 5
        assert result.remaining_images == 0
        assert result.can_generate is False
        assert "upgrade" in result.upgrade_message.lower()

    @pytest.mark.asyncio
    async def test_check_trial_status_invalid_session(self, mock_services):
        """Test MCP check_trial_status with invalid session."""
        # Mock session not found
        mock_services['trial'].get_or_create_trial_session.side_effect = Exception("Session not found")

        result = await check_trial_status(session_id="invalid_session")

        assert result.success is False
        assert "error" in result.error.lower()


class TestMCPIntegration:

    @pytest.mark.asyncio
    async def test_full_trial_workflow(self, mock_services):
        """Test complete trial workflow via MCP."""
        # Step 1: Start trial session
        trial_result = await start_trial_session()
        assert trial_result.success is True
        session_id = trial_result.session_id

        # Step 2: Check trial status
        status_result = await check_trial_status(session_id=session_id)
        assert status_result.success is True
        assert status_result.can_generate is True

        # Step 3: Generate image
        image_result = await stylize_image(
            style_id="test_style",
            session_id=session_id,
            user_prompt="Test generation"
        )
        assert image_result.success is True
        assert image_result.trial_info is not None
        assert image_result.trial_info.remaining_images == 2  # One less after generation

    @pytest.mark.asyncio
    async def test_api_key_vs_trial_session(self, mock_services):
        """Test that API key and trial session produce different response formats."""
        # API key request
        api_result = await stylize_image(
            style_id="test_style",
            api_key="valid_api_key",
            user_prompt="Test prompt"
        )

        # Trial session request
        trial_result = await stylize_image(
            style_id="test_style",
            session_id="test_session",
            user_prompt="Test prompt"
        )

        # Both should succeed
        assert api_result.success is True
        assert trial_result.success is True

        # But only trial should have trial_info
        assert api_result.trial_info is None
        assert trial_result.trial_info is not None
        assert trial_result.trial_info.remaining_images is not None
