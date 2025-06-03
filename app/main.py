"""Main application module for the Stylize MCP Server."""

import base64
import json
import logging

# Import the MCP server module
import os
import random
import secrets
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth_service import AuthService
from app.context_analysis_service import ContextAnalysisService
from app.gcs_service import (
    GcsService,
)
from app.models import (
    APIPermission,
    AuthTokenResponse,
    CreateAPIKeyRequest,
    CreateAPIKeyResponse,
    ProjectContext,
    SubscriptionTier,
    TrialToAccountRequest,
    UpdateAPIKeyRequest,
    UserAPIKeyRequest,
    UserAPIKeyResponse,
    UserLoginRequest,
    UserRegistrationRequest,
)
from app.openai_service import (
    OpenAIAPIConnectionError,
    OpenAIContentPolicyViolationError,
    OpenAIInvalidRequestError,
    OpenAIRateLimitError,
    OpenAIService,
    OpenAIServiceError,
)
from app.styles_service import StyleService
from app.trial_service import TrialService
from app.user_service import UserService


# Setup startup error handling and logging
def log_startup_error(e, context="general"):
    """Log startup errors with detailed information."""
    logger = logging.getLogger("startup")
    logger.error(f"Startup error in {context}: {str(e)}", exc_info=True)
    env_vars = []
    for k, v in os.environ.items():
        if k.upper() in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN'] and len(v) > 6:
            env_vars.append(f'{k}={v[:3]}...')
        else:
            env_vars.append(f'{k}=PRESENT')
    logger.error(f"Environment variables: {', '.join(env_vars)}")
    return True  # Error was logged

@contextmanager
def graceful_import():
    """Context manager for gracefully handling import errors."""
    try:
        yield
    except ImportError as e:
        log_startup_error(e, "import")
        print(f"ERROR: Failed to import required module: {e}", file=sys.stderr)

# MCP server will be imported directly when needed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastMCP first (before FastAPI)
mcp_instance = None
mcp_app = None
try:
    from app.mcp_server import mcp
    mcp_instance = mcp
    mcp_app = mcp_instance.http_app(path="/")
    logger.info("FastMCP instance and HTTP app created successfully")
except Exception as e:
    log_startup_error(e, "mcp_import")
    logger.warning("Failed to create MCP HTTP app, continuing without lifespan integration")

# Create FastAPI app with MCP lifespan integration
app = FastAPI(
    title="Stylize MCP Server",
    description="API for stylizing images using generative AI",
    version="0.1.0",
    lifespan=mcp_app.lifespan if mcp_app else None
)

# Service instances (initialized lazily via getters)
_style_service = None
_context_analysis_service = None
_openai_service = None
_gcs_service = None
_auth_service = None
_user_service = None
_trial_service = None

# Security dependencies
security = HTTPBearer(auto_error=False)

# Getter functions for services
def get_style_service():
    """Get or initialize the style service."""
    global _style_service
    if _style_service is None:
        try:
            _style_service = StyleService()
            logger.info(f"Loaded {len(_style_service.get_all_styles())} styles from catalog")
        except Exception as e:
            log_startup_error(e, "style_service_initialization")
            logger.error(f"Failed to initialize style catalog: {str(e)}")
            raise
    return _style_service

def get_context_analysis_service():
    """Get or initialize the context analysis service."""
    global _context_analysis_service
    if _context_analysis_service is None:
        try:
            _context_analysis_service = ContextAnalysisService()
            logger.info("Context analysis service initialized")
        except Exception as e:
            log_startup_error(e, "context_analysis_service_initialization")
            logger.error(f"Failed to initialize context analysis service: {str(e)}")
            raise
    return _context_analysis_service

def get_openai_service():
    """Get or initialize the OpenAI service."""
    global _openai_service
    if _openai_service is None:
        try:
            _openai_service = OpenAIService()
            logger.info("OpenAI service initialized successfully")
        except Exception as e:
            log_startup_error(e, "openai_service_initialization")
            logger.error(f"Failed to initialize OpenAI service: {str(e)}")
            raise
    return _openai_service

def get_gcs_service():
    """Get or initialize the GCS service."""
    global _gcs_service
    if _gcs_service is None:
        try:
            _gcs_service = GcsService()
            logger.info("GCS service initialized successfully")
        except Exception as e:
            log_startup_error(e, "gcs_service_initialization")
            logger.error(f"Failed to initialize GCS service: {str(e)}")
            raise
    return _gcs_service

