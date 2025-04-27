#!/bin/bash

echo "🔍 Checking container logs for errors"
echo "--------------------------------"

# Check Flask app logs
echo
echo "===== FLASK APP LOGS ====="
docker logs flask_app

# Check Flask app logs for specific errors
echo
echo "===== FLASK ERROR PATTERNS ====="
docker logs flask_app 2>&1 | grep -E "Error|Exception|Failed|Traceback" -A 10 -B 2

# Check environment variables in the container
echo
echo "===== FLASK APP ENVIRONMENT ====="
docker exec -it flask_app env 2>/dev/null || echo "Container not running to check environment"

# Print container configuration
echo
echo "===== CONTAINER CONFIGURATION ====="
docker inspect flask_app | grep -E "Env|Cmd|WorkingDir|Ports|Binds|Volumes" -A 3

# Print status of both containers
echo
echo "===== CONTAINER STATUS ====="
docker ps -a

# Try to run app manually to see the error
echo
echo "===== RUNNING APP MANUALLY IN CONTAINER ====="
docker exec -it flask_app python -c "import run; app = run.create_app(); print('App created successfully')" 2>&1 || echo "Failed to create app manually"

# Create a modified docker-compose for testing
echo
echo "===== CREATING DEBUG DOCKER-COMPOSE ====="
cat > docker-compose.debug.yml << EOF
services:
  app:
    build: .
    restart: "no"
    container_name: flask_app_debug
    ports:
      - "5001:5000"
    volumes:
      - ./docker_volumes/app_uploads:/app/uploads
      - ./docker_volumes/app_data:/app/data
      - ./docker_volumes/app_static:/app/static
    env_file:
      - .env
    environment:
      - FLASK_ENV=development
      - FLASK_DEBUG=1
    command: python run.py
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
EOF

echo
echo "You can run a debug container with:"
echo "docker-compose -f docker-compose.debug.yml up --build"
echo 
echo "Access the application directly at:"
echo "http://13.126.220.175:5000 (main app)"
echo "http://13.126.220.175:5001 (debug app - after running docker-compose -f docker-compose.debug.yml up)" 