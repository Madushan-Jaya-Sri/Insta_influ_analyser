#!/bin/bash
set -e

echo "🔧 Advanced troubleshooting for Insta_influ_analyser"
echo "------------------------------------------------"
echo

# Function to display section headers
section() {
  echo
  echo "🔍 $1"
  echo "----------------------"
}

# Stop any running containers
section "Stopping all containers"
docker-compose -f docker-compose.prod.yml down || true
docker ps -q | xargs -r docker stop
docker ps -aq | xargs -r docker rm

# Clean up Docker system
section "Cleaning Docker system"
docker system prune -f
docker volume prune -f

# Check Docker version
section "Docker version"
docker --version
docker-compose --version

# Setup app directories
section "Setting up directories"
mkdir -p docker_volumes/app_data docker_volumes/app_uploads docker_volumes/app_static docker_volumes/app_sessions
chmod -R 777 docker_volumes
sudo chown -R $USER:$USER docker_volumes

# Make sure the .env file exists
section "Creating/checking .env file"
if [ ! -f ".env" ]; then
  echo "Creating .env file"
  echo "FLASK_ENV=production" > .env
  echo "SECRET_KEY=Insta_influ_analyser" >> .env
  # Add any other required env vars
else
  echo ".env file exists"
  grep -v "API\|KEY\|TOKEN\|SECRET" .env
fi

# Check memory and disk space
section "System resources"
free -h
df -h

# Test Docker network
section "Docker network"
docker network prune -f
docker network create app_network || true

# Build with direct logs
section "Building and starting containers"
docker-compose -f docker-compose.prod.yml build --no-cache

# Start containers with detailed logs
docker-compose -f docker-compose.prod.yml up -d

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 15

# Check container status
section "Container status"
docker ps -a

# Test directly connecting to Flask (bypass nginx)
section "Testing direct Flask connection"
echo "Trying to connect to Flask on port 5000..."
curl -v http://localhost:5000 || echo "❌ Could not connect directly to Flask app"

# Check logs
section "Flask app logs"
docker logs flask_app

section "Nginx logs"
docker logs nginx

# Try restarting nginx container
section "Restarting nginx container"
docker restart nginx

# Final status check
section "Final container status"
docker ps

echo
echo "✅ Troubleshooting completed!"
echo "If the application is still not working, check the logs using:"
echo "docker logs flask_app"
echo "docker logs nginx"
echo
echo "Try accessing the app directly at http://13.126.220.175:5000"
echo "And through nginx at http://13.126.220.175" 