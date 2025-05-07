"""Main application module for the Stylize MCP Server."""

import logging
from fastapi import FastAPI, UploadFile, Form, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

# Import the MCP server module
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
app.include_router(get_mcp_router(), tags=["mcp"])

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
    return {"status": "ok"}

# Stubbed stylize_image endpoint
@app.post("/stylize_image")
async def stylize_image(image: UploadFile = Form(...), style_id: str = Form(...)):
    """Stylize an uploaded image with the specified style.
    
    Args:
        image: The image file to stylize
        style_id: The ID of the style to apply
        
    Returns:
        JSON with original_id, style, and stylized_image_url
    """
    logger.info(f"Received stylize_image request with style_id: {style_id}")
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
