#!/bin/bash

# Script to fix permissions and create required static files on the EC2 instance

set -e

echo "Fixing permissions and creating required files..."

# Create directories if they don't exist
mkdir -p app/static/images/brand
mkdir -p app/static/css
mkdir -p app/data/sessions
mkdir -p uploads data static

# Set permissions with sudo if available
if command -v sudo &> /dev/null; then
    echo "Using sudo to set permissions..."
    # Remove existing files that might be causing issues
    sudo rm -f app/data/users.json app/data/sessions/*
    
    # Set permissions on directories
    sudo chmod -R 777 app data static uploads
    sudo chmod -R 777 app/static app/data
else
    echo "Setting permissions without sudo..."
    # Try to fix permissions without sudo
    chmod -R 777 app data static uploads 2>/dev/null || true
    chmod -R 777 app/static app/data 2>/dev/null || true
fi

# Create empty users.json file
echo "Creating empty users.json file..."
echo "[]" > app/data/users.json
# Ensure the file has proper permissions
if command -v sudo &> /dev/null; then
    sudo chmod 666 app/data/users.json
else
    chmod 666 app/data/users.json 2>/dev/null || true
fi

# Create a placeholder logo if it doesn't exist
if [ ! -f app/static/images/brand/momentro-logo.png ]; then
    echo "Creating placeholder logo..."
    
    # If ImageMagick is installed, create a simple logo
    if command -v convert &> /dev/null; then
        convert -size 200x50 xc:transparent -fill black -gravity center -annotate 0 "Momentro" app/static/images/brand/momentro-logo.png
    else
        # Fallback - download a simple logo
        curl -s https://via.placeholder.com/200x50/FFFFFF/000000?text=Momentro -o app/static/images/brand/momentro-logo.png
    fi
    
    # Set permissions on the logo
    if command -v sudo &> /dev/null; then
        sudo chmod 666 app/static/images/brand/momentro-logo.png
    else
        chmod 666 app/static/images/brand/momentro-logo.png 2>/dev/null || true
    fi
fi

# Fix container permissions
echo "Fixing container permissions..."
docker-compose -f docker-compose.prod.yml down || true

# Update the Docker volume paths in docker-compose.prod.yml
echo "Updating Docker volume paths in docker-compose.prod.yml..."
cat > docker-compose.prod.yml << EOF
services:
  app:
    build: .
    restart: always
    container_name: flask_app
    expose:
      - "5000"  # Only expose to internal network, not to host
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./app/data:/app/app/data  # Add this mapping for user data
      - ./static:/app/static
      - ./app/static:/app/app/static  # Add this mapping for app static files
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    networks:
      - app_network

  nginx:
    image: nginx:1.25-alpine
    restart: always
    container_name: nginx
    ports:
      - "80:80"  # Map port 80 to host
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./uploads:/app/uploads
      - ./static:/app/static
      - ./app/static:/app/app/static  # Add this mapping for app static files
    depends_on:
      - app
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
EOF

# Restart the containers
echo "Restarting containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# After containers start, try to fix permissions again
echo "Fixing container permissions from inside Docker..."
sleep 5
docker exec flask_app bash -c "mkdir -p /app/app/data/sessions && chmod -R 777 /app/app/data /app/data" || true

echo "Done! All permissions and files should be fixed." 