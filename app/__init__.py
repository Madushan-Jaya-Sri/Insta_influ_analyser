# This file marks the directory as a Python package
# It's intentionally left minimal to avoid circular imports

import os
from datetime import datetime, timedelta
import logging
from logging.handlers import RotatingFileHandler
import traceback
from flask import Flask, session, request, jsonify
from flask_login import LoginManager
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Initialize extensions globally but without app context initially
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

def create_app():
    # Define base directory for better path management
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'),
                static_url_path='/static')
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-please-change')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(base_dir, "app.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'app', 'data', 'sessions')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'app', 'uploads')
    app.config['DATA_FOLDER'] = os.path.join(base_dir, 'app', 'data')
    app.config['IMAGES_FOLDER'] = os.path.join(base_dir, 'app', 'static', 'images')
    app.config['LOG_SESSIONS'] = os.getenv('LOG_SESSIONS', 'false').lower() == 'true'
    
    # Setup logging for production environment
    if not app.debug and not app.testing:
        # Ensure log directory exists
        log_dir = os.path.join(base_dir, 'logs')
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except FileExistsError:
            # Directory already exists, which is fine
            pass
        
        # Create a rotating file handler
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'app.log'),
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Instagram Influencer Analyzer startup')
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    Session(app)
    
    # Error handler for production 500 errors
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}\n{traceback.format_exc()}')
        return jsonify(error="Internal server error. This has been logged and will be addressed."), 500
    
    # Error handler for production 502 errors (proxy errors)
    @app.errorhandler(502)
    def bad_gateway(error):
        app.logger.error(f'Bad Gateway Error: {error}')
        return jsonify(error="Bad gateway error. Please check your server configuration."), 502
    
    # Ensure folders exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DATA_FOLDER'], app.config['IMAGES_FOLDER'], app.config['SESSION_FILE_DIR']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return db.session.get(User, int(user_id))
    
    # Add template context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.now}
    
    # Add custom Jinja filters
    @app.template_filter('min')
    def min_filter(a, b):
        return min(a, b)
    
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

    # Debugging: Log session data only if explicitly enabled
    @app.before_request
    def log_session():
        if app.config['LOG_SESSIONS']:
            app.logger.debug("Session: %s, Cookies: %s", session, request.cookies)
    
    # Register blueprints - move the imports inside the function to avoid circular imports
    def register_blueprints(app):
        # Import blueprints
        from app.routes.main import main_bp
        from app.routes.auth import auth_bp
        
        # Register blueprints
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Call the blueprint registration function
    register_blueprints(app)
    
    # Create database tables if they don't exist (for simple setup without full migrations initially)
    # Consider using Flask-Migrate commands for production/better management
    with app.app_context():
        db.create_all()
    
    return app
