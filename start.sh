#!/bin/bash
set -e

# Set up necessary directories
echo "Setting up application directories..."
mkdir -p /app/app/static /app/app/uploads /app/app/data
mkdir -p /app/app/static/css /app/app/static/js /app/app/static/images/profiles /app/app/static/images/posts
chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Debug static files (check directory structure)
echo "Static files directory structure:"
find /app/app/static -type d | sort

# Debug Font Awesome files
echo "Checking Font Awesome files:"
ls -la /app/app/static/font-awesome/4.3.0/css/ || echo "Font Awesome directory not found"

echo "Starting Nginx..."
nginx -t && nginx

echo "Starting Gunicorn..."
cd /app
gunicorn --bind 127.0.0.1:8000 --timeout 120 --workers 3 --log-level debug --access-logfile - --error-logfile - app:app

# Keep the container running if gunicorn fails
exec "$@"