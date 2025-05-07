"""
This is a minimal version of the main routes with just the blueprint definition.
This helps break circular dependencies in the import structure.
"""

from flask import Blueprint

# Create the blueprint that can be imported by __init__.py
main_bp = Blueprint('main', __name__)

# Import routes after blueprint is defined to avoid circular imports
from app.routes.main import (
    index, upload_files, select_countries, dashboard,
    influencer_detail, influencer_api, history,
    view_historical_analysis, processing, progress_stream,
    check_progress, clear_data, reset_dashboard,
    check_processing_status, debug_logs
) 