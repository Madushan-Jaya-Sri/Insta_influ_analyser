#!/bin/bash

# Deployment script for Instagram Influencer Analyzer
# This script should be run on the EC2 instance

set -e  # Exit on any error

echo "Starting deployment process..."

# Ensure we're in the correct directory
cd "$(dirname "$0")/.."
PROJECT_ROOT=$(pwd)

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Create it before deploying."
    exit 1
fi

# Ensure necessary directories exist
echo "Creating necessary directories..."
mkdir -p uploads data static app/data/sessions app/uploads app/static/images
chmod -R 777 uploads data static app/data app/uploads app/static

# Pull latest changes if it's a git repository
if [ -d .git ]; then
    echo "Pulling latest changes from git..."
    git pull
fi

# Stop and remove existing containers
echo "Stopping any existing containers..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start new containers
echo "Building and starting new containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Check if containers are running
echo "Checking container status..."
sleep 5
docker ps

echo "Deployment completed successfully!"
echo "Your application should now be available at http://13.126.220.175"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f" 