def get_auth_service():
    """Get or initialize the auth service."""
    global _auth_service
    if _auth_service is None:
        try:
            _auth_service = AuthService()
            logger.info("Auth service initialized successfully")
        except Exception as e:
            log_startup_error(e, "auth_service_initialization")
            logger.error(f"Failed to initialize auth service: {str(e)}")
            raise
    return _auth_service

def get_user_service():
    """Get or initialize the user service."""
    global _user_service
    if _user_service is None:
        try:
            _user_service = UserService()
            logger.info("User service initialized successfully")
        except Exception as e:
            log_startup_error(e, "user_service_initialization")
            logger.error(f"Failed to initialize user service: {str(e)}")
            raise
    return _user_service

def get_trial_service():
    """Get or initialize the trial service."""
    global _trial_service
    if _trial_service is None:
        try:
            _trial_service = TrialService()
            logger.info("Trial service initialized successfully")
        except Exception as e:
            log_startup_error(e, "trial_service_initialization")
            logger.error(f"Failed to initialize trial service: {str(e)}")
            raise
    return _trial_service

# Authentication dependency
async def authenticate(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    required_permission: APIPermission = APIPermission.STYLIZE
):
    """Authenticate requests and check permissions (supports both API keys and JWT tokens)."""
    auth_service = get_auth_service()
    user_service = get_user_service()

    # Check if auth is disabled or in bypass mode
    if not auth_service.is_auth_enabled() or auth_service.should_bypass_auth():
        logger.debug("Authentication bypassed")
        return None

    # Extract token from credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # First, try to validate as JWT token (for user authentication)
    jwt_payload = user_service.verify_token(token)
    if jwt_payload:
        user_id = jwt_payload.get("sub")
        if user_id:
            user = await user_service.get_user_by_id(user_id)
            if user and user.is_active:
                # For user tokens, we only allow certain permissions
                user_permissions = [APIPermission.STYLIZE, APIPermission.STYLES]
                if user.subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
                    user_permissions.append(APIPermission.MCP)

                if required_permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"User subscription does not include {required_permission.value} access",
                    )

                logger.debug(f"Authenticated user request: {user_id}")
                return {"type": "user", "user": user}

    # If JWT validation failed, try API key validation (for admin/API access)
    api_key_auth = await auth_service.validate_api_key(token)
    if api_key_auth:
        # Check permissions
        if not auth_service.check_permission(api_key_auth, required_permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}",
            )

        logger.debug(f"Authenticated API key request: {api_key_auth.key_id}")
        return {"type": "api_key", "api_key": api_key_auth}

    # Neither JWT nor API key validation succeeded
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Permission-specific authentication dependencies
def create_auth_dependency(permission: APIPermission):
    """Factory function to create authentication dependencies with specific permissions."""
    async def auth_dependency(
        credentials: HTTPAuthorizationCredentials | None = Depends(security)
    ):
        return await authenticate(credentials, permission)
    return auth_dependency

require_stylize_permission = create_auth_dependency(APIPermission.STYLIZE)
require_styles_permission = create_auth_dependency(APIPermission.STYLES)
require_mcp_permission = create_auth_dependency(APIPermission.MCP)
require_admin_permission = create_auth_dependency(APIPermission.ADMIN)

# Trial-compatible authentication (allows anonymous users)
async def authenticate_with_trial(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    required_permission: APIPermission = APIPermission.STYLIZE
):
    """Authenticate requests supporting trial users, registered users, and API keys."""
    auth_service = get_auth_service()
    trial_service = get_trial_service()

    # Check if auth is disabled or in bypass mode
    if not auth_service.is_auth_enabled() or auth_service.should_bypass_auth():
        logger.debug("Authentication bypassed")
        return None

    # If credentials provided, try normal authentication
    if credentials:
        try:
            auth_result = await authenticate(credentials, required_permission)
            if auth_result:
                return auth_result
        except HTTPException:
            # If auth fails, fall through to trial mode
            pass

    # No credentials or auth failed - check if this is a trial request
    if required_permission in [APIPermission.STYLIZE, APIPermission.STYLES]:
        # For image generation and styles, allow trial usage
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")

        trial_session = await trial_service.get_or_create_trial_session(client_ip, user_agent)

        return {"type": "trial", "session": trial_session}

    # For other permissions (MCP, admin), require proper authentication
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required for this endpoint",
        headers={"WWW-Authenticate": "Bearer"},
    )

