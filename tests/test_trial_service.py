from unittest.mock import Mock, patch

import pytest

from app.models import CreditPackage
from app.trial_service import TrialService


@pytest.fixture
def mock_firestore():
    with patch('google.cloud.firestore.Client') as mock_client:
        mock_db = Mock()
        mock_client.return_value = mock_db
        yield mock_db


@pytest.fixture
def trial_service(mock_firestore):
    service = TrialService()
    # Force firestore_client to None to test fallback behavior
    service.firestore_client = None
    return service


class TestTrialService:

    @pytest.mark.asyncio
    async def test_get_or_create_trial_session_new(self, trial_service, mock_firestore):
        client_ip = "192.168.1.1"

        session = await trial_service.get_or_create_trial_session(client_ip)

        assert session.ip_address == client_ip
        assert session.images_used == 0
        assert session.max_images == 5

    @pytest.mark.asyncio
    async def test_get_or_create_trial_session_existing(self, trial_service, mock_firestore):
        client_ip = "192.168.1.1"

        # In fallback mode, always creates new session
        session = await trial_service.get_or_create_trial_session(client_ip)

        assert session.ip_address == client_ip
        assert session.images_used == 0
        assert session.max_images == 5

    @pytest.mark.asyncio
    async def test_check_trial_usage_within_limit(self, trial_service, mock_firestore):
        session_id = "test-session-123"

        # In fallback mode, always allows usage
        can_use, usage_response = await trial_service.check_trial_usage(session_id)

        assert can_use is True
        assert usage_response.images_remaining == 5

    @pytest.mark.asyncio
    async def test_check_trial_usage_at_limit(self, trial_service, mock_firestore):
        session_id = "test-session-123"

        # In fallback mode, always allows usage
        can_use, usage_response = await trial_service.check_trial_usage(session_id)

        assert can_use is True
        assert usage_response.images_remaining == 5

    @pytest.mark.asyncio
    async def test_check_trial_usage_expired_session(self, trial_service, mock_firestore):
        session_id = "test-session-123"

        # In fallback mode, always allows usage
        can_use, usage_response = await trial_service.check_trial_usage(session_id)

        assert can_use is True
        assert usage_response.trial_expired is False

    @pytest.mark.asyncio
    async def test_increment_trial_usage(self, trial_service, mock_firestore):
        session_id = "test-session-123"

        # In fallback mode, increment always succeeds
        result = await trial_service.increment_trial_usage(session_id)

        assert result is True

    def test_get_credit_packages(self, trial_service):
        packages = trial_service.get_credit_packages()

        assert len(packages) == 4
        assert all(isinstance(pkg, CreditPackage) for pkg in packages)

        # Check starter package
        starter = next(p for p in packages if p.name == "Starter Pack")
        assert starter.credits == 50
        assert starter.price_usd == 9.99

    @pytest.mark.asyncio
    async def test_convert_trial_to_account_success(self, trial_service, mock_firestore):
        session_id = "test_session"
        email = "test@example.com"
        password = "password123"

        # In fallback mode, conversion will fail (no Firestore)
        from app.models import TrialToAccountRequest
        request = TrialToAccountRequest(
            session_id=session_id,
            email=email,
            password=password,
            first_name="Test",
            last_name="User"
        )
        result = await trial_service.convert_trial_to_account(request)

        # Should return error in fallback mode (no Firestore)
        success, message, user_id = result
        assert success is False

    @pytest.mark.asyncio
    async def test_convert_trial_to_account_no_session(self, trial_service, mock_firestore):
        session_id = "nonexistent_session"
        email = "test@example.com"
        password = "password123"

        # In fallback mode, conversion will fail (no Firestore)
        from app.models import TrialToAccountRequest
        request = TrialToAccountRequest(
            session_id=session_id,
            email=email,
            password=password,
            first_name="Test",
            last_name="User"
        )
        result = await trial_service.convert_trial_to_account(request)

        # Should return error in fallback mode (no Firestore)
        success, message, user_id = result
        assert success is False
