#!/bin/bash
set -e

echo "=== Deploying Insta_influ_analyser ==="

# Create necessary directories
echo "Setting up directories..."
mkdir -p docker_volumes/app_data docker_volumes/app_uploads docker_volumes/app_static docker_volumes/app_sessions
chmod -R 755 docker_volumes
sudo chown -R $USER:$USER docker_volumes

# Make sure all dependencies are in requirements.txt
if ! grep -q "flask-session" requirements.txt; then
  echo "Adding flask-session to requirements.txt"
  echo "flask-session==0.5.0" >> requirements.txt
fi

# Ensure nginx directory exists
mkdir -p nginx

# Set up environment file if not exists
if [ ! -f ".env" ]; then
  echo "Creating .env file"
  cat > .env << EOF
FLASK_ENV=production
SECRET_KEY="Insta_influ_analyser"
OPENAI_API_KEY="your_openai_api_key"
APIFY_API_TOKEN="your_apify_token"
APIFY_TOKEN="your_apify_token"
EOF
  echo "Created .env file - please edit with your actual API keys before continuing"
  exit 1
fi

# Stop any existing containers
echo "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start the container
echo "Building and starting the application..."
docker-compose -f docker-compose.prod.yml up -d --build

# Check container status
echo "Checking container status..."
docker ps

echo "=== Deployment complete ==="
echo "Your application should be available at:"
echo "http://$(curl -s ifconfig.me):80"
echo "or"
echo "http://$(curl -s ifconfig.me):5000 (direct to Flask)" 