def create_trial_auth_dependency(permission: APIPermission):
    """Factory function to create trial-compatible authentication dependencies."""
    async def auth_dependency(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(security)
    ):
        return await authenticate_with_trial(request, credentials, permission)
    return auth_dependency

# Trial-compatible authentication dependencies
require_stylize_permission_with_trial = create_trial_auth_dependency(APIPermission.STYLIZE)
require_styles_permission_with_trial = create_trial_auth_dependency(APIPermission.STYLES)

# Mount the MCP server (if successfully created above)
if mcp_app:
    try:
        app.mount("/mcp", mcp_app)
        logger.info("Successfully mounted MCP server at /mcp")
    except Exception as e:
        log_startup_error(e, "mcp_server_mounting")
        logger.warning("Failed to mount MCP server, continuing without it")
else:
    logger.warning("MCP app not available for mounting")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, replace with specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    logger.info(
        f"Request {request_id}: {request.method} {request.url.path} from {request.client.host}"
    )
    response = await call_next(request)
    logger.info(f"Response {request_id}: {response.status_code}")
    return response

# Error handling middleware
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected internal server error occurred."},
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Get available services and their status
    services = {
        "app": "ok"
    }

    # Check MCP service health
    try:
        if mcp_app:
            # Test if MCP endpoints are actually functional
            services["mcp"] = "ok"
        else:
            services["mcp"] = "unavailable (HTTP app creation failed)"
    except Exception as e:
        services["mcp"] = f"error: {str(e)}"

    # Check required environment variables
    env_vars_present = {
        "GCP_PROJECT_ID": "ok" if os.environ.get("GCP_PROJECT_ID") else "missing",
        "OPENAI_API_KEY_SECRET_PATH": "ok" if os.environ.get("OPENAI_API_KEY_SECRET_PATH") else "missing"
    }

    # Check style service status
    try:
        styles_count = len(get_style_service().get_all_styles())
        services["styles"] = f"ok ({styles_count} styles)"
    except Exception as e:
        services["styles"] = f"error: {str(e)}"

    # Check authentication service status
    try:
        auth_service = get_auth_service()
        auth_enabled = auth_service.is_auth_enabled()
        dev_bypass = auth_service.should_bypass_auth()
        if auth_enabled and not dev_bypass:
            services["auth"] = "enabled"
        elif dev_bypass:
            services["auth"] = "bypassed (development)"
        else:
            services["auth"] = "disabled"
    except Exception as e:
        services["auth"] = f"error: {str(e)}"

    # Optional env vars
    if os.environ.get("REDIS_HOST") and os.environ.get("REDIS_PORT"):
        env_vars_present["REDIS"] = "ok"
    else:
        env_vars_present["REDIS"] = "not_configured"

    return {
        "status": "ok",
        "services": services,
        "environment": env_vars_present,
        "version": "0.1.0"
    }

# Default max upload size in MB
DEFAULT_MAX_UPLOAD_SIZE_MB = 5

# Get the configured max upload size from environment variable or use default
MAX_UPLOAD_SIZE_MB = int(os.environ.get("MAX_UPLOAD_SIZE_MB", DEFAULT_MAX_UPLOAD_SIZE_MB))
# Convert to bytes for easier comparison
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

