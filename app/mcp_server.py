"""MCP Server module for the Stylize MCP Server application."""

import base64
import json
import logging
import uuid
from typing import Any

from fastapi import HTTPException, status
from fastmcp import FastMCP

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
        from app.main import (
            get_auth_service,
            get_context_analysis_service,
            get_gcs_service,
            get_openai_service,
            get_style_service,
        )
        return {
            'style_service': get_style_service(),
            'openai_service': get_openai_service(),
            'gcs_service': get_gcs_service(),
            'context_analysis_service': get_context_analysis_service(),
            'auth_service': get_auth_service()
        }
    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        return None

async def authenticate_mcp_request(request_data: dict[str, Any]) -> dict | None:
    """Authenticate MCP requests using API key from request metadata."""
    services = get_services()
    if not services or not services['auth_service']:
        logger.warning("Auth service not available for MCP authentication")
        return None

    auth_service = services['auth_service']

    # Check if auth is disabled or in bypass mode
    if not auth_service.is_auth_enabled() or auth_service.should_bypass_auth():
        logger.debug("MCP authentication bypassed")
        return None

    # Extract API key from request metadata or headers
    # MCP tools can include metadata in their calls
    api_key = None

    # Try to get API key from various sources in the request
    if isinstance(request_data, dict):
        # Check for api_key in the request metadata
        api_key = request_data.get('api_key') or request_data.get('auth_token')

        # Check nested metadata structures
        if 'metadata' in request_data and isinstance(request_data['metadata'], dict):
            api_key = api_key or request_data['metadata'].get('api_key') or request_data['metadata'].get('auth_token')

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="MCP request missing API key in request data or metadata"
        )

    # Validate the API key
    from app.models import APIPermission
    api_key_auth = await auth_service.validate_api_key(api_key)
    if not api_key_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key for MCP request"
        )

    # Check MCP permission
    if not auth_service.check_permission(api_key_auth, APIPermission.MCP):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for MCP access"
        )

    logger.debug(f"Authenticated MCP request with key: {api_key_auth.key_id}")
    return api_key_auth

# MCP Tools Implementation

