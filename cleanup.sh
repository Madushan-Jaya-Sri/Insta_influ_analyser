#!/bin/bash
# Comprehensive cleanup script for Docker containers, images and volumes

echo "=== Starting Docker environment cleanup ==="

# Stop and remove all running containers
echo "Stopping all running containers..."
docker stop $(docker ps -a -q) || echo "No containers to stop"

echo "Removing all containers..."
docker rm -f $(docker ps -a -q) || echo "No containers to remove"

# Remove all Docker networks (except default ones)
echo "Removing custom Docker networks..."
docker network prune -f

# Remove unused volumes
echo "Removing Docker volumes..."
docker volume prune -f

# Remove unused images
echo "Removing unused Docker images..."
docker image prune -a -f

# Remove specific container names that we know might exist
echo "Ensuring specific containers are gone..."
docker rm -f insta_analyzer_app nginx flask_app || echo "No specific containers to remove"

# Remove specific Docker Compose setup if it exists
echo "Cleaning up Docker Compose setups in known locations..."

# List of possible locations
LOCATIONS=(
  "/home/ubuntu/insta_influencer_analyzer"
  "/home/ubuntu/Insta_influ_analyser"
  "~/insta_influencer_analyzer"
  "~/Insta_influ_analyser"
)

for LOC in "${LOCATIONS[@]}"; do
  if [ -d "$LOC" ]; then
    echo "Found directory: $LOC"
    if [ -f "$LOC/docker-compose.yml" ]; then
      echo "Found docker-compose.yml in $LOC - stopping services"
      cd "$LOC" && docker-compose down -v
    fi
  fi
done

# Sometimes we need to kill processes using ports we want
echo "Checking for processes using port 8000..."
sudo lsof -i :8000 | grep LISTEN
if [ $? -eq 0 ]; then
  echo "Found processes using port 8000, attempting to kill them..."
  sudo kill -9 $(sudo lsof -t -i:8000) || echo "Failed to kill processes"
fi

echo "Checking for processes using port 80..."
sudo lsof -i :80 | grep LISTEN
if [ $? -eq 0 ]; then
  echo "Found processes using port 80, attempting to kill them..."
  sudo kill -9 $(sudo lsof -t -i:80) || echo "Failed to kill processes"
fi

# Make sure nginx is not running at the system level
echo "Stopping system Nginx if running..."
sudo systemctl stop nginx || echo "No system Nginx to stop"

echo "=== Cleanup completed ==="
echo "You can now deploy your application from scratch!" 