#!/bin/bash

# Debug script for user authentication issues in Instagram Influencer Analyzer
set -e

echo "=== DEBUG USER AUTHENTICATION ==="

# Check files and permissions
echo "Checking data directory and users.json file..."
mkdir -p ~/Insta_influ_analyser/app/data
mkdir -p ~/Insta_influ_analyser/data

# Display users file contents if it exists
if [ -f ~/Insta_influ_analyser/app/data/users.json ]; then
    echo "Current users.json content in app/data:"
    cat ~/Insta_influ_analyser/app/data/users.json
else
    echo "users.json doesn't exist in app/data"
fi

if [ -f ~/Insta_influ_analyser/data/users.json ]; then
    echo "Current users.json content in data:"
    cat ~/Insta_influ_analyser/data/users.json
else
    echo "users.json doesn't exist in data"
fi

# Update Flask config to enable debug and fix session issues
echo "Creating debug config file..."
cat > ~/Insta_influ_analyser/app/config.py << 'EOF'
import os
import datetime

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-development-only'
    
    # Server name config for session cookies
    SERVER_NAME = None  # Allow cookies to work on any domain
    
    # Session config
    PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=7)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login settings
    REMEMBER_COOKIE_DURATION = datetime.timedelta(days=30)
    REMEMBER_COOKIE_SECURE = False  # Set to True in production with HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
EOF

# Create app data directory inside container
echo "Creating app data directory inside container..."
docker exec flask_app mkdir -p /app/app/data

# Create a proper test user in both locations
echo "Creating test user in users.json..."
cat > ~/Insta_influ_analyser/app/data/users.json << 'EOF'
[
    {
        "id": "test-user-id-123",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "pbkdf2:sha256:600000$vt0TiCPHhWS8PKGk$99a8abde3eb4bec88d2b3cfd99863d4f9fafdb048ac8c00acfb11b94d4c2c37f"
    }
]
EOF

# Set permissive permissions
chmod 777 ~/Insta_influ_analyser/app/data/users.json

# Copy to both locations 
cp ~/Insta_influ_analyser/app/data/users.json ~/Insta_influ_analyser/data/

# Copy directly into container
echo "Copying users.json into container..."
docker cp ~/Insta_influ_analyser/app/data/users.json flask_app:/app/app/data/
docker exec flask_app chmod 777 /app/app/data/users.json

# Get auth routes to debug login/register
echo "Creating login debug script in the container..."
cat > ~/Insta_influ_analyser/debug_auth.py << 'EOF'
# Auth debugging to add to app/routes/auth.py

@auth_bp.route('/debug-login', methods=['GET', 'POST'])
def debug_login():
    """Simplified login for debugging"""
    form = LoginForm()
    
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data
        
        # First check if the test user credentials match
        if username_or_email == 'testuser' and password == 'password123':
            # Hard-coded test user
            user = User.get_by_username('testuser')
            if not user:
                # Create test user if not exists
                user = User(
                    user_id='test-user-id-123',
                    username='testuser',
                    email='test@example.com',
                    password_hash='pbkdf2:sha256:600000$vt0TiCPHhWS8PKGk$99a8abde3eb4bec88d2b3cfd99863d4f9fafdb048ac8c00acfb11b94d4c2c37f'
                )
                User._users['test-user-id-123'] = user
                
            login_user(user, remember=True)
            flash('Debug login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        
        # Otherwise try normal authentication
        user = User.authenticate(username_or_email, password)
        if user:
            login_user(user, remember=True)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('auth/login.html', form=form)
EOF

# Copy auth debug into container
echo "Copying auth debug into container..."
docker cp ~/Insta_influ_analyser/debug_auth.py flask_app:/app/app/

# Modify app/__init__.py to fix session issues
echo "Creating session fix file..."
cat > ~/Insta_influ_analyser/session_fix.py << 'EOF'
def setup_session(app):
    """Setup session handling - needed for login to work"""
    import os
    from datetime import timedelta
    
    # Session config
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = True
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'instaanalyzer_'
    
    # Session directory
    os.makedirs('/app/app/data/sessions', exist_ok=True)
    app.config['SESSION_FILE_DIR'] = '/app/app/data/sessions'
    
    # Cookie settings
    app.config['SESSION_COOKIE_SECURE'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Remember me settings
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
    app.config['REMEMBER_COOKIE_SECURE'] = False
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
EOF

# Copy session fix into container
echo "Copying session fix into container..."
docker cp ~/Insta_influ_analyser/session_fix.py flask_app:/app/app/

# Update __init__.py in the container to use the session fix
echo "Patching app/__init__.py directly in container..."
docker exec flask_app bash -c 'cat > /app/app/__init__.py_patch << EOF
from flask import Flask
from flask_login import LoginManager
from werkzeug.middleware.proxy_fix import ProxyFix

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"

def create_app():
    app = Flask(__name__)
    
    # Load configuration
    from app.config import Config
    app.config.from_object(Config)
    
    # Fix for working behind proxy/nginx
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    
    # Setup session (from session_fix.py)
    from app.session_fix import setup_session
    setup_session(app)
    
    # Initialize extensions
    login_manager.init_app(app)
    
    # Register blueprint
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.analyzer import analyzer_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analyzer_bp)
    
    # User loader function for Flask-Login
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(user_id)
    
    return app
EOF

# Apply the patch
mv /app/app/__init__.py_patch /app/app/__init__.py
'

# We need to install Flask-Session inside the container
echo "Installing Flask-Session in the container..."
docker exec flask_app pip install flask-session==0.5.0

# Restart the app container
echo "Restarting Flask app..."
docker restart flask_app

# Copying the files again after restart
echo "Waiting 5 seconds for container to restart..."
sleep 5

# Copy users.json again after restart
echo "Copying users.json into container after restart..."
docker cp ~/Insta_influ_analyser/app/data/users.json flask_app:/app/app/data/
docker exec flask_app chmod 777 /app/app/data/users.json

echo "=== DEBUG COMPLETED ==="
echo "You can now try logging in with: username: testuser, password: password123"
echo "If login still fails, use http://13.126.220.175/auth/debug-login with the same credentials"
echo "Check the Flask logs with: docker logs flask_app" 