import os
import datetime
from flask import Flask, session, request
from flask_login import LoginManager
from flask_session import Session  # Add this import
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Initialize extensions globally but without app context initially
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

def create_app():
    # Define base directory for better path management
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'),
                static_url_path='/static')
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-please-change') # Use a more descriptive default
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', f'sqlite:///{os.path.join(base_dir, "app.db")}')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'app', 'data', 'sessions')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'app', 'uploads')
    app.config['DATA_FOLDER'] = os.path.join(base_dir, 'app', 'data')
    app.config['IMAGES_FOLDER'] = os.path.join(base_dir, 'app', 'static', 'images')
    app.config['LOG_SESSIONS'] = os.getenv('LOG_SESSIONS', 'false').lower() == 'true'
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    Session(app)
    
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
        return {'now': datetime.datetime.now}
    
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
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # Create database tables if they don't exist (for simple setup without full migrations initially)
    # Consider using Flask-Migrate commands for production/better management
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='127.0.0.1', port=8001)