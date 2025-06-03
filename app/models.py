"""Data models for the Stylize MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import base64


class ProjectContext(BaseModel):
    """Model representing the structured project context information.
    
    This model captures structured contextual information about a project that will be
    analyzed by the server to refine image generation prompts.
    """
    project_name: Optional[str] = Field(None, description="Project name")
    project_description: Optional[str] = Field(
        None, description="A brief description of the project or the subject of the image"
    )
    target_audience: Optional[str] = Field(
        None, description="Intended audience for the design"
    )
    keywords: Optional[List[str]] = Field(
        None, description="List of relevant keywords, concepts, or themes"
    )
    brand_colors: Optional[List[str]] = Field(
        None, description="Up to 3 primary brand colors (e.g., '#FF0000')"
    )
    desired_elements: Optional[List[str]] = Field(
        None, description="Specific elements or objects that should be included"
    )
    avoid_elements: Optional[List[str]] = Field(
        None, description="Specific elements or objects to avoid"
    )
    artistic_mood: Optional[str] = Field(
        None, description="e.g., 'playful', 'serious', 'futuristic', 'minimalist'"
    )
    reference_logo_image_base64: Optional[str] = Field(
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
    permissions: List[APIPermission] = Field(
        default=[APIPermission.STYLIZE, APIPermission.STYLES], 
        description="List of permissions granted to this key"
    )
    created_at: Optional[str] = Field(None, description="ISO timestamp when key was created")
    last_used_at: Optional[str] = Field(None, description="ISO timestamp when key was last used")
    usage_count: int = Field(0, description="Number of times this key has been used")


class AuthConfig(BaseModel):
    """Configuration model for authentication settings."""
    enabled: bool = Field(True, description="Whether authentication is enabled")
    allow_dev_bypass: bool = Field(False, description="Allow bypassing auth in development")
    secret_manager_key_path: Optional[str] = Field(
        None, 
        description="Path to API keys in Google Cloud Secret Manager"
    )


class CreateAPIKeyRequest(BaseModel):
    """Request model for creating a new API key."""
    name: str = Field(..., description="Human-readable name for the key")
    permissions: List[APIPermission] = Field(
        default=[APIPermission.STYLIZE, APIPermission.STYLES], 
        description="List of permissions to grant to this key"
    )


class CreateAPIKeyResponse(BaseModel):
    """Response model for creating a new API key."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    api_key: str = Field(..., description="The actual API key (only shown once)")
    permissions: List[APIPermission] = Field(..., description="Granted permissions")
    created_at: str = Field(..., description="ISO timestamp when key was created")


class APIKeyInfo(BaseModel):
    """Model for API key information (without the actual key)."""
    key_id: str = Field(..., description="Unique identifier for the API key")
    name: str = Field(..., description="Human-readable name for the key")
    is_active: bool = Field(..., description="Whether the key is currently active")
    permissions: List[APIPermission] = Field(..., description="Granted permissions")
    created_at: Optional[str] = Field(None, description="ISO timestamp when key was created")
    last_used_at: Optional[str] = Field(None, description="ISO timestamp when key was last used")
    usage_count: int = Field(0, description="Number of times this key has been used")


class UpdateAPIKeyRequest(BaseModel):
    """Request model for updating an existing API key."""
    is_active: Optional[bool] = Field(None, description="Whether the key should be active")
    permissions: Optional[List[APIPermission]] = Field(None, description="New permissions for the key")


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
    company: Optional[str] = Field(None, description="Company name (optional)")


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
    company: Optional[str] = Field(None, description="Company name")
    subscription_tier: SubscriptionTier = Field(SubscriptionTier.FREE, description="Current subscription tier")
    is_active: bool = Field(True, description="Whether the user account is active")
    is_email_verified: bool = Field(False, description="Whether email is verified")
    created_at: str = Field(..., description="Account creation timestamp")
    last_login_at: Optional[str] = Field(None, description="Last login timestamp")


class UserUsageStats(BaseModel):
    """User usage statistics model."""
    user_id: str = Field(..., description="User identifier")
    current_month_usage: int = Field(0, description="Images generated this month")
    total_usage: int = Field(0, description="Total images generated")
    api_key_count: int = Field(0, description="Number of active API keys")
    last_usage_at: Optional[str] = Field(None, description="Last API usage timestamp")


class SubscriptionLimits(BaseModel):
    """Subscription tier limits."""
    monthly_images: int = Field(..., description="Monthly image generation limit")
    max_api_keys: int = Field(..., description="Maximum number of API keys")
    available_styles: List[str] = Field(..., description="Available style IDs")
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
    """Model for anonymous trial sessions."""
    session_id: str = Field(..., description="Unique session identifier")
    ip_address: str = Field(..., description="User's IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    images_used: int = Field(0, description="Number of images generated in this session")
    max_images: int = Field(5, description="Maximum images allowed for trial")
    created_at: str = Field(..., description="Session creation timestamp")
    last_used_at: Optional[str] = Field(None, description="Last usage timestamp")
    is_expired: bool = Field(False, description="Whether the trial has expired")
    converted_to_user_id: Optional[str] = Field(None, description="User ID if converted to account")


class TrialUsageResponse(BaseModel):
    """Response model for trial usage information."""
    session_id: str = Field(..., description="Trial session ID")
    images_used: int = Field(..., description="Images used in trial")
    images_remaining: int = Field(..., description="Images remaining in trial")
    trial_expired: bool = Field(False, description="Whether trial has expired")
    upgrade_message: Optional[str] = Field(None, description="Message encouraging upgrade")
    signup_url: Optional[str] = Field(None, description="URL for account registration")


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
    last_purchase_at: Optional[str] = Field(None, description="Last credit purchase timestamp")


class CreditPurchaseRequest(BaseModel):
    """Request model for purchasing credits."""
    package_id: str = Field(..., description="Credit package to purchase")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class TrialToAccountRequest(BaseModel):
    """Request model for converting trial to account."""
    session_id: str = Field(..., description="Trial session to convert")
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    company: Optional[str] = Field(None, description="Company name (optional)")


class MCPTrialResponse(BaseModel):
    """Response model for MCP trial usage."""
    success: bool = Field(..., description="Whether the operation succeeded")
    image_url: Optional[str] = Field(None, description="Generated image URL if successful")
    trial_info: TrialUsageResponse = Field(..., description="Trial usage information")
    upgrade_options: Optional[List[CreditPackage]] = Field(None, description="Available upgrade options")
