import os
import datetime
from flask import Flask, session, request
from flask_login import LoginManager
from flask_session import Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def create_app():
    # Define base directory for better path management
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'),
                static_url_path='/static')
    
    # Configure app
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = os.path.join(base_dir, 'app', 'data', 'sessions')
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_PATH'] = '/'  # Ensure cookie is valid for all routes
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'app', 'uploads')
    app.config['DATA_FOLDER'] = os.path.join(base_dir, 'app', 'data')
    app.config['IMAGES_FOLDER'] = os.path.join(base_dir, 'app', 'static', 'images')
    
    # Configure SQLAlchemy
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(base_dir, 'app', 'data', 'insta_analyser.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize flask-session
    Session(app)
    
    # Ensure folders exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DATA_FOLDER'], app.config['IMAGES_FOLDER'], app.config['SESSION_FILE_DIR']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Initialize Database
    from app.models.database import init_db
    init_db(app)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.database import User
        return User.query.get(int(user_id))
    
    # Add template context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now}
    
    # Add custom Jinja filters
    @app.template_filter('min')
    def min_filter(a, b):
        return min(a, b)
    
    # Debugging: Log session data only in development
    if os.getenv('FLASK_ENV') == 'development':
        @app.before_request
        def log_session():
            app.logger.debug("Session: %s, Cookies: %s", session, request.cookies)
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    return app

# Production WSGI application
application = create_app()

if __name__ == '__main__':
    # Default to development mode for local running
    debug_mode = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # Use host 0.0.0.0 to make the server accessible from outside the container
    port = int(os.getenv('PORT', 8000))
    
    application.run(
        debug=debug_mode, 
        host='0.0.0.0', 
        port=port
    ) 