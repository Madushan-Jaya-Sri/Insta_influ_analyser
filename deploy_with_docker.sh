#!/bin/bash
# Simple Docker deployment script for Instagram Influencer Analyzer
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== Instagram Influencer Analyzer Docker Deployment =====${NC}"

# Check for Docker and Docker Compose
echo -e "Checking prerequisites..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo -e "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check for docker-compose or Docker Compose plugin
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

# Fix database.py if needed (just to be sure)
if [ ! -f "app/database.py" ]; then
    echo -e "${YELLOW}Warning: database.py not found, creating it...${NC}"
    cat > app/database.py << 'EOF'
"""Database initialization module to prevent circular imports."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create all tables
    with app.app_context():
        db.create_all()
EOF
    echo -e "${GREEN}✓ Created database.py${NC}"
fi

# Run the fix_auth.sh script if it exists
if [ -f "fix_auth.sh" ]; then
    echo -e "Running auth fix script..."
    chmod +x fix_auth.sh
    ./fix_auth.sh
fi

# Set proper permissions
echo -e "Setting correct permissions..."
chmod -R 755 app
chmod -R 777 app/static/images
chmod -R 777 app/uploads
chmod -R 777 app/data
chmod -R 777 logs

# Build and start Docker containers
echo -e "Building and starting Docker containers..."
$COMPOSE_CMD down
$COMPOSE_CMD build --no-cache
$COMPOSE_CMD up -d

# Check if deployment was successful
echo -e "Checking deployment status..."
sleep 5

if $COMPOSE_CMD ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Deployment successful!${NC}"
    echo -e "Your application is now running at: ${GREEN}http://localhost:8000${NC}"
else
    echo -e "${RED}× Deployment failed!${NC}"
    echo -e "Container logs:"
    $COMPOSE_CMD logs
fi

echo -e "\n${YELLOW}Troubleshooting:${NC}"
echo -e "• To view logs: ${YELLOW}$COMPOSE_CMD logs -f${NC}"
echo -e "• To restart: ${YELLOW}$COMPOSE_CMD restart${NC}"
echo -e "• To stop: ${YELLOW}$COMPOSE_CMD down${NC}" 