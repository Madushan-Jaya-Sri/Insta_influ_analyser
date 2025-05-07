"""
This is a minimal version of the main routes with just the blueprint definition.
This helps break circular dependencies in the import structure.
"""

from app.routes.main import main_bp

# Export the blueprint for use in __init__.py
__all__ = ['main_bp'] 