#!/bin/bash

# Script to fix permissions and create required static files on the EC2 instance

set -e

echo "Fixing permissions and creating required files..."

# Create directories if they don't exist
mkdir -p app/static/images/brand
mkdir -p app/static/css
mkdir -p app/data

# Set permissions
chmod -R 777 app/static app/data

# Create empty users.json if it doesn't exist
if [ ! -f app/data/users.json ]; then
    echo "Creating empty users.json file..."
    echo "[]" > app/data/users.json
    chmod 666 app/data/users.json
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
    
    chmod 666 app/static/images/brand/momentro-logo.png
fi

# Restart the containers
echo "Restarting containers..."
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "Done! All permissions and files should be fixed." 