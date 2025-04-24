import os
import datetime
from flask import Flask
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

def create_app():
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static', static_url_path='/static')
    
    # Configure app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-dev-key')
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/uploads')
    app.config['DATA_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/data')
    app.config['IMAGES_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app/static/images')
    
    # Ensure folders exist
    for folder in [app.config['UPLOAD_FOLDER'], app.config['DATA_FOLDER'], app.config['IMAGES_FOLDER']]:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.user import User
        return User.get_by_id(user_id)
    
    # Add template context processors
    @app.context_processor
    def inject_now():
        return {'now': datetime.datetime.now}
    
    # Add custom Jinja filters
    @app.template_filter('min')
    def min_filter(a, b):
        return min(a, b)
    
    # Register blueprints
    from app.routes.main import main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 