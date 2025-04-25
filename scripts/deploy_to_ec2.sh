#!/bin/bash
set -e

# Create the necessary directories
echo "Setting up directories..."
mkdir -p docker_volumes/app_data docker_volumes/app_uploads docker_volumes/app_static docker_volumes/app_sessions
chmod -R 755 docker_volumes

# Create .env file with the provided secrets
echo "Creating .env file..."
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY="${SECRET_KEY}"
OPENAI_API_KEY="${OPENAI_API_KEY}"
APIFY_API_TOKEN="${APIFY_API_TOKEN}"
APIFY_TOKEN="${APIFY_API_TOKEN}"
EOF

# Ensure nginx directory exists
mkdir -p nginx

# Pull the latest changes if this is a git repository
if [ -d ".git" ]; then
  echo "Pulling latest changes..."
  git pull
fi

# Build and start the containers
echo "Building and starting Docker containers..."
if command -v docker compose &> /dev/null; then
  # Docker Compose V2
  docker compose -f docker-compose.prod.yml down
  docker compose -f docker-compose.prod.yml build --no-cache
  docker compose -f docker-compose.prod.yml up -d
else
  # Docker Compose V1
  docker-compose -f docker-compose.prod.yml down
  docker-compose -f docker-compose.prod.yml build --no-cache
  docker-compose -f docker-compose.prod.yml up -d
fi

echo "Deployment completed successfully!" 