"""Data models for the Stylize MCP Server."""

import base64
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ProjectContext(BaseModel):
    """Model representing the structured project context information.

    This model captures structured contextual information about a project that will be
    analyzed by the server to refine image generation prompts.
    """
    project_name: str | None = Field(None, description="Project name")
    project_description: str | None = Field(
        None, description="A brief description of the project or the subject of the image"
    )
    target_audience: str | None = Field(
        None, description="Intended audience for the design"
    )
    keywords: list[str] | None = Field(
        None, description="List of relevant keywords, concepts, or themes"
    )
    brand_colors: list[str] | None = Field(
        None, description="Up to 3 primary brand colors (e.g., '#FF0000')"
    )
    desired_elements: list[str] | None = Field(
        None, description="Specific elements or objects that should be included"
    )
    avoid_elements: list[str] | None = Field(
        None, description="Specific elements or objects to avoid"
    )
    artistic_mood: str | None = Field(
        None, description="e.g., 'playful', 'serious', 'futuristic', 'minimalist'"
    )
    reference_logo_image_base64: str | None = Field(
        None,
        description="Base64 encoded string of an existing logo image. If provided, "
                  "the generation will aim to refresh or create variations based on this reference."
    )

    @field_validator('reference_logo_image_base64')
    @classmethod
    def validate_base64(cls, v):
        """Validate that the reference_logo_image_base64 is a valid base64 string."""
        if v is not None:
            # Ensure we're getting a string that can be decoded as base64
            if not isinstance(v, str):
                raise ValueError(f"Expected string, got {type(v).__name__}")

            # Basic character validation before attempting to decode
            import re
            if not re.match('^[A-Za-z0-9+/]*={0,2}$', v):
                raise ValueError("Invalid characters in base64 string")

            try:
                # Try to decode the base64 string
                base64.b64decode(v, validate=True)  # Use validate=True to enforce strict checking
            except Exception as e:
                # Raise a clear validation error
                raise ValueError(f"Invalid base64 encoding: {str(e)}")

            # Additional check - make sure it's actually decodable
            try:
                decoded = base64.b64decode(v)
                if not decoded:  # Empty result isn't valid for our purposes
                    raise ValueError("Base64 decoding produced empty result")
            except Exception as e:
                raise ValueError(f"Base64 validation failed: {str(e)}")
        return v

    @field_validator('brand_colors')
    @classmethod
    def validate_brand_colors(cls, v):
        """Validate that brand colors are in hex format and limit to 3 colors."""
        if v is not None:
            # Limit to 3 colors
            if len(v) > 3:
                v = v[:3]

            # Validate hex format
            for color in v:
                if not color.startswith('#') or len(color) not in [4, 7]:  # #RGB or #RRGGBB
                    raise ValueError(f"Invalid color format: {color}. Must be hex format like '#FF0000'")
        return v


class APIPermission(str, Enum):
    """Available API permissions."""
    STYLIZE = "stylize"
    STYLES = "styles"
    MCP = "mcp"
    ADMIN = "admin"


class APIKeyAuth(BaseModel):
    """Model representing an API key with permissions."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    hashed_key: str = Field(..., description="SHA-256 hashed API key")
    is_active: bool = Field(True, description="Whether the key is currently active")
    permissions: list[APIPermission] = Field(
        default=[APIPermission.STYLIZE, APIPermission.STYLES],
        description="List of permissions granted to this key"
    )
    created_at: str | None = Field(None, description="ISO timestamp when key was created")
    last_used_at: str | None = Field(None, description="ISO timestamp when key was last used")
    usage_count: int = Field(0, description="Number of times this key has been used")


class AuthConfig(BaseModel):
    """Configuration model for authentication settings."""
    enabled: bool = Field(True, description="Whether authentication is enabled")
    allow_dev_bypass: bool = Field(False, description="Allow bypassing auth in development")
    secret_manager_key_path: str | None = Field(
        None,
        description="Path to API keys in Google Cloud Secret Manager"
    )


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating a new API key."""
    name: str = Field(..., description="Human-readable name for the key")
    permissions: list[APIPermission] = Field(
        default=[APIPermission.STYLIZE, APIPermission.STYLES],
        description="List of permissions to grant to this key"
    )


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating a new API key."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    api_key: str = Field(..., description="The actual API key (only shown once)")
    permissions: list[APIPermission] = Field(..., description="Granted permissions")
    created_at: str = Field(..., description="ISO timestamp when key was created")


