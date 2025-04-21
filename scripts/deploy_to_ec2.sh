#!/bin/bash

# Exit on error
set -e

# Configuration - using the pre-configured SSH settings
EC2_HOST="13.203.105.218"
SSH_KEY_PATH="/Users/jayasri/Downloads/IG-Analyzer-momentro.pem"
REMOTE_DIR="/home/ubuntu/Insta_influ_analyser"

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "SSH key not found at $SSH_KEY_PATH"
    echo "Trying to use SSH config instead..."
    # Try using the SSH host alias from ~/.ssh/config
    if ssh -T -o BatchMode=yes -o ConnectTimeout=5 IG-Analyzer-momentro exit 2>/dev/null; then
        echo "Using SSH config with host 'IG-Analyzer-momentro'"
        USE_SSH_CONFIG=true
    else
        echo "Could not connect using SSH config either. Please check your SSH setup."
        exit 1
    fi
fi

# Build and package the application
echo "Building application..."
git archive --format=tar.gz -o deploy.tar.gz HEAD

# Upload to EC2
echo "Uploading to EC2..."
if [ "$USE_SSH_CONFIG" = true ]; then
    scp deploy.tar.gz IG-Analyzer-momentro:~
else
    scp -i "$SSH_KEY_PATH" deploy.tar.gz ubuntu@${EC2_HOST}:~
fi

# Deploy on EC2
echo "Deploying on EC2..."
if [ "$USE_SSH_CONFIG" = true ]; then
    ssh IG-Analyzer-momentro << EOF
        # Create application directory if it doesn't exist
        mkdir -p $REMOTE_DIR
        
        # Extract the application
        tar -xzf ~/deploy.tar.gz -C $REMOTE_DIR
        
        # Clean up
        rm ~/deploy.tar.gz
        
        # Set proper permissions
        chmod +x $REMOTE_DIR/scripts/*.sh
        
        # Navigate to application directory
        cd $REMOTE_DIR
        
        # Deploy using Docker Compose
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml build --no-cache
        docker-compose -f docker-compose.prod.yml up -d
EOF
else
    ssh -i "$SSH_KEY_PATH" ubuntu@${EC2_HOST} << EOF
        # Create application directory if it doesn't exist
        mkdir -p $REMOTE_DIR
        
        # Extract the application
        tar -xzf ~/deploy.tar.gz -C $REMOTE_DIR
        
        # Clean up
        rm ~/deploy.tar.gz
        
        # Set proper permissions
        chmod +x $REMOTE_DIR/scripts/*.sh
        
        # Navigate to application directory
        cd $REMOTE_DIR
        
        # Deploy using Docker Compose
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml build --no-cache
        docker-compose -f docker-compose.prod.yml up -d
EOF
fi

# Clean up local tar
rm deploy.tar.gz

echo "Deployment completed successfully!"
if [ "$USE_SSH_CONFIG" = true ]; then
    echo "Your application should be running at http://IG-Analyzer-momentro (13.203.105.218)"
else
    echo "Your application should be running at http://$EC2_HOST" 
    