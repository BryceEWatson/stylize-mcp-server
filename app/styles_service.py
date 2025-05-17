"""Service module for handling style catalog operations."""

import json
import logging
import os
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class StyleService:
    """Service for managing the style catalog."""
    
    def __init__(self, styles_file_path: str = None):
        """Initialize the StyleService.
        
        Args:
            styles_file_path: Path to the styles.json file. If None, uses the default path.
        """
        self.styles_file_path = styles_file_path or os.path.join(os.path.dirname(__file__), 'styles.json')
        self.styles = []
        self.styles_by_id = {}
        self._load_styles()
    
    def _load_styles(self) -> None:
        """Load styles from the styles.json file.
        
        Raises:
            FileNotFoundError: If the styles file doesn't exist.
            json.JSONDecodeError: If the styles file contains invalid JSON.
        """
        try:
            with open(self.styles_file_path, 'r') as f:
                self.styles = json.load(f)
                
            # Build a lookup dictionary for styles by ID for efficient validation
            self.styles_by_id = {style['id']: style for style in self.styles}
            logger.info(f"Loaded {len(self.styles)} styles from {self.styles_file_path}")
            
        except FileNotFoundError:
            logger.error(f"Styles file not found: {self.styles_file_path}")
            # Re-raise to indicate a critical startup issue
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in styles file: {e}")
            # Re-raise to indicate a critical startup issue
            raise
    
    def get_all_styles(self) -> List[Dict]:
        """Get all available styles.
        
        Returns:
            List of style objects.
        """
        return self.styles
    
    def is_valid_style_id(self, style_id: str) -> bool:
        """Check if a style ID exists in the catalog.
        
        Args:
            style_id: The style ID to validate.
            
        Returns:
            True if the style ID exists, False otherwise.
        """
        return style_id in self.styles_by_id
    
    def get_available_style_ids(self) -> List[str]:
        """Get a list of all available style IDs.
        
        Returns:
            List of style IDs.
        """
        return list(self.styles_by_id.keys())
        
    def get_style_by_id(self, style_id: str) -> Optional[Dict]:
        """Get a style by its ID.
        
        Args:
            style_id: The style ID to retrieve.
            
        Returns:
            The style dictionary if the style ID exists, None otherwise.
        """
        return self.styles_by_id.get(style_id)
