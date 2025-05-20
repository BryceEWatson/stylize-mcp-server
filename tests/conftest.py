"""Configure pytest for the stylize-mcp project."""

import os
import sys

# Add the project root directory to the Python path
# This allows tests to import modules from the app directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
