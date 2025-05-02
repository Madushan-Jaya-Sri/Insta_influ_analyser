#!/bin/bash
set -e

# Set up necessary directories
echo "Setting up application directories..."
mkdir -p /app/app/static /app/app/uploads /app/app/data
mkdir -p /app/app/static/css /app/app/static/js 
mkdir -p /app/app/static/images/profiles /app/app/static/images/posts /app/app/static/images/brand
chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Create missing CSS file
echo "Creating missing CSS file..."
cat > /app/app/static/css/style.css << 'EOF'
/* Basic styles */
body {
  font-family: 'Arial', sans-serif;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  color: #333;
}
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 15px;
}
EOF

# Create missing logo files
echo "Creating logo files..."
# Create text-based logo file (as a fallback)
echo "MOMENTRO" > /app/app/static/images/brand/momentro-logo.png
echo "MOMENTRO" > /app/app/static/images/brand/momentro_logo.png
chmod 644 /app/app/static/images/brand/momentro-logo.png
chmod 644 /app/app/static/images/brand/momentro_logo.png

# Create favicon
echo "Creating favicon..."
touch /app/app/static/favicon.ico
chmod 644 /app/app/static/favicon.ico

# Debug static files (check directory structure)
echo "Static files directory structure:"
find /app/app/static -type d | sort

# List created files
echo "Created static files:"
find /app/app/static -type f | sort

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