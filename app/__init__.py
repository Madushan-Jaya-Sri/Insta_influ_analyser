# This file marks the directory as a Python package
# It's intentionally left minimal to avoid circular imports

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO

# Initialize SocketIO object
socketio = SocketIO()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object('config.Config')
    
    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Initialize SocketIO with the app
    socketio.init_app(app, 
                     cors_allowed_origins="*",
                     async_mode='gevent',
                     ping_timeout=60,
                     ping_interval=25)
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
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
    
    # Initialize socket event handlers
    with app.app_context():
        from app.socket_handlers import register_socket_handlers
        register_socket_handlers(socketio)
    
    return app
