#!/bin/bash

# Exit on error
set -e

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git

# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group
sudo usermod -aG docker ${USER}

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.3/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /home/ubuntu/Insta_influ_analyser

# Clone the repository (if using HTTPS)
# git clone https://github.com/YOUR_USERNAME/Insta_influ_analyser.git /home/ubuntu/Insta_influ_analyser

# Create directories for certbot (SSL)
mkdir -p /home/ubuntu/Insta_influ_analyser/certbot/conf
mkdir -p /home/ubuntu/Insta_influ_analyser/certbot/www

# Create .env file template (to be filled manually)
cat << EOF > /home/ubuntu/Insta_influ_analyser/.env.example
# Application settings
FLASK_ENV=production
SECRET_KEY=your_random_secure_key_here

# API Keys
OPENAI_API_KEY=your_openai_api_key_here
APIFY_API_TOKEN=your_apify_api_token_here
EOF

echo "EC2 instance setup complete!"
echo "Next steps:"
echo "1. Clone your repository to /home/ubuntu/Insta_influ_analyser"
echo "2. Create .env file with your environment variables"
echo "3. Deploy using docker-compose -f docker-compose.prod.yml up -d" 