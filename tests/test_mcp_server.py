"""Tests for the MCP tools in app.mcp_server.

FastMCP's @mcp.tool() decorator wraps each function in a tool object, so the
tests call the underlying coroutine through ``.fn``.
"""

import base64
from unittest.mock import AsyncMock, Mock, patch

import pytest

from app import mcp_server
from app.models import CreditPackage, TrialSession, TrialUsageResponse


def _fn(tool):
    """Return the plain coroutine behind a FastMCP tool."""
    return getattr(tool, "fn", tool)


stylize_image = _fn(mcp_server.stylize_image)
start_trial_session = _fn(mcp_server.start_trial_session)
check_trial_status = _fn(mcp_server.check_trial_status)

IMAGE_B64 = base64.b64encode(b"fake-image-bytes").decode()

STYLES = [
    {"id": f"style_{i}", "name": f"Style {i}", "prompt_fragment": f"in style {i}"}
    for i in range(5)
]


def _usage(used, remaining, message=None):
    return TrialUsageResponse(
        session_id="trial-test",
        images_used=used,
        images_remaining=remaining,
        trial_expired=remaining == 0,
        upgrade_message=message,
        signup_url="/auth/register",
    )


@pytest.fixture
def services():
    """Patch get_services() with mocks for every dependency the tools use."""
    style = Mock()
    style.get_all_styles.return_value = STYLES
    style.is_valid_style_id.side_effect = lambda sid: any(s["id"] == sid for s in STYLES)
    style.get_style_by_id.side_effect = lambda sid: next(s for s in STYLES if s["id"] == sid)
    style.get_available_style_ids.return_value = [s["id"] for s in STYLES]

    openai = Mock()
    openai.transform_image_with_style.return_value = b"stylized-bytes"

    gcs = Mock()
    gcs.variants_bucket_name = "variants"
    gcs.upload_image = AsyncMock(return_value=None)
    gcs.generate_signed_url = AsyncMock(
        return_value="https://storage.googleapis.com/variants/image.png"
    )

    trial = Mock()
    trial.check_trial_usage = AsyncMock(return_value=(True, _usage(2, 3)))
    trial.increment_trial_usage = AsyncMock(return_value=None)
    trial.get_credit_packages.return_value = [
        CreditPackage(package_id="starter", name="Starter", credits=50, price_usd=9.99)
    ]
    trial.get_or_create_trial_session = AsyncMock(
        return_value=TrialSession(
            session_id="trial-new",
            ip_address="mcp-client",
            created_at="2025-06-01T00:00:00Z",
            creation_timestamp=0.0,
        )
    )

    auth = Mock()
    auth.is_auth_enabled.return_value = False
    auth.should_bypass_auth.return_value = True

    mocks = {
        "style_service": style,
        "openai_service": openai,
        "gcs_service": gcs,
        "context_analysis_service": Mock(),
        "auth_service": auth,
        "trial_service": trial,
    }
    # get_services() builds a new dict on every call, so return a fresh copy.
    with patch.object(mcp_server, "get_services", side_effect=lambda: dict(mocks)):
        yield mocks


class TestStylizeImage:
    async def test_single_style_with_api_key(self, services):
        result = await stylize_image(IMAGE_B64, style_id="style_1", api_key="key")

        assert result["success"] is True
        assert result["style_applied"] == "style_1"
        assert result["stylized_image_url"].startswith("https://")
        assert "trial_info" not in result
        services["openai_service"].transform_image_with_style.assert_called_once()
        services["trial_service"].increment_trial_usage.assert_not_called()

    async def test_prompt_combines_user_prompt_and_style(self, services):
        result = await stylize_image(
            IMAGE_B64, style_id="style_2", user_prompt="a cow", api_key="key"
        )

        assert result["prompt_used"] == "a cow, in style 2"

    async def test_no_style_generates_four_images(self, services):
        result = await stylize_image(IMAGE_B64, api_key="key")

        assert result["multiple_styles"] is True
        assert result["total_images"] == 4
        assert len({img["style_id"] for img in result["images"]}) == 4
        assert services["gcs_service"].upload_image.await_count == 4

    async def test_trial_session_counts_usage(self, services):
        result = await stylize_image(IMAGE_B64, style_id="style_1", session_id="trial-test")

        assert result["success"] is True
        assert result["trial_info"]["images_remaining"] == 3
        services["trial_service"].increment_trial_usage.assert_awaited_once_with(
            "trial-test", 1
        )

    async def test_trial_multi_style_counts_four(self, services):
        await stylize_image(IMAGE_B64, session_id="trial-test")

        services["trial_service"].check_trial_usage.assert_any_await("trial-test", 4)
        services["trial_service"].increment_trial_usage.assert_awaited_once_with(
            "trial-test", 4
        )

    async def test_trial_limit_exceeded_returns_upgrade_options(self, services):
        services["trial_service"].check_trial_usage.return_value = (
            False,
            _usage(5, 0, "Trial limit reached"),
        )

        result = await stylize_image(IMAGE_B64, style_id="style_1", session_id="trial-test")

        assert result["success"] is False
        assert result["error"] == "Trial limit reached"
        assert result["upgrade_options"][0]["package_id"] == "starter"
        services["openai_service"].transform_image_with_style.assert_not_called()

    async def test_no_auth_is_rejected(self, services):
        result = await stylize_image(IMAGE_B64, style_id="style_1")

        assert "api_key or session_id is required" in result["error"]
        services["openai_service"].transform_image_with_style.assert_not_called()

    async def test_invalid_style_is_rejected(self, services):
        result = await stylize_image(IMAGE_B64, style_id="nope", api_key="key")

        assert result["error"].startswith("Invalid style_id")

    async def test_invalid_base64_is_rejected(self, services):
        result = await stylize_image("not base64!", style_id="style_1", api_key="key")

        assert "Invalid base64" in result["error"]

    async def test_services_unavailable(self):
        with patch.object(mcp_server, "get_services", return_value=None):
            result = await stylize_image(IMAGE_B64, style_id="style_1", api_key="key")

        assert result == {"error": "Services not available"}


class TestTrialTools:
    async def test_start_trial_session(self, services):
        result = await start_trial_session()

        assert result["session_id"] == "trial-new"
        assert result["images_remaining"] == 5
        assert result["upgrade_options"][0]["package_id"] == "starter"

    async def test_check_trial_status_active(self, services):
        result = await check_trial_status("trial-test")

        assert result["can_generate"] is True
        assert result["trial_info"]["images_remaining"] == 3
        assert "upgrade_options" not in result

    async def test_check_trial_status_expired(self, services):
        services["trial_service"].check_trial_usage.return_value = (False, _usage(5, 0))

        result = await check_trial_status("trial-test")

        assert result["can_generate"] is False
        assert "upgrade_options" in result

    async def test_check_trial_status_error(self, services):
        services["trial_service"].check_trial_usage.side_effect = Exception("boom")

        result = await check_trial_status("trial-test")

        assert result == {"error": "boom"}