# Stylize image endpoint (with trial support)
@app.post("/stylize_image")
async def stylize_image(
    image: UploadFile = Form(None),
    style_id: str | None = Form(None),
    user_prompt: str = Form(None),
    project_context_str: str | None = Form(None),
    auth: dict | None = Depends(require_stylize_permission_with_trial)
):
    """Stylize an uploaded image or generate from text with the specified style.
    
    Args:
        image: Optional image file to stylize
        style_id: The ID of the style to apply
        user_prompt: Optional user prompt to combine with the style's prompt fragment
        project_context_str: Optional JSON string containing structured contextual information
        
    Returns:
        JSON with original_id, style, and stylized_image_url
        
    Raises:
        HTTP 400 Bad Request: If validation fails for any reason
    """
    # Input presence validation - either image or context/prompt is required
    if not image and not project_context_str and not user_prompt:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Either an image file, project context, or user prompt is required."}
        )

    # Generate multiple random styles if no style_id provided
    multiple_styles_mode = style_id is None
    selected_styles = []

    if multiple_styles_mode:
        # Select 4 random styles
        style_service = get_style_service()
        all_styles = style_service.get_all_styles()
        selected_styles = random.sample(all_styles, min(4, len(all_styles)))
        logger.info(f"No style_id provided, generating with 4 random styles: {[s['id'] for s in selected_styles]}")
    else:
        # Validate the provided style_id
        style_service = get_style_service()
        if not style_service.is_valid_style_id(style_id):
            available_styles = style_service.get_available_style_ids()
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid style_id. Available styles are: {available_styles}"}
            )
        selected_styles = [style_service.get_style_by_id(style_id)]


    # Image validation (only if image is provided)
    if image:
        # Content type validation
        valid_content_types = ["image/jpeg", "image/png"]
        if image.content_type not in valid_content_types:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid image format. Only JPEG and PNG are supported."}
            )

        # File size validation
        # Read the first chunk to check the size
        content = await image.read(MAX_UPLOAD_SIZE_BYTES + 1)  # Read one more byte than the limit to check
        await image.seek(0)  # Reset file position after reading

        if len(content) > MAX_UPLOAD_SIZE_BYTES:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Image size exceeds the limit of {MAX_UPLOAD_SIZE_MB} MB."}
            )

    # Process project_context if provided
    project_context = None
    decoded_reference_logo_bytes = None
    context_analysis_result = None

    if project_context_str:
        # Parse the JSON string
        try:
            project_context_dict = json.loads(project_context_str)
            logger.info("Successfully parsed project_context JSON")
        except json.JSONDecodeError as e:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid project_context JSON format: {str(e)}"}
            )

        # Validate the parsed dictionary against our Pydantic model
        try:
            # Pre-validate base64 data if present
            if 'reference_logo_image_base64' in project_context_dict and project_context_dict['reference_logo_image_base64']:
                try:
                    # First do a direct decode attempt to catch obvious errors
                    base64_str = project_context_dict['reference_logo_image_base64']
                    if not isinstance(base64_str, str):
                        raise ValueError(f"Invalid type for base64 data: expected string, got {type(base64_str).__name__}")

                    # Check for invalid characters
                    import re
                    if not re.match('^[A-Za-z0-9+/]*={0,2}$', base64_str):
                        raise ValueError("Invalid characters in base64 string")

                    # Try decoding
                    try:
                        base64.b64decode(base64_str, validate=True)
                    except Exception as e:
                        raise ValueError(f"Base64 decode failed: {str(e)}")

                except Exception as e:
                    logger.error(f"Invalid base64 encoding detected: {str(e)}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": f"Invalid project_context data: Invalid base64 encoding: {str(e)}"}
                    )

            # Continue with Pydantic validation
            from pydantic import ValidationError
            try:
                project_context = ProjectContext(**project_context_dict)
                logger.info("Successfully validated project_context against schema")
            except ValidationError as e:
                logger.error(f"Pydantic validation error: {str(e)}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": f"Invalid project_context data: {str(e)}"}
                )
        except Exception as e:
            logger.error(f"Unexpected error in project_context validation: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": f"Invalid project_context data: {str(e)}"}
            )

        # Now we can analyze the validated ProjectContext
        try:
            # Double-check base64 for added safety
            if project_context.reference_logo_image_base64:
                try:
                    base64.b64decode(project_context.reference_logo_image_base64)
                except Exception as e:
                    # If this fails, we should return a 400 error
                    logger.error(f"Base64 validation failed: {str(e)}")
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={"error": f"Invalid project_context data: Invalid base64 encoding: {str(e)}"}
                    )

            context_analysis_service = get_context_analysis_service()
            context_analysis_result = context_analysis_service.analyze(project_context)
            logger.info("Successfully analyzed project context")
        except Exception as e:
            logger.error(f"Error analyzing project context: {str(e)}")
            # We'll continue with the request even if analysis fails,
            # Just without the context enhancement

    # Log successful validation
    logger.info(f"Received valid stylize_image request with style_id: {style_id}")

    # Calculate usage multiplier based on number of styles
    usage_multiplier = len(selected_styles)

    # Check usage limits based on auth type (accounting for multiple images)
    if auth and auth.get("type") == "user":
        user = auth["user"]
        user_service = get_user_service()

        # Check if user has exceeded limits (accounting for multiple images)
        can_use, limit_message = await user_service.check_usage_limits(user.user_id, usage_multiplier)
        if not can_use:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"error": limit_message}
            )
    elif auth and auth.get("type") == "trial":
        trial_session = auth["session"]
        trial_service = get_trial_service()

        # Check if trial can be used (accounting for multiple images)
        can_use, trial_info = await trial_service.check_trial_usage(trial_session.session_id, usage_multiplier)
        if not can_use:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": trial_info.upgrade_message,
                    "trial_expired": True,
                    "signup_url": trial_info.signup_url,
                    "images_used": trial_info.images_used,
                    "images_remaining": trial_info.images_remaining
                }
            )

    # We already have selected_styles from above

    # Construct context information for reuse across all styles
    context_summary = ""
    brand_colors_text = ""
    avoid_elements_text = ""

    if context_analysis_result:
        # Get context summary from analysis result
        context_summary = context_analysis_result.get("context_summary_string", "")

        # Format brand colors into textual description if available
        brand_colors = context_analysis_result.get("brand_colors_list", [])
        if brand_colors and len(brand_colors) > 0:
            color_names = ", ".join(brand_colors)
            brand_colors_text = f" using colors {color_names}"

        # Format elements to avoid if available
        avoid_elements = context_analysis_result.get("avoid_elements_list", [])
        if avoid_elements and len(avoid_elements) > 0:
            elements_to_avoid = ", ".join(avoid_elements)
            avoid_elements_text = f". Avoid including {elements_to_avoid}"

        # Store reference logo bytes for potential use in image variation API calls
        decoded_reference_logo_bytes = context_analysis_result.get("decoded_reference_logo_bytes")

    def build_final_prompt(style: dict[str, str]) -> str:
        """Helper function to build final prompt for a given style."""
        if context_summary:
            if user_prompt and user_prompt.strip():
                return f"{context_summary}, {user_prompt.strip()}{brand_colors_text}, {style['prompt_fragment']}{avoid_elements_text}"
            else:
                return f"{context_summary}{brand_colors_text}, {style['prompt_fragment']}{avoid_elements_text}"
        else:
            if user_prompt and user_prompt.strip():
                return f"{user_prompt.strip()}, {style['prompt_fragment']}"
            else:
                return style['prompt_fragment']

    # Generate base request ID
    request_id = str(uuid.uuid4())
    if decoded_reference_logo_bytes:
        logger.info(f"Reference logo provided for request_id {request_id}, size: {len(decoded_reference_logo_bytes)} bytes")

    # Get the image bytes for upload to GCS (if image provided)
    try:
        original_image_bytes = None
        original_blob_name = None

        if image:
            # Reset the file pointer to read the image bytes
            await image.seek(0)
            original_image_bytes = await image.read()

            # Construct the blob names for GCS storage
            original_blob_name = f"{request_id}/{image.filename}"

            # Upload the original image to GCS
            logger.info(f"Uploading original image to GCS for request_id {request_id}")
            gcs_service = get_gcs_service()
            await gcs_service.upload_image(
                gcs_service.originals_bucket_name,
                original_blob_name,
                original_image_bytes,
                image.content_type
            )
            logger.info(f"Original image uploaded to GCS for request_id {request_id}")
        else:
            logger.info(f"No input image provided for request_id {request_id}, proceeding with text-only generation")
            gcs_service = get_gcs_service()

        # Initialize services
        openai_service = get_openai_service()

        # Generate images for all selected styles
        generated_images = []

        for style in selected_styles:
            style_id_current = style['id']
            final_prompt = build_final_prompt(style)

            logger.info(f"Generated final prompt for style {style_id_current}: {final_prompt}")

            # Construct the variant blob name
            variant_blob_name = f"{request_id}/{style_id_current}.png"  # Assuming PNG output from DALL-E 3

            # Call OpenAI to generate the image
            # Determine the generation approach based on available inputs
            if original_image_bytes:
                # We have an input image to transform
                logger.info(f"Transforming input image with style {style_id_current} for request_id {request_id}")
                stylized_image_bytes = openai_service.transform_image_with_style(original_image_bytes, final_prompt)
            elif decoded_reference_logo_bytes:
                # We have a reference logo but no input image
                logger.info(f"Starting two-step process: GPT-4V analysis + DALL-E 3 generation with reference logo for style {style_id_current} for request_id {request_id}")
                stylized_image_bytes = openai_service.generate_image_from_prompt_and_reference(final_prompt, decoded_reference_logo_bytes)
            else:
                # Text-only generation
                logger.info(f"Generating image from prompt for style {style_id_current} for request_id {request_id}")
                stylized_image_bytes = openai_service.generate_image_from_prompt(final_prompt)

            # Log successful image generation
            logger.info(f"Successfully generated image data for style {style_id_current} for request_id {request_id}, size: {len(stylized_image_bytes)} bytes")

            # Upload the stylized image to GCS
            logger.info(f"Uploading stylized image for style {style_id_current} to GCS for request_id {request_id}")
            await gcs_service.upload_image(
                gcs_service.variants_bucket_name,
                variant_blob_name,
                stylized_image_bytes,
                "image/png"  # DALL-E 3 outputs PNG format
            )
            logger.info(f"Stylized image for style {style_id_current} uploaded to GCS for request_id {request_id}")

            # Generate a signed URL for the stylized image
            logger.info(f"Generating signed URL for stylized image for style {style_id_current} for request_id {request_id}")
            stylized_image_url = await gcs_service.generate_signed_url(
                gcs_service.variants_bucket_name,
                variant_blob_name
            )
            logger.info(f"Generated signed URL for stylized image for style {style_id_current} for request_id {request_id}: {stylized_image_url}")

            # Add to results
            generated_images.append({
                "style_id": style_id_current,
                "style_name": style['name'],
                "stylized_image_url": stylized_image_url,
                "prompt_used": final_prompt
            })

        # Increment usage based on auth type (for all generated images)
        if auth and auth.get("type") == "user":
            user = auth["user"]
            user_service = get_user_service()
            await user_service.increment_user_usage(user.user_id, usage_multiplier)
            logger.info(f"Incremented usage by {usage_multiplier} for user: {user.user_id}")
        elif auth and auth.get("type") == "trial":
            trial_session = auth["session"]
            trial_service = get_trial_service()
            await trial_service.increment_trial_usage(trial_session.session_id, usage_multiplier)
            logger.info(f"Incremented trial usage by {usage_multiplier} for session: {trial_session.session_id}")

        # Build response based on single vs multiple styles
        if multiple_styles_mode:
            response = {
                "original_id": request_id,
                "multiple_styles": True,
                "images": generated_images,
                "total_images": len(generated_images)
            }
        else:
            # Single style mode - maintain backward compatibility
            response = {
                "original_id": request_id,
                "style": generated_images[0]["style_id"],
                "stylized_image_url": generated_images[0]["stylized_image_url"]
            }

        # Add trial information for trial users
        if auth and auth.get("type") == "trial":
            trial_service = get_trial_service()
            _, trial_info = await trial_service.check_trial_usage(trial_session.session_id)
            response["trial_info"] = {
                "images_used": trial_info.images_used,
                "images_remaining": trial_info.images_remaining,
                "signup_message": f"You have {trial_info.images_remaining} free images remaining. Sign up for 100 free images per month!",
                "signup_url": "/auth/register"
            }

        return response

    except OpenAIContentPolicyViolationError as e:
        # 400 Bad Request for content policy violations
        logger.error(f"Content policy violation for request_id {request_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Content policy violation: {str(e)}"}
        )

    except OpenAIInvalidRequestError as e:
        # 400 Bad Request for invalid requests
        logger.error(f"Invalid request for request_id {request_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid request: {str(e)}"}
        )

    except OpenAIRateLimitError as e:
        # 429 Too Many Requests for rate limit errors
        logger.error(f"Rate limit exceeded for request_id {request_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"error": f"Rate limit exceeded: {str(e)}"}
        )

    except OpenAIAPIConnectionError as e:
        # 503 Service Unavailable for connection errors
        logger.error(f"API connection error for request_id {request_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"error": f"Service unavailable: {str(e)}"}
        )

    except OpenAIServiceError as e:
        # 500 Internal Server Error for other OpenAI service errors
        logger.error(f"OpenAI service error for request_id {request_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Internal server error: {str(e)}"}
        )

    except Exception as e:
        # 500 Internal Server Error for unexpected errors
        logger.error(f"Unexpected error for request_id {request_id}: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "An unexpected internal server error occurred."}
        )

