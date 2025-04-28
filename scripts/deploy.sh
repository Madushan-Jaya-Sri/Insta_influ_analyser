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
mkdir -p uploads data static app/data/sessions app/uploads app/static/images app/static/css app/static/js app/static/images/brand
chmod -R 777 uploads data static app/data app/uploads app/static

# Make sure CSS directories exist
if [ ! -f app/static/css/style.css ]; then
    echo "Creating basic style.css file..."
    cat > app/static/css/style.css << EOF
/* Base styles */
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 0;
    background-color: #f4f4f4;
}

.container {
    width: 80%;
    margin: auto;
    overflow: hidden;
}

/* Form styles */
.auth-form {
    background: #fff;
    padding: 20px;
    border-radius: 5px;
    box-shadow: 0 0 10px rgba(0,0,0,0.1);
    max-width: 500px;
    margin: 30px auto;
}

.form-group {
    margin-bottom: 15px;
}

.btn {
    display: inline-block;
    padding: 10px 15px;
    background: #333;
    color: #fff;
    border: none;
    border-radius: 5px;
    cursor: pointer;
}

.btn-primary {
    background: #007bff;
}

.btn-primary:hover {
    background: #0069d9;
}

/* Alert styles */
.alert {
    padding: 15px;
    margin-bottom: 20px;
    border: 1px solid transparent;
    border-radius: 4px;
}

.alert-success {
    color: #155724;
    background-color: #d4edda;
    border-color: #c3e6cb;
}

.alert-danger {
    color: #721c24;
    background-color: #f8d7da;
    border-color: #f5c6cb;
}
EOF
fi

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

# Ensure permissions are correctly set after container startup
echo "Setting proper permissions for data directories..."
sleep 5
chmod -R 777 uploads data static app/data app/uploads app/static
docker exec flask_app chmod -R 777 /app/app/data /app/data

# Check if containers are running
echo "Checking container status..."
docker ps

echo "Deployment completed successfully!"
echo "Your application should now be available at http://13.126.220.175"
echo ""
echo "To view logs:"
echo "  docker-compose -f docker-compose.prod.yml logs -f" 