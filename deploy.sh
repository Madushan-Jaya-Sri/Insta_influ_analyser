#!/bin/bash
# Deployment script for the Instagram Influencer Analyzer
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Instagram Influencer Analyzer Deployment =====${NC}"
echo -e "Starting deployment process..."

# Check for Docker and Docker Compose
echo -e "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo -e "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: docker-compose not found, checking for Docker Compose plugin...${NC}"
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}Error: Neither docker-compose nor Docker Compose plugin found${NC}"
        echo -e "Please install Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    else
        echo -e "${GREEN}✓ Docker Compose plugin found${NC}"
        COMPOSE_CMD="docker compose"
    fi
else
    echo -e "${GREEN}✓ docker-compose found${NC}"
    COMPOSE_CMD="docker-compose"
fi

# Ensure necessary directories exist
echo -e "Creating necessary directories..."
mkdir -p ./app/static/images/{profiles,posts,brand}
mkdir -p ./app/uploads
mkdir -p ./app/data
mkdir -p ./logs

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found, creating default...${NC}"
    cat > .env << EOF
# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
FLASK_DEBUG=0

# Security - CHANGE THESE IN PRODUCTION!
SECRET_KEY=super-secret-key-please-change-in-prod

# Database Configuration (SQLite by default)
DATABASE_URL=sqlite:///app.db

# Logging
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✓ Created default .env file${NC}"
    echo -e "${YELLOW}WARNING: Please edit the .env file to set proper secrets for production!${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Build and start the containers
echo -e "Building Docker images..."
$COMPOSE_CMD build --no-cache

echo -e "Starting containers..."
$COMPOSE_CMD up -d

# Check if the application is running
echo -e "Waiting for application to start..."
sleep 5

# Check if the container is running
if $COMPOSE_CMD ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Application is running${NC}"
    
    # Get container IP
    CONTAINER_ID=$($COMPOSE_CMD ps -q app)
    if [ -n "$CONTAINER_ID" ]; then
        echo -e "Container ID: $CONTAINER_ID"
    fi
    
    echo -e "${GREEN}===== Deployment Successful! =====${NC}"
    echo -e "Your application is now running. You can access it at:"
    echo -e "${GREEN}http://localhost:8000${NC}"
    
    # Check for common issues
    echo -e "\n${YELLOW}Important Notes:${NC}"
    echo -e "1. If you encounter any circular import issues, run the fix script inside the container:"
    echo -e "   ${YELLOW}docker exec -it $CONTAINER_ID bash -c 'chmod +x /app/fix_deployment.sh && /app/fix_deployment.sh'${NC}"
    echo -e "2. To view logs:"
    echo -e "   ${YELLOW}$COMPOSE_CMD logs -f${NC}"
    echo -e "3. To restart the application:"
    echo -e "   ${YELLOW}$COMPOSE_CMD restart${NC}"
else
    echo -e "${RED}ERROR: Application failed to start!${NC}"
    echo -e "Checking container logs:"
    $COMPOSE_CMD logs
    echo -e "\n${YELLOW}Try running the fix script manually:${NC}"
    echo -e "1. ${YELLOW}$COMPOSE_CMD exec app bash${NC}"
    echo -e "2. ${YELLOW}chmod +x /app/fix_deployment.sh && /app/fix_deployment.sh${NC}"
    echo -e "3. ${YELLOW}exit${NC}"
    echo -e "4. ${YELLOW}$COMPOSE_CMD restart${NC}"
fi 