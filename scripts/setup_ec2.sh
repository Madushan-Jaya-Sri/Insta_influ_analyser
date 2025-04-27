#!/bin/bash
set -e

# This script sets up an EC2 instance for deploying the Insta_influ_analyser app
echo "Setting up EC2 instance for deployment..."

# Update and install dependencies
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
sudo apt-get update
sudo apt-get install -y docker-ce

# Add current user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose
echo "Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.6/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create directories for Docker volumes
echo "Creating Docker volume directories..."
mkdir -p ~/Insta_influ_analyser/docker_volumes/app_data
mkdir -p ~/Insta_influ_analyser/docker_volumes/app_uploads 
mkdir -p ~/Insta_influ_analyser/docker_volumes/app_static
mkdir -p ~/Insta_influ_analyser/docker_volumes/app_sessions
mkdir -p ~/Insta_influ_analyser/nginx
chmod -R 755 ~/Insta_influ_analyser/docker_volumes

# Setup Firewall rules
echo "Setting up firewall rules..."
sudo apt-get install -y ufw
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5000/tcp

# Restart Docker
echo "Restarting Docker service..."
sudo systemctl enable docker
sudo systemctl restart docker

echo "EC2 setup completed!"
echo "You can now run the GitHub Actions workflow to deploy the application."
echo "Make sure you have the following GitHub secrets set:"
echo "- AWS_HOST: Your EC2 IP address (e.g., 13.126.220.175)"
echo "- AWS_USERNAME: Your EC2 username (usually 'ubuntu')"
echo "- AWS_SSH_KEY: Your EC2 SSH private key"
echo "- SECRET_KEY: A secret key for Flask"
echo "- OPENAI_API_KEY: Your OpenAI API key"
echo "- APIFY_API_TOKEN: Your Apify API token" 