# Styles endpoint
@app.get("/styles")
async def get_styles(auth: dict | None = Depends(require_styles_permission)):
    """Get available styles.
    
    Returns:
        JSON array of available styles
    """
    style_service = get_style_service()
    return get_style_service().get_all_styles()

# Admin endpoints for API key management
@app.post("/admin/api-keys", response_model=CreateAPIKeyResponse)
async def create_api_key(
    request: CreateAPIKeyRequest,
    auth: dict | None = Depends(require_admin_permission)
):
    """Create a new API key.
    
    Args:
        request: API key creation request with name and permissions
        
    Returns:
        Created API key information including the actual key (shown only once)
    """
    try:
        auth_service = get_auth_service()

        # Create and store the API key
        plain_key, api_key_auth = await auth_service.create_and_store_api_key(
            name=request.name,
            permissions=request.permissions
        )

        return CreateAPIKeyResponse(
            key_id=api_key_auth.key_id,
            name=api_key_auth.name,
            api_key=plain_key,
            permissions=api_key_auth.permissions,
            created_at=api_key_auth.created_at
        )

    except Exception as e:
        logger.error(f"Error creating API key: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to create API key: {str(e)}"}
        )

@app.get("/admin/api-keys")
async def list_api_keys(auth: dict | None = Depends(require_admin_permission)):
    """List all API keys (without the actual key values).
    
    Returns:
        List of API key information
    """
    try:
        auth_service = get_auth_service()
        api_keys = await auth_service.list_api_keys()
        return api_keys

    except Exception as e:
        logger.error(f"Error listing API keys: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to list API keys: {str(e)}"}
        )

