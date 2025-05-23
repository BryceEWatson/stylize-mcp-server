"""MCP Server module for the Stylize MCP Server application."""

import logging
import base64
import json
from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
from fastapi import APIRouter
import uuid
from io import BytesIO

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

# Import services lazily to avoid circular imports
def get_services():
    """Get service instances from main module."""
    try:
        from app.main import get_style_service, get_openai_service, get_gcs_service, get_context_analysis_service
        return {
            'style_service': get_style_service(),
            'openai_service': get_openai_service(),
            'gcs_service': get_gcs_service(),
            'context_analysis_service': get_context_analysis_service()
        }
    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        return None

# MCP Tools Implementation

@mcp.tool()
async def stylize_image(
    image_base64: str, 
    style_id: str, 
    user_prompt: Optional[str] = None,
    project_context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Stylize an image with the specified style.
    
    Args:
        image_base64: Base64 encoded image data
        style_id: ID of the style to apply (e.g., 'van_gogh', 'pixel_art')
        user_prompt: Optional custom prompt to guide the stylization
        project_context: Optional context with brand colors, mood, etc.
        
    Returns:
        Dictionary with:
        - stylized_image_url: URL of the stylized image
        - style_applied: The style that was applied
        - prompt_used: The final prompt used for generation
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}
            
        # Validate style_id
        if not services['style_service'].is_valid_style_id(style_id):
            available_styles = services['style_service'].get_available_style_ids()
            return {"error": f"Invalid style_id. Available styles: {available_styles}"}
        
        # Decode image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return {"error": f"Invalid base64 image data: {str(e)}"}
        
        # Get style details
        style = services['style_service'].get_style_by_id(style_id)
        
        # Process project context if provided
        context_summary = ""
        if project_context:
            try:
                from app.models import ProjectContext
                context_obj = ProjectContext(**project_context)
                context_analysis = services['context_analysis_service'].analyze(context_obj)
                context_summary = context_analysis.get("context_summary_string", "")
            except Exception as e:
                logger.warning(f"Failed to process project context: {str(e)}")
        
        # Build final prompt
        prompt_parts = []
        if context_summary:
            prompt_parts.append(context_summary)
        if user_prompt:
            prompt_parts.append(user_prompt)
        prompt_parts.append(style['prompt_fragment'])
        final_prompt = ", ".join(filter(None, prompt_parts))
        
        # Generate stylized image
        stylized_bytes = services['openai_service'].transform_image_with_style(
            image_bytes, 
            final_prompt
        )
        
        # Upload to GCS
        request_id = str(uuid.uuid4())
        blob_name = f"{request_id}/{style_id}.png"
        
        await services['gcs_service'].upload_image(
            services['gcs_service'].variants_bucket_name,
            blob_name,
            stylized_bytes,
            "image/png"
        )
        
        # Generate signed URL
        signed_url = await services['gcs_service'].generate_signed_url(
            services['gcs_service'].variants_bucket_name,
            blob_name
        )
        
        return {
            "stylized_image_url": signed_url,
            "style_applied": style_id,
            "prompt_used": final_prompt
        }
        
    except Exception as e:
        logger.error(f"Error in stylize_image MCP tool: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_styles() -> List[Dict[str, str]]:
    """List all available styles for image transformation.
    
    Returns:
        List of style dictionaries with id, name, and description
    """
    try:
        services = get_services()
        if not services:
            return []
            
        styles = services['style_service'].get_all_styles()
        return [
            {
                "id": style["id"],
                "name": style["name"],
                "description": style["description"]
            }
            for style in styles
        ]
    except Exception as e:
        logger.error(f"Error in list_styles MCP tool: {str(e)}")
        return []

@mcp.tool()
async def get_style_details(style_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific style.
    
    Args:
        style_id: The ID of the style to get details for
        
    Returns:
        Style details including id, name, description, and example prompt
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}
            
        if not services['style_service'].is_valid_style_id(style_id):
            return {"error": f"Style '{style_id}' not found"}
            
        style = services['style_service'].get_style_by_id(style_id)
        return {
            "id": style["id"],
            "name": style["name"],
            "description": style["description"],
            "prompt_fragment": style["prompt_fragment"],
            "example_prompt": f"A beautiful landscape, {style['prompt_fragment']}"
        }
    except Exception as e:
        logger.error(f"Error in get_style_details MCP tool: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def generate_image_from_text(
    prompt: str,
    style_id: str,
    project_context: Optional[Dict[str, Any]] = None
) -> Dict[str, str]:
    """Generate an image from text description with the specified style.
    
    Args:
        prompt: Text description of the image to generate
        style_id: ID of the style to apply
        project_context: Optional context with brand colors, mood, etc.
        
    Returns:
        Dictionary with:
        - generated_image_url: URL of the generated image
        - style_applied: The style that was applied
        - prompt_used: The final prompt used for generation
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}
            
        # Validate style_id
        if not services['style_service'].is_valid_style_id(style_id):
            available_styles = services['style_service'].get_available_style_ids()
            return {"error": f"Invalid style_id. Available styles: {available_styles}"}
        
        # Get style details
        style = services['style_service'].get_style_by_id(style_id)
        
        # Process project context if provided
        context_summary = ""
        if project_context:
            try:
                from app.models import ProjectContext
                context_obj = ProjectContext(**project_context)
                context_analysis = services['context_analysis_service'].analyze(context_obj)
                context_summary = context_analysis.get("context_summary_string", "")
            except Exception as e:
                logger.warning(f"Failed to process project context: {str(e)}")
        
        # Build final prompt
        prompt_parts = []
        if context_summary:
            prompt_parts.append(context_summary)
        prompt_parts.append(prompt)
        prompt_parts.append(style['prompt_fragment'])
        final_prompt = ", ".join(filter(None, prompt_parts))
        
        # Generate image
        generated_bytes = services['openai_service'].generate_image_from_prompt(final_prompt)
        
        # Upload to GCS
        request_id = str(uuid.uuid4())
        blob_name = f"{request_id}/{style_id}_generated.png"
        
        await services['gcs_service'].upload_image(
            services['gcs_service'].variants_bucket_name,
            blob_name,
            generated_bytes,
            "image/png"
        )
        
        # Generate signed URL
        signed_url = await services['gcs_service'].generate_signed_url(
            services['gcs_service'].variants_bucket_name,
            blob_name
        )
        
        return {
            "generated_image_url": signed_url,
            "style_applied": style_id,
            "prompt_used": final_prompt
        }
        
    except Exception as e:
        logger.error(f"Error in generate_image_from_text MCP tool: {str(e)}")
        return {"error": str(e)}

# MCP Resources
@mcp.resource("styles://catalog")
async def styles_catalog() -> str:
    """Provide the complete styles catalog as a resource.
    
    Returns:
        JSON string containing all available styles
    """
    try:
        services = get_services()
        if not services:
            return json.dumps({"error": "Services not available"})
            
        styles = services['style_service'].get_all_styles()
        return json.dumps(styles, indent=2)
    except Exception as e:
        logger.error(f"Error in styles_catalog resource: {str(e)}")
        return json.dumps({"error": str(e)})

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