#!/bin/bash

# Update packages
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker
echo "Installing Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo usermod -aG docker $USER
    echo "Docker installed successfully!"
else
    echo "Docker is already installed."
fi

# Install Docker Compose
echo "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "Docker Compose installed successfully!"
else
    echo "Docker Compose is already installed."
fi

# Create app directories
echo "Creating application directories..."
mkdir -p ~/Insta_influ_analyser/app/uploads
mkdir -p ~/Insta_influ_analyser/app/data
mkdir -p ~/Insta_influ_analyser/app/static/images/brand
mkdir -p ~/Insta_influ_analyser/app/static/images/profiles
mkdir -p ~/Insta_influ_analyser/app/static/images/posts

# Setup Nginx for reverse proxy (optional)
echo "Do you want to install Nginx as a reverse proxy? (y/n)"
read install_nginx

if [ "$install_nginx" = "y" ]; then
    echo "Installing Nginx..."
    sudo apt-get install -y nginx
    
    # Configure Nginx
    echo "Configuring Nginx..."
    cat > /tmp/insta_analyser_nginx << 'EOL'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOL
    sudo mv /tmp/insta_analyser_nginx /etc/nginx/sites-available/insta_analyser
    sudo ln -sf /etc/nginx/sites-available/insta_analyser /etc/nginx/sites-enabled/
    sudo rm -f /etc/nginx/sites-enabled/default
    sudo systemctl restart nginx
    echo "Nginx configured successfully!"
fi

echo "EC2 server setup completed successfully!"
echo "You can now deploy your application using GitHub Actions or manually." 