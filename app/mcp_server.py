"""MCP Server module for the Stylize MCP Server application."""

import logging
from fastmcp import FastMCP
from fastapi import APIRouter

# Configure logging for this module
logger = logging.getLogger(__name__)

# Initialize FastMCP server with the server name
try:
    import os
    # Check if Redis-related environment variables are set
    redis_host = os.environ.get('REDIS_HOST')
    redis_port = os.environ.get('REDIS_PORT')
    
    if redis_host and redis_port:
        logger.info(f"Initializing FastMCP with Redis at {redis_host}:{redis_port}")
        mcp = FastMCP("StylizeServer")
    else:
        logger.warning("Redis environment variables not found. Initializing FastMCP with in-memory storage")
        # Pass in-memory configuration to FastMCP or use appropriate fallback mechanism
        mcp = FastMCP("StylizeServer", cache_type="memory")
except Exception as e:
    logger.exception(f"Error initializing FastMCP: {str(e)}")
    # Create a minimal version of FastMCP that won't crash
    mcp = FastMCP("StylizeServer", cache_type="memory")

# Define placeholder MCP tool for image stylization
@mcp.tool()
async def stylize_image_mcp_tool(image_bytes: bytes, style_id: str) -> str:
    """(Placeholder) Stylizes an image with the given style. Returns URL of stylized image.
    
    Args:
        image_bytes: Binary representation of the image to stylize
        style_id: ID of the style to apply
        
    Returns:
        URL pointing to the stylized image
    """
    logger.info(f"MCP tool called: stylize_image_mcp_tool with style_id: {style_id}")
    # This is just a placeholder implementation for now
    return f"Placeholder: Image with style '{style_id}' processed. Output at http://example.com/mcp_placeholder.jpg"

# Create a FastAPI router for the MCP server
def get_mcp_router():
    """Get a FastAPI router for the MCP server.
    
    Returns:
        APIRouter: A FastAPI router that can be included in a FastAPI app
    """
    logger.info("Creating MCP router for FastAPI integration")
    # Create a router from the MCP server
    router = APIRouter()
    
    try:
        # Add the MCP endpoint to the router
        # This creates a Server-Sent Events (SSE) endpoint that clients can connect to
        mcp.add_endpoint_to_router(router, path="/mcp")
        logger.info("Successfully added MCP endpoint to router")
    except Exception as e:
        logger.error(f"Failed to add MCP endpoint to router: {str(e)}")
        # Instead of failing completely, add a minimal health endpoint
        @router.get("/mcp/health")
        async def mcp_health():
            return {"status": "degraded", "message": "MCP router initialized in fallback mode"}
    
    return router
