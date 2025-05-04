# This file marks the directory as a Python package
# It's intentionally left minimal to avoid circular imports

from flask import Flask
from flask_login import LoginManager

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    # Register context processors
    from app.routes.main import inject_processing_status
    app.context_processor(inject_processing_status)
    
    # Register template filters
    @app.template_filter('format_number')
    def format_number(value):
        """Format large numbers for display (e.g., 1000 -> 1K, 1000000 -> 1M)"""
        if value is None:
            return "0"
        
        try:
            value = int(value)
        except (TypeError, ValueError):
            return str(value)
            
        if value < 1000:
            return str(value)
        elif value < 1000000:
            return f"{value/1000:.1f}K".replace('.0K', 'K')
        else:
            return f"{value/1000000:.1f}M".replace('.0M', 'M')
    
    return app