class APIKeyInfo(BaseModel):
    """Model for API key information (without the actual key)."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    is_active: bool = Field(..., description="Whether the key is currently active")
    permissions: list[APIPermission] = Field(..., description="Granted permissions")
    created_at: str | None = Field(None, description="ISO timestamp when key was created")
    last_used_at: str | None = Field(None, description="ISO timestamp when key was last used")
    usage_count: int = Field(0, description="Number of times this key has been used")


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an existing API key."""
    is_active: bool | None = Field(None, description="Whether the key should be active")
    permissions: list[APIPermission] | None = Field(None, description="New permissions for the key")


# User Management Models for SaaS

class SubscriptionTier(str, Enum):
    """Available subscription tiers."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class UserRegistrationRequest(BaseModel):
    """Request model for user registration."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    company: str | None = Field(None, description="Company name (optional)")


class UserLoginRequest(BaseModel):
    """Request model for user login."""
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class UserProfile(BaseModel):
    """User profile model."""
    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    company: str | None = Field(None, description="Company name")
    subscription_tier: SubscriptionTier = Field(SubscriptionTier.FREE, description="Current subscription tier")
    is_active: bool = Field(True, description="Whether the user account is active")
    is_email_verified: bool = Field(False, description="Whether email is verified")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login_at: str | None = Field(None, description="Last login timestamp")


class UserUsageStats(BaseModel):
    """User usage statistics model."""
    user_id: str = Field(..., description="User identifier")
    current_month_usage: int = Field(0, description="Images generated this month")
    total_usage: int = Field(0, description="Total images generated")
    api_key_count: int = Field(0, description="Number of active API keys")
    last_usage_at: str | None = Field(None, description="Last API usage timestamp")


class SubscriptionLimits(BaseModel):
    """Subscription tier limits."""
    monthly_images: int = Field(..., description="Monthly image generation limit")
    max_api_keys: int = Field(..., description="Maximum number of API keys")
    available_styles: list[str] = Field(..., description="Available style IDs")
    priority_support: bool = Field(False, description="Priority support access")
    custom_styles: bool = Field(False, description="Custom style creation")


class UserAPIKeyRequest(BaseModel):
    """Request model for users creating their own API keys."""
    name: str = Field(..., description="Human-readable name for the key")