@mcp.tool()
async def stylize_image(
    image_base64: str,
    style_id: str | None = None,
    user_prompt: str | None = None,
    project_context: dict[str, Any] | None = None,
    api_key: str | None = None,
    session_id: str | None = None
) -> dict[str, str]:
    """Stylize an image with the specified style or generate 4 random styles.
    
    Args:
        image_base64: Base64 encoded image data
        style_id: ID of the style to apply (e.g., 'van_gogh', 'pixel_art'). If not provided, generates 4 random styles.
        user_prompt: Optional custom prompt to guide the stylization
        project_context: Optional context with brand colors, mood, etc.
        api_key: API key for authentication (if provided, skips trial)
        session_id: Trial session ID for anonymous usage (if no api_key)
        
    Returns:
        Dictionary with:
        For single style (when style_id provided):
        - stylized_image_url: URL of the stylized image
        - style_applied: The style that was applied
        - prompt_used: The final prompt used for generation
        
        For multiple styles (when style_id not provided):
        - multiple_styles: True
        - images: Array of objects with style_id, style_name, stylized_image_url, prompt_used
        - total_images: Number of images generated
        
        For all modes:
        - trial_info: Trial usage information (for anonymous users)
        - upgrade_options: Available packages (if trial expired)
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}

        # Determine if we're generating multiple styles
        multiple_styles_mode = style_id is None
        selected_styles = []

        if multiple_styles_mode:
            # Select 4 random styles
            import random
            all_styles = services['style_service'].get_all_styles()
            selected_styles = random.sample(all_styles, min(4, len(all_styles)))
            logger.info(f"No style_id provided to MCP, generating with 4 random styles: {[s['id'] for s in selected_styles]}")
        else:
            # Validate the provided style_id
            if not services['style_service'].is_valid_style_id(style_id):
                available_styles = services['style_service'].get_available_style_ids()
                return {"error": f"Invalid style_id. Available styles: {available_styles}"}
            selected_styles = [services['style_service'].get_style_by_id(style_id)]

        # Calculate usage multiplier
        usage_multiplier = len(selected_styles)

        # Check authentication: API key takes precedence over trial
        if api_key:
            # Authenticate with API key
            await authenticate_mcp_request({"api_key": api_key})
            auth_type = "api_key"
            trial_session = None
        elif session_id:
            # Use trial session
            auth_type = "trial"
            # Get or create trial session (we'll need IP, but MCP doesn't provide it)
            # For MCP, we'll trust the provided session_id
            if not services.get('trial_service'):
                from app.main import get_trial_service
                services['trial_service'] = get_trial_service()

            trial_service = services['trial_service']

            # Check trial usage (accounting for multiple images)
            can_use, trial_info = await trial_service.check_trial_usage(session_id, usage_multiplier)
            if not can_use:
                # Return trial expired response with upgrade options
                upgrade_options = trial_service.get_credit_packages()
                return {
                    "success": False,
                    "error": trial_info.upgrade_message,
                    "trial_info": trial_info.dict(),
                    "upgrade_options": [pkg.dict() for pkg in upgrade_options],
                    "signup_url": trial_info.signup_url
                }
            trial_session = session_id
        else:
            return {"error": "Either api_key or session_id is required for MCP access"}

        # Decode image
        try:
            image_bytes = base64.b64decode(image_base64)
        except Exception as e:
            return {"error": f"Invalid base64 image data: {str(e)}"}

        # Process project context if provided (reused for all styles)
        context_summary = ""
        if project_context:
            try:
                from app.models import ProjectContext
                context_obj = ProjectContext(**project_context)
                context_analysis = services['context_analysis_service'].analyze(context_obj)
                context_summary = context_analysis.get("context_summary_string", "")
            except Exception as e:
                logger.warning(f"Failed to process project context: {str(e)}")

        def build_final_prompt(style: dict[str, str]) -> str:
            """Helper function to build final prompt for a given style."""
            prompt_parts = []
            if context_summary:
                prompt_parts.append(context_summary)
            if user_prompt:
                prompt_parts.append(user_prompt)
            prompt_parts.append(style['prompt_fragment'])
            return ", ".join(filter(None, prompt_parts))

        # Generate images for all selected styles
        request_id = str(uuid.uuid4())
        generated_images = []

        for style in selected_styles:
            style_id_current = style['id']
            final_prompt = build_final_prompt(style)

            # Generate stylized image
            stylized_bytes = services['openai_service'].transform_image_with_style(
                image_bytes,
                final_prompt
            )

            # Upload to GCS
            blob_name = f"{request_id}/{style_id_current}.png"

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

            # Add to results
            generated_images.append({
                "style_id": style_id_current,
                "style_name": style['name'],
                "stylized_image_url": signed_url,
                "prompt_used": final_prompt
            })

        # Increment usage based on auth type (for all generated images)
        if auth_type == "trial":
            trial_service = services['trial_service']
            await trial_service.increment_trial_usage(trial_session, usage_multiplier)

            # Get updated trial info
            _, updated_trial_info = await trial_service.check_trial_usage(trial_session)

            if multiple_styles_mode:
                response = {
                    "success": True,
                    "multiple_styles": True,
                    "images": generated_images,
                    "total_images": len(generated_images),
                    "trial_info": {
                        "images_used": updated_trial_info.images_used,
                        "images_remaining": updated_trial_info.images_remaining,
                        "signup_message": f"You have {updated_trial_info.images_remaining} free images remaining!"
                    }
                }
            else:
                response = {
                    "success": True,
                    "stylized_image_url": generated_images[0]["stylized_image_url"],
                    "style_applied": generated_images[0]["style_id"],
                    "prompt_used": generated_images[0]["prompt_used"],
                    "trial_info": {
                        "images_used": updated_trial_info.images_used,
                        "images_remaining": updated_trial_info.images_remaining,
                        "signup_message": f"You have {updated_trial_info.images_remaining} free images remaining!"
                    }
                }

            # Include upgrade options if getting close to limit
            if updated_trial_info.images_remaining <= 1:
                response["upgrade_options"] = [pkg.dict() for pkg in trial_service.get_credit_packages()]
                response["signup_url"] = "/auth/register"

            return response
        else:
            # Regular authenticated user
            if multiple_styles_mode:
                return {
                    "success": True,
                    "multiple_styles": True,
                    "images": generated_images,
                    "total_images": len(generated_images)
                }
            else:
                return {
                    "success": True,
                    "stylized_image_url": generated_images[0]["stylized_image_url"],
                    "style_applied": generated_images[0]["style_id"],
                    "prompt_used": generated_images[0]["prompt_used"]
                }

    except Exception as e:
        logger.error(f"Error in stylize_image MCP tool: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_styles(api_key: str | None = None) -> list[dict[str, str]]:
    """List all available styles for image transformation.
    
    Args:
        api_key: API key for authentication
    
    Returns:
        List of style dictionaries with id, name, and description
    """
    try:
        # Authenticate the request
        await authenticate_mcp_request({"api_key": api_key})

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
async def get_style_details(style_id: str, api_key: str | None = None) -> dict[str, Any]:
    """Get detailed information about a specific style.
    
    Args:
        style_id: The ID of the style to get details for
        api_key: API key for authentication
        
    Returns:
        Style details including id, name, description, and example prompt
    """
    try:
        # Authenticate the request
        await authenticate_mcp_request({"api_key": api_key})

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
    style_id: str | None = None,
    project_context: dict[str, Any] | None = None,
    api_key: str | None = None
) -> dict[str, str]:
    """Generate an image from text description with the specified style or 4 random styles.
    
    Args:
        prompt: Text description of the image to generate
        style_id: ID of the style to apply. If not provided, generates 4 random styles.
        project_context: Optional context with brand colors, mood, etc.
        api_key: API key for authentication
        
    Returns:
        Dictionary with:
        For single style (when style_id provided):
        - generated_image_url: URL of the generated image
        - style_applied: The style that was applied
        - prompt_used: The final prompt used for generation
        
        For multiple styles (when style_id not provided):
        - multiple_styles: True
        - images: Array of objects with style_id, style_name, generated_image_url, prompt_used
        - total_images: Number of images generated
    """
    try:
        # Authenticate the request
        await authenticate_mcp_request({"api_key": api_key})

        services = get_services()
        if not services:
            return {"error": "Services not available"}

        # Determine if we're generating multiple styles
        multiple_styles_mode = style_id is None
        selected_styles = []

        if multiple_styles_mode:
            # Select 4 random styles
            import random
            all_styles = services['style_service'].get_all_styles()
            selected_styles = random.sample(all_styles, min(4, len(all_styles)))
            logger.info(f"No style_id provided to MCP text generation, generating with 4 random styles: {[s['id'] for s in selected_styles]}")
        else:
            # Validate the provided style_id
            if not services['style_service'].is_valid_style_id(style_id):
                available_styles = services['style_service'].get_available_style_ids()
                return {"error": f"Invalid style_id. Available styles: {available_styles}"}
            selected_styles = [services['style_service'].get_style_by_id(style_id)]

        # Process project context if provided (reused for all styles)
        context_summary = ""
        if project_context:
            try:
                from app.models import ProjectContext
                context_obj = ProjectContext(**project_context)
                context_analysis = services['context_analysis_service'].analyze(context_obj)
                context_summary = context_analysis.get("context_summary_string", "")
            except Exception as e:
                logger.warning(f"Failed to process project context: {str(e)}")

        def build_final_prompt(style: dict[str, str]) -> str:
            """Helper function to build final prompt for a given style."""
            prompt_parts = []
            if context_summary:
                prompt_parts.append(context_summary)
            prompt_parts.append(prompt)
            prompt_parts.append(style['prompt_fragment'])
            return ", ".join(filter(None, prompt_parts))

        # Generate images for all selected styles
        request_id = str(uuid.uuid4())
        generated_images = []

        for style in selected_styles:
            style_id_current = style['id']
            final_prompt = build_final_prompt(style)

            # Generate image
            generated_bytes = services['openai_service'].generate_image_from_prompt(final_prompt)

            # Upload to GCS
            blob_name = f"{request_id}/{style_id_current}_generated.png"

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

            # Add to results
            generated_images.append({
                "style_id": style_id_current,
                "style_name": style['name'],
                "generated_image_url": signed_url,
                "prompt_used": final_prompt
            })

        # Build response based on single vs multiple styles
        if multiple_styles_mode:
            return {
                "success": True,
                "multiple_styles": True,
                "images": generated_images,
                "total_images": len(generated_images)
            }
        else:
            # Single style mode - maintain backward compatibility
            return {
                "generated_image_url": generated_images[0]["generated_image_url"],
                "style_applied": generated_images[0]["style_id"],
                "prompt_used": generated_images[0]["prompt_used"]
            }

    except Exception as e:
        logger.error(f"Error in generate_image_from_text MCP tool: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def start_trial_session() -> dict[str, Any]:
    """Start a new trial session for anonymous users.
    
    Returns:
        Dictionary with:
        - session_id: Trial session identifier
        - images_remaining: Number of free images available
        - upgrade_options: Available credit packages
        - instructions: How to use the trial
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}

        if not services.get('trial_service'):
            from app.main import get_trial_service
            services['trial_service'] = get_trial_service()

        trial_service = services['trial_service']

        # Create trial session with generic IP (MCP doesn't provide real IP)
        trial_session = await trial_service.get_or_create_trial_session("mcp-client", "MCP-Client")

        return {
            "session_id": trial_session.session_id,
            "images_remaining": trial_session.max_images,
            "trial_duration_hours": 24,
            "upgrade_options": [pkg.dict() for pkg in trial_service.get_credit_packages()],
            "instructions": [
                f"You can generate {trial_session.max_images} free images using this session_id",
                "Use the session_id parameter in stylize_image or generate_image_from_text",
                "When you reach the limit, you can sign up for 100 free images per month!",
                "Visit /auth/register to create your account"
            ]
        }

    except Exception as e:
        logger.error(f"Error in start_trial_session MCP tool: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def check_trial_status(session_id: str) -> dict[str, Any]:
    """Check the status of a trial session.
    
    Args:
        session_id: Trial session identifier
        
    Returns:
        Dictionary with trial usage information and upgrade options
    """
    try:
        services = get_services()
        if not services:
            return {"error": "Services not available"}

        if not services.get('trial_service'):
            from app.main import get_trial_service
            services['trial_service'] = get_trial_service()

        trial_service = services['trial_service']

        # Check trial usage
        can_use, trial_info = await trial_service.check_trial_usage(session_id)

        response = {
            "session_id": session_id,
            "trial_info": trial_info.dict(),
            "can_generate": can_use
        }

        if not can_use:
            response["upgrade_options"] = [pkg.dict() for pkg in trial_service.get_credit_packages()]
            response["message"] = "Trial expired! Sign up for 100 free images per month or purchase credits."

        return response

    except Exception as e:
        logger.error(f"Error in check_trial_status MCP tool: {str(e)}")
        return {"error": str(e)}

# MCP Resources - Note: FastMCP may require URI templates with parameters
# For now, we'll comment this out and provide styles via the list_styles tool instead
# @mcp.resource("styles://catalog")
async def styles_catalog(api_key: str | None = None) -> str:
    """Provide the complete styles catalog as a resource.
    
    Args:
        api_key: API key for authentication
    
    Returns:
        JSON string containing all available styles
    """
    try:
        # Authenticate the request
        await authenticate_mcp_request({"api_key": api_key})

        services = get_services()
        if not services:
            return json.dumps({"error": "Services not available"})

        styles = services['style_service'].get_all_styles()
        return json.dumps(styles, indent=2)
    except Exception as e:
        logger.error(f"Error in styles_catalog resource: {str(e)}")
        return json.dumps({"error": str(e)})

# Note: The MCP server is now mounted directly in main.py using mcp.http_app()
# This provides the full MCP protocol endpoints at /mcp
