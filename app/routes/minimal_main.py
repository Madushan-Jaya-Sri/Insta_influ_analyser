"""
This is a minimal version of the main routes with just the blueprint definition.
This helps break circular dependencies in the import structure.
"""

from flask import Blueprint

# Create the blueprint that can be imported by __init__.py
main_bp = Blueprint('main', __name__)

# Import all routes at the bottom to avoid circular imports
# These imports must happen after the blueprint is defined
from app.routes.main import * 