class UserAPIKeyResponse(BaseModel):
    """Response model for user API key creation."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    api_key: str = Field(..., description="The actual API key (only shown once)")
    created_at: str = Field(..., description="ISO timestamp when key was created")


class AuthTokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(3600, description="Token expiration in seconds")
    user: UserProfile = Field(..., description="User profile information")


# Anonymous Trial System Models

class TrialSession(BaseModel):
    """Model for anonymous trial sessions with abuse prevention."""
    session_id: str = Field(..., description="Unique session identifier")
    ip_address: str = Field(..., description="User's IP address")
    user_agent: str | None = Field(None, description="User agent string")

    # Fingerprinting fields
    device_fingerprint: str | None = Field(None, description="Server-side device fingerprint")
    client_fingerprint: str | None = Field(None, description="Client-side fingerprint hash")
    canvas_fingerprint: str | None = Field(None, description="Canvas fingerprint (first 32 chars)")
    webgl_fingerprint: str | None = Field(None, description="WebGL fingerprint (first 32 chars)")
    screen_resolution: str | None = Field(None, description="Screen resolution")
    timezone_offset: int | None = Field(None, description="Timezone offset in minutes")

    # Usage tracking
    images_used: int = Field(0, description="Number of images generated in this session")
    max_images: int = Field(5, description="Maximum images allowed for trial")
    created_at: str = Field(..., description="Session creation timestamp")
    last_used_at: str | None = Field(None, description="Last usage timestamp")
    is_expired: bool = Field(False, description="Whether the trial has expired")
    converted_to_user_id: str | None = Field(None, description="User ID if converted to account")

    # Abuse prevention fields
    risk_score: float = Field(0.0, description="Calculated risk score (0.0-1.0)")
    is_flagged: bool = Field(False, description="Whether session is flagged as suspicious")
    flagged_reasons: list[str] = Field(default_factory=list, description="Reasons for flagging")
    verification_challenges_passed: int = Field(0, description="Number of CAPTCHA/challenges passed")
    request_timestamps: list[float] = Field(default_factory=list, description="Request timing history")
    creation_timestamp: float = Field(..., description="Unix timestamp of session creation")

    # VPN/Proxy detection
    is_vpn_detected: bool = Field(False, description="Whether VPN/proxy was detected")
    vpn_confidence: float = Field(0.0, description="VPN detection confidence (0.0-1.0)")
    ip_reputation_score: float = Field(0.0, description="IP reputation score (0.0-1.0, higher = worse)")
    geolocation_data: dict | None = Field(None, description="IP geolocation information")


class TrialUsageResponse(BaseModel):
    """Response model for trial usage information."""
    session_id: str = Field(..., description="Trial session ID")
    images_used: int = Field(..., description="Images used in trial")
    images_remaining: int = Field(..., description="Images remaining in trial")
    trial_expired: bool = Field(False, description="Whether trial has expired")
    upgrade_message: str | None = Field(None, description="Message encouraging upgrade")
    signup_url: str | None = Field(None, description="URL for account registration")


class CreditPackage(BaseModel):
    """Model for credit packages."""
    package_id: str = Field(..., description="Unique package identifier")
    name: str = Field(..., description="Package name")
    credits: int = Field(..., description="Number of image credits")
    price_usd: float = Field(..., description="Price in USD")
    bonus_credits: int = Field(0, description="Bonus credits included")
    popular: bool = Field(False, description="Whether this is a popular package")


class UserCredits(BaseModel):
    """Model for user credit balance."""
    user_id: str = Field(..., description="User identifier")
    credits_balance: int = Field(0, description="Current credit balance")
    total_credits_purchased: int = Field(0, description="Total credits ever purchased")
    credits_used_this_month: int = Field(0, description="Credits used this month")
    last_purchase_at: str | None = Field(None, description="Last credit purchase timestamp")


class CreditPurchaseRequest(BaseModel):
    """Request model for purchasing credits."""
    package_id: str = Field(..., description="Credit package to purchase")
    payment_method_id: str | None = Field(None, description="Stripe payment method ID")


class TrialToAccountRequest(BaseModel):
    """Request model for converting trial to account."""
    session_id: str = Field(..., description="Trial session to convert")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    company: str | None = Field(None, description="Company name (optional)")


class MCPTrialResponse(BaseModel):
    """Response model for MCP trial usage."""
    success: bool = Field(..., description="Whether the operation succeeded")
    image_url: str | None = Field(None, description="Generated image URL if successful")
    trial_info: TrialUsageResponse = Field(..., description="Trial usage information")
    upgrade_options: list[CreditPackage] | None = Field(None, description="Available upgrade options")


# Abuse Prevention Models

class IPRiskAssessment(BaseModel):
    """Model for IP risk assessment results."""
    ip_address: str = Field(..., description="IP address assessed")
    is_vpn: bool = Field(False, description="Whether IP is identified as VPN")
    is_proxy: bool = Field(False, description="Whether IP is identified as proxy")
    is_tor: bool = Field(False, description="Whether IP is Tor exit node")
    is_datacenter: bool = Field(False, description="Whether IP is from datacenter")
    risk_score: float = Field(0.0, description="Overall risk score (0.0-1.0)")
    confidence: float = Field(0.0, description="Confidence in assessment (0.0-1.0)")
    country_code: str | None = Field(None, description="Country code if available")
    asn: str | None = Field(None, description="Autonomous System Number")
    isp: str | None = Field(None, description="Internet Service Provider")


class RateLimitResult(BaseModel):
    """Model for rate limiting results."""
    allowed: bool = Field(..., description="Whether the request is allowed")
    current_usage: int = Field(0, description="Current usage count")
    limit: int = Field(0, description="Rate limit threshold")
    retry_after: int | None = Field(None, description="Seconds to wait before retrying")
    window_seconds: int = Field(0, description="Rate limit window in seconds")


class VerificationChallenge(str, Enum):
    """Types of verification challenges."""
    NONE = "none"
    SIMPLE_MATH = "simple_math"
    RECAPTCHA_V2 = "recaptcha_v2"
    RECAPTCHA_V3 = "recaptcha_v3"
    HCAPTCHA = "hcaptcha"
    EMAIL_VERIFICATION = "email_verification"


class BehaviorAnalysis(BaseModel):
    """Model for behavioral analysis results."""
    session_id: str = Field(..., description="Session identifier")
    timing_regularity_score: float = Field(0.0, description="Score for timing pattern regularity")
    rapid_consumption_score: float = Field(0.0, description="Score for rapid usage patterns")
    interaction_naturalness_score: float = Field(0.0, description="Score for natural interaction patterns")
    overall_bot_probability: float = Field(0.0, description="Overall probability of bot behavior")
    analyzed_requests: int = Field(0, description="Number of requests analyzed")


class AbuseEvent(BaseModel):
    """Model for logging abuse events."""
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of abuse event")
    session_id: str | None = Field(None, description="Related session ID")
    ip_address: str = Field(..., description="IP address involved")
    user_agent: str | None = Field(None, description="User agent string")
    timestamp: str = Field(..., description="Event timestamp")
    details: dict = Field(default_factory=dict, description="Additional event details")
    action_taken: str | None = Field(None, description="Action taken in response")
    severity: str = Field("medium", description="Event severity (low/medium/high)")


class FingerprintValidationRequest(BaseModel):
    """Request model for fingerprint validation."""
    client_fingerprint_data: dict = Field(..., description="Client-side fingerprint data")
    session_id: str | None = Field(None, description="Existing session ID if any")


class SecurityConfig(BaseModel):
    """Configuration model for security settings."""
    fingerprinting_enabled: bool = Field(True, description="Enable device fingerprinting")
    vpn_detection_enabled: bool = Field(True, description="Enable VPN/proxy detection")
    behavior_analysis_enabled: bool = Field(True, description="Enable behavioral analysis")
    captcha_enabled: bool = Field(True, description="Enable CAPTCHA challenges")
    rate_limiting_enabled: bool = Field(True, description="Enable rate limiting")
    abuse_monitoring_enabled: bool = Field(True, description="Enable abuse monitoring")

    # Thresholds
    high_risk_threshold: float = Field(0.7, description="Threshold for high-risk classification")
    captcha_threshold: float = Field(0.5, description="Risk score threshold for CAPTCHA")
    block_threshold: float = Field(0.9, description="Risk score threshold for blocking")

    # Rate limits
    trial_creation_per_ip_per_hour: int = Field(3, description="Trial sessions per IP per hour")
    trial_creation_per_fingerprint_per_hour: int = Field(1, description="Trial sessions per fingerprint per hour")
    image_generation_per_minute: int = Field(2, description="Image generations per minute")

    # VPN detection settings
    vpn_api_timeout_seconds: int = Field(5, description="VPN API timeout")
    vpn_cache_duration_seconds: int = Field(3600, description="VPN detection cache duration")

    # Fingerprint settings
    fingerprint_uniqueness_threshold: float = Field(0.8, description="Threshold for fingerprint uniqueness")
    fingerprint_spoofing_threshold: float = Field(0.6, description="Threshold for fingerprint spoofing detection")
