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

# Update the run.py to use sessions properly
echo "Updating run.py with session handling..."
cat > ~/Insta_influ_analyser/run.py << 'EOF'
from app import create_app
from flask_session import Session

app = create_app()

# Initialize Flask-Session
Session(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
EOF

# Update requirements to include Flask-Session
echo "Updating requirements.txt..."
echo "flask-session==0.5.0" >> ~/Insta_influ_analyser/requirements.txt

# Restart containers
echo "Restarting containers..."
cd ~/Insta_influ_analyser
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

echo "Waiting 15 seconds for containers to start..."
sleep 15

# Copy files again after container restart
echo "Copying users.json into container after restart..."
docker cp ~/Insta_influ_analyser/app/data/users.json flask_app:/app/app/data/
docker exec flask_app chmod 777 /app/app/data/users.json

echo "=== DEBUG COMPLETED ==="
echo "You can now try logging in with: username: testuser, password: password123"
echo "If login still fails, please try registering a new user with the registration form."
echo "Check the Flask logs with: docker logs flask_app" 