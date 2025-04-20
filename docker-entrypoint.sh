#!/bin/bash
set -e

# Create necessary directories if they don't exist
mkdir -p app/uploads app/data app/static/images/profiles app/static/images/posts app/static/images/brand

# Set proper permissions
chmod -R 755 app/uploads app/data app/static

# Get the port from environment variable or use default
PORT=${PORT:-5000}

# Start gunicorn server
exec gunicorn --bind 0.0.0.0:${PORT} --workers 3 --timeout 120 "app:create_app()" 