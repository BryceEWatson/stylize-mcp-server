"""Main application module for the Stylize MCP Server."""

import logging
import json
import base64
from typing import Optional, Dict, Any
from fastapi import FastAPI, UploadFile, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid
import requests

# Import the MCP server module
import os
import sys
from contextlib import contextmanager
from app.styles_service import StyleService
from app.models import ProjectContext
from app.context_analysis_service import ContextAnalysisService
from app.openai_service import (
    OpenAIService, 
    OpenAIServiceError, 
    OpenAIAPIConnectionError, 
    OpenAIRateLimitError, 
    OpenAIContentPolicyViolationError,
    OpenAIInvalidRequestError
)
from app.gcs_service import (
    GcsService,
    GcsServiceError,
    GcsBucketNotFoundError,
    GcsUploadError,
    GcsSignedUrlError
)

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

# Initialize FastAPI app
app = FastAPI(
    title="Stylize MCP Server",
    description="API for stylizing images using generative AI",
    version="0.1.0",
)

# Service instances (initialized lazily via getters)
_style_service = None
_context_analysis_service = None
_openai_service = None
_gcs_service = None

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

# Include the MCP server
try:
    from app.mcp_server import mcp
    # Mount the MCP server as a sub-application
    mcp_app = mcp.http_app()
    app.mount("/mcp", mcp_app)
    logger.info("Successfully mounted MCP server at /mcp")
except Exception as e:
    log_startup_error(e, "mcp_server_mounting")
    logger.warning("Failed to mount MCP server, continuing without it")
    # Don't re-raise - allow app to start without MCP functionality

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
        # Check if MCP is mounted by looking for it in the app's routes
        mcp_mounted = any(route.path.startswith("/mcp") for route in app.routes)
        if mcp_mounted:
            services["mcp"] = "ok"
        else:
            services["mcp"] = "unavailable"
    except Exception:
        services["mcp"] = "error"
        
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

# Stylize image endpoint
@app.post("/stylize_image")
async def stylize_image(
    image: UploadFile = Form(None), 
    style_id: str = Form(None), 
    user_prompt: str = Form(None),
    project_context_str: Optional[str] = Form(None)
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
        
    if not style_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Style ID is required."}
        )
    
    # Style ID validation
    style_service = get_style_service()
    if not style_service.is_valid_style_id(style_id):
        available_styles = style_service.get_available_style_ids()
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": f"Invalid style_id. Available styles are: {available_styles}"}
        )
    
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
            logger.info(f"Successfully parsed project_context JSON")
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
                logger.info(f"Successfully validated project_context against schema")
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
            logger.info(f"Successfully analyzed project context")
        except Exception as e:
            logger.error(f"Error analyzing project context: {str(e)}")
            # We'll continue with the request even if analysis fails,
            # Just without the context enhancement
    
    # Log successful validation
    logger.info(f"Received valid stylize_image request with style_id: {style_id}")
    
    # Get the selected style
    style_service = get_style_service()
    style = style_service.get_style_by_id(style_id)
    
    # Construct final prompt using context-aware prompt generation
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
    
    # Construct the final prompt combining all elements
    if context_summary:
        if user_prompt and user_prompt.strip():
            final_prompt = f"{context_summary}, {user_prompt.strip()}{brand_colors_text}, {style['prompt_fragment']}{avoid_elements_text}"
        else:
            final_prompt = f"{context_summary}{brand_colors_text}, {style['prompt_fragment']}{avoid_elements_text}"
    else:
        if user_prompt and user_prompt.strip():
            final_prompt = f"{user_prompt.strip()}, {style['prompt_fragment']}"
        else:
            final_prompt = style['prompt_fragment']
    
    # Log the final prompt and context information for debugging
    request_id = str(uuid.uuid4())
    logger.info(f"Generated final prompt for request_id {request_id}: {final_prompt}")
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
        
        # Construct the variant blob name
        variant_blob_name = f"{request_id}/{style_id}.png"  # Assuming PNG output from DALL-E 3
        
        # Call OpenAI to generate the image
        # Determine the generation approach based on available inputs
        openai_service = get_openai_service()
        
        if original_image_bytes:
            # We have an input image to transform
            logger.info(f"Transforming input image with style for request_id {request_id}")
            stylized_image_bytes = openai_service.transform_image_with_style(original_image_bytes, final_prompt)
        elif decoded_reference_logo_bytes:
            # We have a reference logo but no input image
            logger.info(f"Starting two-step process: GPT-4V analysis + DALL-E 3 generation with reference logo for request_id {request_id}")
            stylized_image_bytes = openai_service.generate_image_from_prompt_and_reference(final_prompt, decoded_reference_logo_bytes)
        else:
            # Text-only generation
            logger.info(f"Generating image from prompt for request_id {request_id}")
            stylized_image_bytes = openai_service.generate_image_from_prompt(final_prompt)
            
        # Log successful image generation
        logger.info(f"Successfully generated image data for request_id {request_id}, size: {len(stylized_image_bytes)} bytes")
        
        # Upload the stylized image to GCS
        logger.info(f"Uploading stylized image to GCS for request_id {request_id}")
        # We've already got the gcs_service instance above
        await gcs_service.upload_image(
            gcs_service.variants_bucket_name,
            variant_blob_name,
            stylized_image_bytes,
            "image/png"  # DALL-E 3 outputs PNG format
        )
        logger.info(f"Stylized image uploaded to GCS for request_id {request_id}")
        
        # Generate a signed URL for the stylized image
        logger.info(f"Generating signed URL for stylized image for request_id {request_id}")
        # We've already got the gcs_service instance above
        stylized_image_url = await gcs_service.generate_signed_url(
            gcs_service.variants_bucket_name,
            variant_blob_name
        )
        logger.info(f"Generated signed URL for stylized image for request_id {request_id}: {stylized_image_url}")
        
        # Return the response with the signed URL
        return {
            "original_id": request_id,
            "style": style_id,
            "stylized_image_url": stylized_image_url
        }
        
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
async def get_styles():
    """Get available styles.
    
    Returns:
        JSON array of available styles
    """
    style_service = get_style_service()
    return get_style_service().get_all_styles()

# The MCP endpoint is now handled by the router included above

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
