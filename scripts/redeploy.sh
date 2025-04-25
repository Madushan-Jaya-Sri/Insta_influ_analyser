#!/bin/bash
set -e

echo "Redeploying Insta_influ_analyser application"
echo "-------------------------------------------"
echo

# Stop and remove all containers
echo "Stopping and removing all containers..."
docker-compose -f docker-compose.prod.yml down || true

# Remove any dangling images
echo "Cleaning up Docker..."
docker system prune -f || true

# Install required packages if missing
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y netcat-openbsd iproute2 iputils-ping net-tools

# Ensure the app directories exist
echo "Setting up directories..."
mkdir -p docker_volumes/app_data docker_volumes/app_uploads docker_volumes/app_static docker_volumes/app_sessions
chmod -R 755 docker_volumes
chown -R $USER:$USER docker_volumes

# Ensure nginx directory exists
mkdir -p nginx

# Install netcat and ping utilities in the containers
echo "Creating .env file if it doesn't exist..."
if [ ! -f .env ]; then
  echo "FLASK_ENV=production" > .env
  echo "SECRET_KEY=Insta_influ_analyser" >> .env
fi

# Force recreate containers and build
echo "Building and starting containers..."
docker-compose -f docker-compose.prod.yml up -d --build --force-recreate

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 10

# Check container status
echo "Container status:"
docker ps -a

echo
echo "Application logs:"
docker logs flask_app | tail -n 20

echo
echo "nginx logs:"
docker logs nginx | tail -n 20

echo
echo "Redeployment completed!"
echo "You can access the application at http://13.126.220.175" 