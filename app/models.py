"""Data models for the Stylize MCP Server."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
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
    
    @validator('reference_logo_image_base64')
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
    
    @validator('brand_colors')
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
