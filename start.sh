#!/bin/bash
set -e

echo "Starting Nginx..."
nginx -t && nginx

echo "Starting Gunicorn..."
cd /app
gunicorn --bind 127.0.0.1:8000 --timeout 120 --workers 3 --log-level info --access-logfile - --error-logfile - app:app

# Keep the container running if gunicorn fails
exec "$@"