@app.patch("/admin/api-keys/{key_id}")
async def update_api_key(
    key_id: str,
    request: UpdateAPIKeyRequest,
    auth: dict | None = Depends(require_admin_permission)
):
    """Update an API key's properties.
    
    Args:
        key_id: The ID of the API key to update
        request: Update request with new properties
        
    Returns:
        Success message
    """
    try:
        auth_service = get_auth_service()

        success = await auth_service.update_api_key(
            key_id=key_id,
            is_active=request.is_active,
            permissions=request.permissions
        )

        if success:
            return {"message": f"Successfully updated API key {key_id}"}
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"API key {key_id} not found"}
            )

    except Exception as e:
        logger.error(f"Error updating API key {key_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to update API key: {str(e)}"}
        )

@app.delete("/admin/api-keys/{key_id}")
async def deactivate_api_key(
    key_id: str,
    auth: dict | None = Depends(require_admin_permission)
):
    """Deactivate an API key.
    
    Args:
        key_id: The ID of the API key to deactivate
        
    Returns:
        Success message
    """
    try:
        auth_service = get_auth_service()

        success = await auth_service.deactivate_api_key(key_id)

        if success:
            return {"message": f"Successfully deactivated API key {key_id}"}
        else:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"error": f"API key {key_id} not found"}
            )

    except Exception as e:
        logger.error(f"Error deactivating API key {key_id}: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": f"Failed to deactivate API key: {str(e)}"}
        )

