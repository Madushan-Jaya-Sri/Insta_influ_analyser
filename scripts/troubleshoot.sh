#!/bin/bash
set -e

echo "Troubleshooting Insta_influ_analyser deployment"
echo "----------------------------------------------"
echo

# Check if Docker is running
echo "Checking Docker status..."
if sudo systemctl is-active docker > /dev/null 2>&1; then
  echo "✅ Docker is running"
else
  echo "❌ Docker is not running"
  echo "   Starting Docker..."
  sudo systemctl start docker
fi

# Check container status
echo
echo "Checking container status..."
docker ps -a

# Check container logs
echo
echo "Checking Flask app logs..."
docker logs flask_app 2>&1 | tail -n 50

echo
echo "Checking nginx logs..."
docker logs nginx 2>&1 | tail -n 50

# Test network connectivity
echo
echo "Testing network connectivity..."
docker exec nginx ping -c 2 flask_app || echo "❌ Cannot ping Flask app from nginx"

# Check nginx config
echo
echo "Checking nginx configuration..."
docker exec nginx nginx -t

# Check the Flask app is listening on port 5000
echo
echo "Checking if Flask app is listening on port 5000..."
docker exec flask_app netstat -tulpn | grep 5000 || echo "❌ Flask app is not listening on port 5000"

echo
echo "Troubleshooting complete!"
echo "If you need to restart the containers, run:"
echo "docker-compose -f docker-compose.prod.yml down"
echo "docker-compose -f docker-compose.prod.yml up -d" 