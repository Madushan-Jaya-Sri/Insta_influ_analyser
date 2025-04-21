#!/bin/bash
set -e

# Debug information
echo "Current directory: $(pwd)"
echo "Contents of current directory:"
ls -la
echo "Python version:"
python --version
echo "Python path:"
python -c "import sys; print(sys.path)"
echo "Check for create_app in app.py:"
python -c "import app; print(dir(app)); print('create_app' in dir(app))"

# Create necessary directories
mkdir -p /app/app/data
mkdir -p /app/app/uploads
mkdir -p /app/app/static/images

# Set permissions
chmod -R 755 /app/app/data
chmod -R 755 /app/app/uploads
chmod -R 755 /app/app/static/images

# Get port from environment or use default
PORT=${PORT:-5000}

# Start Gunicorn server - use main.py instead of app.py
cd /app
exec gunicorn --bind 0.0.0.0:${PORT} --workers 3 --timeout 120 "main:create_app()" 