"""Service for analyzing project context and extracting information for prompt generation."""

import base64
import logging
from typing import Any

from app.models import ProjectContext

logger = logging.getLogger(__name__)


class ContextAnalysisService:
    """Service for analyzing project context to enhance prompt generation."""

    def analyze(self, context: ProjectContext) -> dict[str, Any]:
        """Analyze the project context and extract information for prompt generation.
        
        Args:
            context: A validated ProjectContext Pydantic object.
            
        Returns:
            A dictionary containing:
            - context_summary_string: A textual summary of the context
            - brand_colors_list: List of brand colors
            - decoded_reference_logo_bytes: Decoded logo image bytes (or None)
            - avoid_elements_list: List of elements to avoid
        """
        logger.info("Analyzing project context")

        # Generate context summary string
        context_summary_string = self._generate_context_summary(context)

        # Extract brand colors
        brand_colors_list = context.brand_colors if context.brand_colors else []

        # Extract and decode reference logo if present
        decoded_reference_logo_bytes = None
        if context.reference_logo_image_base64:
            try:
                decoded_reference_logo_bytes = base64.b64decode(context.reference_logo_image_base64)
                logger.info("Successfully decoded reference logo image")
            except Exception as e:
                # This should not happen as the model validator would have caught it,
                # but we're being defensive here
                logger.error(f"Error decoding reference logo: {str(e)}")

        # Extract elements to avoid
        avoid_elements_list = context.avoid_elements if context.avoid_elements else []

        # Log the results
        logger.info(f"Context summary: {context_summary_string}")
        logger.info(f"Brand colors: {brand_colors_list}")
        logger.info(f"Avoid elements: {avoid_elements_list}")
        logger.info(f"Reference logo provided: {decoded_reference_logo_bytes is not None}")

        return {
            "context_summary_string": context_summary_string,
            "brand_colors_list": brand_colors_list,
            "decoded_reference_logo_bytes": decoded_reference_logo_bytes,
            "avoid_elements_list": avoid_elements_list
        }

    def _generate_context_summary(self, context: ProjectContext) -> str:
        """Generate a descriptive summary string from the project context.
        
        This concatenates relevant text fields into a readable description that can
        be incorporated into the prompt.
        
        Args:
            context: The ProjectContext object
            
        Returns:
            A concatenated string summarizing the context
        """
        summary_parts = []

        # Add project name if available
        if context.project_name:
            summary_parts.append(context.project_name)

        # Add project description if available
        if context.project_description:
            summary_parts.append(context.project_description)

        # Add target audience if available
        if context.target_audience:
            summary_parts.append(f"for {context.target_audience}")

        # Add keywords if available
        if context.keywords and len(context.keywords) > 0:
            keywords_str = ", ".join(context.keywords)
            summary_parts.append(f"with elements of {keywords_str}")

        # Add desired elements if available
        if context.desired_elements and len(context.desired_elements) > 0:
            elements_str = ", ".join(context.desired_elements)
            summary_parts.append(f"including {elements_str}")

        # Add artistic mood if available
        if context.artistic_mood:
            summary_parts.append(f"in a {context.artistic_mood} style")

        # Combine all parts with commas or return an empty string if no context provided
        if not summary_parts:
            return ""

        return ", ".join(summary_parts)
