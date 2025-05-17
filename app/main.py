"""Main application module for the Stylize MCP Server."""

import logging
from fastapi import FastAPI, UploadFile, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

# Import the MCP server module
import os
import sys
from contextlib import contextmanager

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

with graceful_import():
    from app.mcp_server import get_mcp_router

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

# Include the MCP router
try:
    mcp_router = get_mcp_router()
    app.include_router(mcp_router, tags=["mcp"])
    logger.info("Successfully included MCP router")
except Exception as e:
    log_startup_error(e, "mcp_router_inclusion")
    logger.warning("Failed to include MCP router, continuing without it")
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
        if "mcp_router" in locals():
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
async def stylize_image(image: UploadFile = Form(None), style_id: str = Form(None)):
    """Stylize an uploaded image with the specified style.
    
    Args:
        image: The image file to stylize
        style_id: The ID of the style to apply
        
    Returns:
        JSON with original_id, style, and stylized_image_url
        
    Raises:
        HTTP 400 Bad Request: If validation fails for any reason
    """
    # Input presence validation
    if not image:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Image file is required."}
        )
        
    if not style_id:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Style ID is required."}
        )
    
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
    
    # Log successful validation
    logger.info(f"Received valid stylize_image request with style_id: {style_id}")
    
    # For now, just return a placeholder response
    temp_id = str(uuid.uuid4())
    return {
        "original_id": temp_id,
        "style": style_id,
        "stylized_image_url": f"http://example.com/placeholder_{temp_id}.jpg"
    }

# Stubbed styles endpoint
@app.get("/styles")
async def get_styles():
    """Get available styles.
    
    Returns:
        JSON array of available styles
    """
    # For now, return an empty array
    return []

# The MCP endpoint is now handled by the router included above

# Main entry point
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
