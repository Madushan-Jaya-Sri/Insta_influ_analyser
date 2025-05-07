#!/bin/bash
# Emergency deployment fix script - run this inside the Docker container to fix circular imports
set -e

echo "===== RUNNING EMERGENCY DEPLOYMENT FIXES ====="

# 1. Create database.py if it doesn't exist
if [ ! -f /app/app/database.py ]; then
    echo "Creating centralized database.py module..."
    mkdir -p /app/app
    cat > /app/app/database.py << 'EOF'
"""
Database initialization module to prevent circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create all tables
    with app.app_context():
        db.create_all()
EOF
    echo "✓ Created database.py"
else
    echo "✓ database.py already exists"
fi

# 2. Fix auth.py circular imports
if [ -f /app/app/routes/auth.py ]; then
    echo "Checking auth.py for circular imports..."
    
    # Create backup
    cp -f /app/app/routes/auth.py /app/app/routes/auth.py.bak
    echo "  Created backup at /app/app/routes/auth.py.bak"
    
    # Fix the import
    if grep -q "from run import db" /app/app/routes/auth.py; then
        sed -i 's/from run import db/from app.database import db/g' /app/app/routes/auth.py
        echo "✓ Fixed circular import in auth.py"
    elif grep -q "from app import db" /app/app/routes/auth.py; then
        sed -i 's/from app import db/from app.database import db/g' /app/app/routes/auth.py
        echo "✓ Updated db import in auth.py to use centralized location"
    else
        echo "  auth.py does not have problematic imports"
    fi
else
    echo "⚠ auth.py not found, cannot fix"
fi

# 3. Fix all model files to use centralized database
echo "Fixing model imports in all files..."
find /app/app/models -type f -name "*.py" | while read file; do
    echo "Checking $file..."
    if grep -q "from app import db" "$file"; then
        sed -i 's/from app import db/from app.database import db/g' "$file"
        echo "✓ Fixed import in $file"
    elif grep -q "from run import db" "$file"; then
        sed -i 's/from run import db/from app.database import db/g' "$file"
        echo "✓ Fixed import in $file"
    fi
done

# 4. Update app/__init__.py
if [ -f /app/app/__init__.py ]; then
    echo "Updating app/__init__.py to use centralized database module..."
    cp -f /app/app/__init__.py /app/app/__init__.py.bak
    
    # Check if __init__.py defines db directly
    if grep -q "db = SQLAlchemy()" /app/app/__init__.py; then
        echo "  app/__init__.py defines db, updating..."
        # This is a complex update that would be better done with a full file replacement
        cat > /app/app/__init__.py.new << 'EOF'
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
from dotenv import load_dotenv

# Import database from the centralized location
from app.database import db, init_db

# Initialize login manager
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
        log_dir = os.path.join(base_dir, 'logs')
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
        except FileExistsError:
            pass
        
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
    init_db(app)  # Initialize database using the centralized function
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
        return {'now': datetime.utcnow}  # Use utcnow instead of now
    
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
    
    return app
EOF
        mv /app/app/__init__.py.new /app/app/__init__.py
        echo "✓ Updated app/__init__.py with centralized database imports"
    else
        echo "  app/__init__.py doesn't need modification"
    fi
else
    echo "⚠ app/__init__.py not found"
fi

# 5. Update wsgi.py
echo "Updating wsgi.py..."
cat > /app/wsgi.py << 'EOF'
"""
WSGI entry point for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import the app factory function
from app import create_app

# Create the application instance
app = create_app()

# This is what will be imported by Gunicorn
application = app

if __name__ == "__main__":
    # Run the app if this script is executed directly (not recommended for production)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8001)))
EOF
echo "✓ Updated wsgi.py"

# 6. Update run.py
echo "Updating run.py..."
cat > /app/run.py << 'EOF'
"""
Development server entry point.
This file is used for local development only.
For production, use wsgi.py with Gunicorn.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001, debug=True)
EOF
echo "✓ Updated run.py"

# 7. Clean Python cache
echo "Cleaning Python cache files..."
find /app -name "*.pyc" -delete
find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
echo "✓ Python cache cleaned"

echo ""
echo "===== ALL FIXES APPLIED SUCCESSFULLY ====="
echo "You can now restart Gunicorn with:"
echo "gunicorn --bind 127.0.0.1:8000 --workers 3 wsgi:application"
echo "===== FIX COMPLETE =====" 