# User registration and authentication endpoints
@app.post("/auth/register", response_model=AuthTokenResponse)
async def register_user(registration: UserRegistrationRequest):
    """Register a new user account.
    
    Args:
        registration: User registration information
        
    Returns:
        JWT access token and user profile
    """
    try:
        user_service = get_user_service()

        success, message, user_profile = await user_service.register_user(registration)

        if not success:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": message}
            )

        # Create access token
        access_token = user_service.create_access_token(
            data={"sub": user_profile.user_id}
        )

        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=user_service.access_token_expire_minutes * 60,
            user=user_profile
        )

    except Exception as e:
        logger.error(f"Error in user registration: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Registration failed"}
        )

@app.post("/auth/login", response_model=AuthTokenResponse)
async def login_user(login: UserLoginRequest):
    """Authenticate user login.
    
    Args:
        login: User login credentials
        
    Returns:
        JWT access token and user profile
    """
    try:
        user_service = get_user_service()

        success, message, user_profile = await user_service.authenticate_user(login)

        if not success:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": message}
            )

        # Create access token
        access_token = user_service.create_access_token(
            data={"sub": user_profile.user_id}
        )

        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=user_service.access_token_expire_minutes * 60,
            user=user_profile
        )

    except Exception as e:
        logger.error(f"Error in user login: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Login failed"}
        )

