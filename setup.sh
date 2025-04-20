#!/bin/bash
set -e

# Create necessary directories for the application
echo "Creating required directories..."
mkdir -p app/uploads app/data app/static/images/profiles app/static/images/posts app/static/images/brand
mkdir -p nginx/ssl nginx/conf.d
mkdir -p certbot/www certbot/conf

# Ensure proper permissions
echo "Setting correct permissions..."
chmod +x docker-entrypoint.sh
chmod 755 app/uploads app/data app/static/images

# Generate self-signed SSL certificates for development (optional)
if [ "$1" == "--with-ssl" ]; then
    echo "Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/server.key -out nginx/ssl/server.crt \
        -subj "/CN=localhost" 2>/dev/null
    chmod 600 nginx/ssl/server.key
fi

# Prepare environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please update the .env file with your credentials."
fi

echo "Setup complete! You can now run the application with:"
echo "  docker-compose up -d"
echo ""
echo "For development mode use:"
echo "  docker-compose -f docker-compose.dev.yml up -d" 