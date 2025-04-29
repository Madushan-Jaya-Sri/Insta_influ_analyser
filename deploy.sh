#!/bin/bash

# Instagram Influencer Analyzer Deployment Script
# This script deploys the application to an EC2 instance

# Exit on any error
set -e

echo "===== Instagram Influencer Analyzer Deployment ====="
echo "Starting deployment process to EC2 instance..."

# Configuration variables
EC2_HOST="13.126.220.175"
EC2_USER="ubuntu"
SSH_KEY_PATH="$HOME/.ssh/insta_analyzer_key.pem"
LOCAL_CODE_DIR="."
REMOTE_APP_DIR="/home/ubuntu/insta_influencer_analyzer"

# Check if key file exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key not found at $SSH_KEY_PATH"
    exit 1
fi

# Ensure SSH key has correct permissions
chmod 400 "$SSH_KEY_PATH"

echo "Packaging application code..."
# Create a temporary tar file excluding unnecessary files
tar --exclude="venv" --exclude=".git" --exclude="__pycache__" \
    --exclude="*.pyc" --exclude=".env" --exclude=".env.*" \
    --exclude="*.db" --exclude="app/data/sessions" \
    -czf /tmp/insta_app.tar.gz "$LOCAL_CODE_DIR"

echo "Transferring files to EC2 instance..."
# Copy the tar file to the EC2 instance
scp -i "$SSH_KEY_PATH" /tmp/insta_app.tar.gz "$EC2_USER@$EC2_HOST:/tmp/"

# Copy configuration files
scp -i "$SSH_KEY_PATH" systemd_service.conf "$EC2_USER@$EC2_HOST:/tmp/insta_analyzer.service"
scp -i "$SSH_KEY_PATH" nginx_config.conf "$EC2_USER@$EC2_HOST:/tmp/insta_analyzer.conf"

echo "Setting up application on EC2 instance..."
# Connect to EC2 and set up the application
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" << 'ENDSSH'
    # Create application directory if it doesn't exist
    mkdir -p $REMOTE_APP_DIR

    # Extract the transferred files
    tar -xzf /tmp/insta_app.tar.gz -C $REMOTE_APP_DIR --strip-components=1
    
    # Navigate to app directory
    cd $REMOTE_APP_DIR
    
    # Create required directories
    mkdir -p app/data/sessions
    mkdir -p app/static/images
    mkdir -p app/uploads
    
    # Set up Python virtual environment
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    pip install -r requirements.txt
    
    # Create production environment file
    cat > .env << 'EOF'
# Application settings
FLASK_ENV=production
SECRET_KEY=JmzPrETNcNdxxJmCwrLqABLYXpw5NeTj9Cb88fSj
PORT=8000

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
EOF
    
    # Set up the database
    python scripts/init_db.py
    
    # Make backup script executable
    chmod +x backup_db.sh
    
    # Move systemd service file to proper location
    sudo mv /tmp/insta_analyzer.service /etc/systemd/system/
    
    # Set up Nginx
    sudo apt-get update
    sudo apt-get install -y nginx
    sudo mv /tmp/insta_analyzer.conf /etc/nginx/sites-available/insta_analyzer
    sudo ln -sf /etc/nginx/sites-available/insta_analyzer /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Reload systemd, enable and restart the service
    sudo systemctl daemon-reload
    sudo systemctl enable insta_analyzer.service
    sudo systemctl restart insta_analyzer.service
    
    # Start Nginx
    sudo systemctl enable nginx
    sudo systemctl restart nginx
    
    # Set correct file permissions
    sudo chown -R ubuntu:ubuntu $REMOTE_APP_DIR
    chmod -R 755 $REMOTE_APP_DIR
    
    echo "Deployment completed on EC2 side!"
ENDSSH

echo "Cleaning up temporary files..."
rm /tmp/insta_app.tar.gz

echo "===== Deployment Complete ====="
echo "Your application should now be running at: http://$EC2_HOST"
echo "To check service status on EC2, run: sudo systemctl status insta_analyzer.service"
echo "To check logs, run: sudo journalctl -u insta_analyzer.service" 