@app.get("/user/profile")
async def get_user_profile(auth=Depends(require_styles_permission)):
    """Get current user's profile.
    
    Returns:
        User profile information
    """
    try:
        if not auth or auth.get("type") != "user":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "This endpoint requires user authentication"}
            )

        return auth["user"]

    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to get profile"}
        )

@app.get("/user/usage")
async def get_user_usage(auth=Depends(require_styles_permission)):
    """Get current user's usage statistics.
    
    Returns:
        Usage statistics and subscription limits
    """
    try:
        if not auth or auth.get("type") != "user":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "This endpoint requires user authentication"}
            )

        user = auth["user"]
        user_service = get_user_service()

        usage_stats = await user_service.get_user_usage_stats(user.user_id)
        limits = user_service.get_subscription_limits(user.subscription_tier)

        return {
            "usage": usage_stats.model_dump() if usage_stats else None,
            "limits": limits.model_dump(),
            "subscription_tier": user.subscription_tier.value
        }

    except Exception as e:
        logger.error(f"Error getting user usage: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to get usage statistics"}
        )

@app.post("/user/api-keys", response_model=UserAPIKeyResponse)
async def create_user_api_key(
    request: UserAPIKeyRequest,
    auth=Depends(require_styles_permission)
):
    """Create an API key for the current user.
    
    Args:
        request: API key creation request
        
    Returns:
        Created API key information
    """
    try:
        if not auth or auth.get("type") != "user":
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "This endpoint requires user authentication"}
            )

        user = auth["user"]
        user_service = get_user_service()

        success, message, api_key = await user_service.create_user_api_key(
            user.user_id,
            request.name
        )

        if not success:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": message}
            )

        return UserAPIKeyResponse(
            key_id=f"user-{user.user_id}-{secrets.token_hex(4)}",
            name=request.name,
            api_key=api_key,
            created_at=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        logger.error(f"Error creating user API key: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to create API key"}
        )

# Trial and conversion endpoints
@app.get("/trial/status")
async def get_trial_status(request: Request):
    """Get trial status for anonymous users.
    
    Returns:
        Trial usage information and upgrade options
    """
    try:
        trial_service = get_trial_service()
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")

        trial_session = await trial_service.get_or_create_trial_session(client_ip, user_agent)
        _, trial_info = await trial_service.check_trial_usage(trial_session.session_id)

        return {
            "trial_info": trial_info.model_dump(),
            "credit_packages": [pkg.model_dump() for pkg in trial_service.get_credit_packages()]
        }

    except Exception as e:
        logger.error(f"Error getting trial status: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to get trial status"}
        )

@app.post("/trial/convert", response_model=AuthTokenResponse)
async def convert_trial_to_account(conversion: TrialToAccountRequest):
    """Convert trial session to full user account.
    
    Args:
        conversion: Trial conversion request with user registration info
        
    Returns:
        JWT access token and user profile
    """
    try:
        trial_service = get_trial_service()

        success, message, access_token = await trial_service.convert_trial_to_account(conversion)

        if not success:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": message}
            )

        # Get user profile for response
        user_service = get_user_service()
        user_id = user_service.verify_token(access_token).get("sub")
        user_profile = await user_service.get_user_by_id(user_id)

        return AuthTokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=user_service.access_token_expire_minutes * 60,
            user=user_profile
        )

    except Exception as e:
        logger.error(f"Error converting trial to account: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Conversion failed"}
        )

@app.get("/pricing/packages")
async def get_credit_packages():
    """Get available credit packages for purchase.
    
    Returns:
        List of available credit packages
    """
    try:
        trial_service = get_trial_service()
        packages = trial_service.get_credit_packages()

        return {
            "packages": [pkg.model_dump() for pkg in packages],
            "currency": "USD",
            "note": "Credits never expire and can be used for any image generation"
        }

    except Exception as e:
        logger.error(f"Error getting credit packages: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Failed to get pricing packages"}
        )

# The MCP endpoint is now handled by the router included above

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
