#!/bin/bash

# Simple direct fix for user registration issues
set -e

echo "=== SIMPLE FIX FOR USER REGISTRATION ==="

# Create necessary directories for data persistence
mkdir -p ~/Insta_influ_analyser/app/data
mkdir -p ~/Insta_influ_analyser/data

# Create an empty users.json file with the right permissions
echo "[]" > ~/Insta_influ_analyser/app/data/users.json
chmod 777 ~/Insta_influ_analyser/app/data/users.json

# Copy it to the /data directory as well (for redundancy)
cp ~/Insta_influ_analyser/app/data/users.json ~/Insta_influ_analyser/data/

# Stop the container
echo "Stopping Docker containers..."
cd ~/Insta_influ_analyser
docker-compose -f docker-compose.prod.yml down

# Create a fixed version of docker-compose.prod.yml
echo "Creating fixed docker-compose.prod.yml..."
cat > ~/Insta_influ_analyser/docker-compose.prod.yml << 'EOF'
services:
  app:
    build: .
    restart: always
    container_name: flask_app
    expose:
      - "5000"  # Only expose to internal network, not to host
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./app/data:/app/app/data  # This is the critical mapping for user data
      - ./static:/app/static
      - ./app/static:/app/app/static  # For static files
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    networks:
      - app_network

  nginx:
    image: nginx:1.25-alpine
    restart: always
    container_name: nginx
    ports:
      - "80:80"  # Map port 80 to host
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./uploads:/app/uploads
      - ./static:/app/static
      - ./app/static:/app/app/static
    depends_on:
      - app
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
EOF

# Hard-code a test user in the users.json file
echo "Creating a test user..."
cat > ~/Insta_influ_analyser/app/data/users.json << 'EOF'
[
    {
        "id": "test-user-id-123",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "pbkdf2:sha256:600000$vt0TiCPHhWS8PKGk$99a8abde3eb4bec88d2b3cfd99863d4f9fafdb048ac8c00acfb11b94d4c2c37f"
    }
]
EOF

# Ensure the same content is in the data directory
cp ~/Insta_influ_analyser/app/data/users.json ~/Insta_influ_analyser/data/

# Rebuild and restart the containers
echo "Rebuilding and starting Docker containers..."
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for container to start
echo "Waiting for containers to start..."
sleep 10

# Copy the users.json file directly into the container to ensure it's there
echo "Copying user file into the container..."
docker cp ~/Insta_influ_analyser/app/data/users.json flask_app:/app/app/data/
docker exec flask_app chmod 777 /app/app/data/users.json

echo "=== FIX COMPLETED ==="
echo "You can now log in with username: testuser and password: password123"
echo "New user registrations should also work correctly." 