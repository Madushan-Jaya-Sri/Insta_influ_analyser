#!/bin/bash
set -e

# Configuration
if [ -z "$1" ]; then
    echo "Usage: ./deploy.sh <ec2-username>@<ec2-host> [ssh-key-path]"
    echo "Example: ./deploy.sh ec2-user@ec2-12-34-56-78.compute-1.amazonaws.com ~/.ssh/my-key.pem"
    exit 1
fi

EC2_CONNECTION="$1"
SSH_KEY=""

if [ ! -z "$2" ]; then
    SSH_KEY="-i $2"
fi

echo "=== Instagram Influencer Analyzer Deployment ==="
echo "Target: $EC2_CONNECTION"
echo ""

# Check SSH connection
echo "Testing SSH connection..."
ssh $SSH_KEY -o ConnectTimeout=5 $EC2_CONNECTION "echo SSH connection successful" || { echo "SSH connection failed. Check your credentials and try again."; exit 1; }

# Create deployment directory on EC2
echo "Creating deployment directory..."
ssh $SSH_KEY $EC2_CONNECTION "mkdir -p ~/Insta_influ_analyser/nginx/conf.d ~/Insta_influ_analyser/nginx/ssl"

# Copy files to EC2
echo "Copying files to EC2..."
scp $SSH_KEY docker-compose.yml $EC2_CONNECTION:~/Insta_influ_analyser/
scp $SSH_KEY .env.example $EC2_CONNECTION:~/Insta_influ_analyser/
scp $SSH_KEY nginx/conf.d/insta-analyzer.conf $EC2_CONNECTION:~/Insta_influ_analyser/nginx/conf.d/
scp $SSH_KEY nginx/conf.d/http.conf $EC2_CONNECTION:~/Insta_influ_analyser/nginx/conf.d/
scp $SSH_KEY docker-entrypoint.sh $EC2_CONNECTION:~/Insta_influ_analyser/
scp $SSH_KEY setup.sh $EC2_CONNECTION:~/Insta_influ_analyser/

# Set up environment on EC2
echo "Setting up environment on EC2..."
ssh $SSH_KEY $EC2_CONNECTION "cd ~/Insta_influ_analyser && chmod +x setup.sh && ./setup.sh --with-ssl"

# Configure environment file
echo "Please update your .env file on the EC2 instance with your credentials."
echo "You can do this by running:"
echo "  ssh $SSH_KEY $EC2_CONNECTION \"nano ~/Insta_influ_analyser/.env\""
echo ""

# Inform about next steps
echo "====================================="
echo "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Update the .env file on your EC2 instance"
echo "2. Run the application with:"
echo "   ssh $SSH_KEY $EC2_CONNECTION \"cd ~/Insta_influ_analyser && docker-compose up -d\""
echo ""
echo "For automatic deployments, set up GitHub Actions as described in CICD.md" 