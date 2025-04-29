#!/bin/bash

# Start Nginx
nginx

# Start Gunicorn
cd /app
gunicorn --bind 127.0.0.1:8000 app:app

# Keep the container running
exec "$@"