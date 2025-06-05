"""
Protection middleware for integrating abuse prevention into API endpoints.
"""

import logging
import time
from collections.abc import Callable

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.abuse_monitoring_service import get_abuse_monitoring_service
from app.behavior_analysis_service import RequestEvent, get_behavior_analysis_service
from app.fingerprint_service import extract_fingerprint_from_request
from app.models import SecurityConfig, VerificationChallenge
from app.rate_limiting_service import RateLimitType, get_rate_limiting_service
from app.risk_scoring_service import get_risk_scoring_service

logger = logging.getLogger(__name__)


class AbuseProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for applying abuse protection to API endpoints."""

    def __init__(self, app, config: SecurityConfig | None = None):
        super().__init__(app)
        self.config = config or SecurityConfig()

        # Initialize services
        self.risk_service = get_risk_scoring_service(self.config)
        self.rate_service = get_rate_limiting_service(self.config)
        self.monitoring_service = get_abuse_monitoring_service(self.config)
        self.behavior_service = get_behavior_analysis_service()

        # Endpoint configuration
        self.protected_endpoints = {
            '/stylize_image': {
                'rate_limit_type': RateLimitType.IMAGE_GENERATION,
                'require_fingerprint': True,
                'risk_threshold': 0.8
            },
            '/trial/create': {
                'rate_limit_type': RateLimitType.TRIAL_CREATION_IP,
                'require_fingerprint': True,
                'risk_threshold': 0.6
            },
            '/api/': {  # Covers all /api/ endpoints
                'rate_limit_type': RateLimitType.API_REQUESTS,
                'require_fingerprint': False,
                'risk_threshold': 0.9
            }
        }

        # Excluded endpoints (no protection)
        self.excluded_endpoints = {
            '/health',
            '/docs',
            '/openapi.json',
            '/static/',
            '/favicon.ico'
        }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Main middleware dispatch method."""

        # Skip protection for excluded endpoints
        if self._should_exclude_endpoint(request.url.path):
            return await call_next(request)

        # Skip protection if disabled
        if not self.config.fingerprinting_enabled:
            return await call_next(request)

        start_time = time.time()

        try:
            # Extract client information
            ip_address = self._get_client_ip(request)
            request.headers.get("user-agent", "")

            # Check basic rate limits
            rate_limit_result = await self._check_basic_rate_limits(request, ip_address)
            if not rate_limit_result.allowed:
                return self._create_rate_limit_response(rate_limit_result)

            # Get endpoint configuration
            endpoint_config = self._get_endpoint_config(request.url.path)

            # Perform risk assessment if configured
            if endpoint_config and endpoint_config.get('require_fingerprint'):
                risk_assessment = await self._assess_request_risk(request)

                if risk_assessment and risk_assessment.overall_risk_score > endpoint_config.get('risk_threshold', 0.8):
                    # High risk request - require additional verification or block
                    return await self._handle_high_risk_request(request, risk_assessment)

            # Process the request
            response = await call_next(request)

            # Record behavior for analysis
            await self._record_request_behavior(request, response, start_time)

            return response

        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.error(f"Error in protection middleware: {e}")
            # Continue processing on middleware errors
            return await call_next(request)

    def _should_exclude_endpoint(self, path: str) -> bool:
        """Check if endpoint should be excluded from protection."""
        for excluded in self.excluded_endpoints:
            if path.startswith(excluded):
                return True
        return False

    def _get_endpoint_config(self, path: str) -> dict | None:
        """Get protection configuration for endpoint."""
        for endpoint_pattern, config in self.protected_endpoints.items():
            if path.startswith(endpoint_pattern):
                return config
        return None

    def _get_client_ip(self, request: Request) -> str:
        """Extract real client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()

        return getattr(request.client, "host", "unknown")

    async def _check_basic_rate_limits(self, request: Request, ip_address: str):
        """Check basic rate limits for all requests."""
        return await self.rate_service.check_rate_limits(
            RateLimitType.API_REQUESTS,
            ip_address,
            1.0  # No risk multiplier for basic check
        )

    async def _assess_request_risk(self, request: Request):
        """Assess risk for a request."""
        try:
            # Extract fingerprint if available
            client_fingerprint_data = None
            if request.method == "POST":
                # Try to get fingerprint from request body or headers
                fingerprint_header = request.headers.get("x-client-fingerprint")
                if fingerprint_header:
                    import json
                    try:
                        client_fingerprint_data = json.loads(fingerprint_header)
                    except Exception:
                        pass

            fingerprint = extract_fingerprint_from_request(request, client_fingerprint_data)

            # Create a temporary session for risk assessment
            from app.models import TrialSession
            temp_session = TrialSession(
                session_id="temp-" + str(time.time()),
                ip_address=self._get_client_ip(request),
                user_agent=request.headers.get("user-agent", ""),
                device_fingerprint=fingerprint.device_fingerprint,
                creation_timestamp=time.time(),
                images_used=0,
                max_images=5,
                created_at="",  # Not needed for risk assessment
            )

            return await self.risk_service.assess_trial_session_risk(temp_session, fingerprint)

        except Exception as e:
            logger.error(f"Error assessing request risk: {e}")
            return None

    async def _handle_high_risk_request(self, request: Request, risk_assessment):
        """Handle high-risk requests."""

        ip_address = self._get_client_ip(request)

        # Log high-risk request
        await self.monitoring_service.log_abuse_event({
            'event_id': f"high-risk-{time.time()}",
            'event_type': 'high_risk_request',
            'ip_address': ip_address,
            'user_agent': request.headers.get("user-agent", ""),
            'timestamp': time.time(),
            'details': {
                'risk_score': risk_assessment.overall_risk_score,
                'endpoint': request.url.path,
                'flagged_reasons': risk_assessment.flagged_reasons
            }
        })

        # Determine action based on risk level
        if risk_assessment.overall_risk_score >= self.config.block_threshold:
            # Block the request
            return JSONResponse(
                status_code=429,
                content={
                    'error': 'Request blocked',
                    'message': 'Your request has been blocked due to suspicious activity.',
                    'retry_after': 3600  # 1 hour
                }
            )

        elif risk_assessment.required_challenge != VerificationChallenge.NONE:
            # Require challenge verification
            return JSONResponse(
                status_code=409,
                content={
                    'error': 'Verification required',
                    'message': 'Please complete verification to continue.',
                    'challenge_type': risk_assessment.required_challenge.value,
                    'challenge_config': self._get_challenge_config(risk_assessment.required_challenge)
                }
            )

        # Allow but log
        return None

    def _get_challenge_config(self, challenge_type: VerificationChallenge) -> dict:
        """Get challenge configuration for client."""
        from app.captcha_service import get_captcha_service
        captcha_service = get_captcha_service()
        return captcha_service.get_challenge_config(challenge_type)

    async def _record_request_behavior(self, request: Request, response: Response, start_time: float):
        """Record request behavior for analysis."""
        try:
            # Get session ID if available
            session_id = None
            if hasattr(request.state, 'session_id'):
                session_id = request.state.session_id

            # Extract from authorization header or query params
            if not session_id:
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer "):
                    # This could be a session ID for trial users
                    token = auth_header[7:]
                    if token.startswith("trial-"):
                        session_id = token

            if session_id:
                event = RequestEvent(
                    timestamp=time.time(),
                    endpoint=request.url.path,
                    user_agent=request.headers.get("user-agent", ""),
                    session_id=session_id,
                    ip_address=self._get_client_ip(request),
                    response_time=(time.time() - start_time) * 1000,  # Convert to ms
                    status_code=response.status_code
                )

                self.behavior_service.add_request_event(event)

        except Exception as e:
            logger.error(f"Error recording request behavior: {e}")

    def _create_rate_limit_response(self, rate_limit_result) -> Response:
        """Create rate limit exceeded response."""
        return JSONResponse(
            status_code=429,
            content={
                'error': 'Rate limit exceeded',
                'message': f'Too many requests. Limit: {rate_limit_result.limit} per {rate_limit_result.window_seconds} seconds.',
                'retry_after': rate_limit_result.retry_after,
                'current_usage': rate_limit_result.current_usage,
                'limit': rate_limit_result.limit
            },
            headers={
                'Retry-After': str(rate_limit_result.retry_after) if rate_limit_result.retry_after else '60'
            }
        )


def create_protection_middleware(config: SecurityConfig | None = None):
    """Factory function to create protection middleware."""
    def middleware_factory(app):
        return AbuseProtectionMiddleware(app, config)
    return middleware_factory
