# Docker Deployment Guide

This guide explains how to deploy the Instagram Influencer Analyzer using Docker and Docker Compose, both locally and on an EC2 instance.

## Prerequisites

- Docker Engine installed
- Docker Compose installed
- Basic understanding of Docker concepts
- SSL certificates for production deployment (optional but recommended)

## Local Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Insta_influ_analyser.git
cd Insta_influ_analyser
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit the `.env` file to set your configuration:

```
SECRET_KEY=your_secure_random_string
OPENAI_API_KEY=your_openai_api_key
APIFY_API_TOKEN=your_apify_token
```

### 3. Build and Start Containers

```bash
docker-compose up -d
```

This command will:
- Build the application image
- Create and start the Flask application container
- Create and start the Nginx container
- Create Docker volumes for persistent data

### 4. Access the Application

Open your browser and navigate to:
- http://localhost (redirects to HTTPS)
- https://localhost (requires self-signed certificate acceptance)

### 5. Check Container Logs

```bash
# View logs from the application container
docker-compose logs -f web

# View logs from the Nginx container
docker-compose logs -f nginx
```

### 6. Stop Containers

```bash
docker-compose down
```

## Production Deployment on EC2

### 1. Set Up EC2 Instance

Follow the instructions in [EC2-DEPLOYMENT.md](EC2-DEPLOYMENT.md) to set up an EC2 instance. Make sure to:
- Configure security groups to allow ports 22 (SSH), 80 (HTTP), and 443 (HTTPS)
- Install Docker and Docker Compose on the instance

### 2. Install Docker on EC2

```bash
# Update packages
sudo yum update -y  # For Amazon Linux
# OR
sudo apt update -y  # For Ubuntu

# Install Docker
sudo amazon-linux-extras install docker -y  # For Amazon Linux
# OR
sudo apt install docker.io -y  # For Ubuntu

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group
sudo usermod -aG docker ec2-user  # Use 'ubuntu' instead of 'ec2-user' for Ubuntu
```

Log out and back in for group changes to take effect.

### 3. Install Docker Compose on EC2

```bash
# Download Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.17.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Apply executable permissions
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### 4. Deploy the Application

```bash
# Clone the repository
git clone https://github.com/your-username/Insta_influ_analyser.git
cd Insta_influ_analyser

# Set up environment variables
cp .env.example .env
nano .env  # Edit with your actual credentials
```

### 5. Set Up SSL Certificates

For production, you should use real SSL certificates. You can:

- Use Let's Encrypt to obtain free certificates
- Use certificates provided by your organization

Create the SSL directory:

```bash
mkdir -p nginx/ssl
```

#### Option A: Using Let's Encrypt

```bash
sudo apt install certbot -y
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates to the project directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/server.crt
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/server.key

# Set proper permissions
sudo chmod 644 nginx/ssl/server.crt
sudo chmod 640 nginx/ssl/server.key
```

#### Option B: Using Self-Signed Certificates (For Testing Only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout nginx/ssl/server.key -out nginx/ssl/server.crt
```

### 6. Update Nginx Configuration

Edit `nginx/conf.d/insta-analyzer.conf` to set your domain:

```bash
nano nginx/conf.d/insta-analyzer.conf
```

Update the `server_name` directive:

```
server_name yourdomain.com www.yourdomain.com;
```

### 7. Launch the Application with Docker Compose

```bash
docker-compose up -d
```

### 8. Monitor the Deployment

```bash
# Check if containers are running
docker-compose ps

# View logs
docker-compose logs -f
```

### 9. Set Up Auto-Restart

To ensure your containers restart after server reboots:

```bash
# Enable Docker to start on boot
sudo systemctl enable docker

# Verify Docker Compose is using restart: always in docker-compose.yml
```

## Updating the Application

To update your application:

```bash
# Pull latest code
git pull

# Rebuild and restart containers
docker-compose down
docker-compose build
docker-compose up -d
```

## Backup and Restore

### Backup Volumes

```bash
# Create a backup directory
mkdir -p backups

# Backup data volume
docker run --rm -v insta_influ_analyser_app_data:/data -v $(pwd)/backups:/backup alpine tar -czf /backup/app_data_$(date +%Y%m%d).tar.gz /data

# Backup uploads volume
docker run --rm -v insta_influ_analyser_app_uploads:/data -v $(pwd)/backups:/backup alpine tar -czf /backup/app_uploads_$(date +%Y%m%d).tar.gz /data

# Backup images volume
docker run --rm -v insta_influ_analyser_app_images:/data -v $(pwd)/backups:/backup alpine tar -czf /backup/app_images_$(date +%Y%m%d).tar.gz /data
```

### Restore Volumes

```bash
# Restore data volume
docker run --rm -v insta_influ_analyser_app_data:/data -v $(pwd)/backups:/backup alpine sh -c "rm -rf /data/* && tar -xzf /backup/app_data_YYYYMMDD.tar.gz -C /data --strip-components=1"

# Restore uploads volume
docker run --rm -v insta_influ_analyser_app_uploads:/data -v $(pwd)/backups:/backup alpine sh -c "rm -rf /data/* && tar -xzf /backup/app_uploads_YYYYMMDD.tar.gz -C /data --strip-components=1"

# Restore images volume
docker run --rm -v insta_influ_analyser_app_images:/data -v $(pwd)/backups:/backup alpine sh -c "rm -rf /data/* && tar -xzf /backup/app_images_YYYYMMDD.tar.gz -C /data --strip-components=1"
```

## Troubleshooting

### Container Not Starting

Check logs for error messages:

```bash
docker-compose logs web
```

### Nginx Not Serving the Application

Check Nginx configuration:

```bash
docker-compose exec nginx nginx -t
```

### Permission Issues

Check permissions on volumes:

```bash
# Enter the container
docker-compose exec web bash

# Check permissions
ls -la app/data app/uploads app/static/images
```

### SSL Certificate Issues

Verify certificates:

```bash
openssl x509 -in nginx/ssl/server.crt -text -noout
```

## Security Considerations

- **Environment Variables**: Never commit `.env` files to version control
- **SSL Certificates**: Use proper certificates for production
- **Docker Network**: Customize network settings for additional security
- **Volume Permissions**: Ensure proper permissions on mounted volumes
- **Regular Updates**: Keep base images and dependencies updated 