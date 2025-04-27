# Deployment Guide for Instagram Influencer Analyzer

This guide explains how to deploy the application to an EC2 instance using Docker and GitHub Actions.

## Prerequisites

1. An AWS EC2 instance with a public IP address (13.126.220.175 in this case)
2. GitHub repository with the following secrets configured:
   - `AWS_HOST`: Your EC2 public IP address
   - `AWS_USERNAME`: SSH username for your EC2 instance (usually 'ubuntu' or 'ec2-user')
   - `AWS_SSH_KEY`: Private SSH key for connecting to your EC2 instance
   - `SECRET_KEY`: A random string for your Flask application
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `APIFY_API_TOKEN`: Your Apify API token

## EC2 Setup Options

### Option 1: Manual Setup

1. SSH into your EC2 instance:
   ```bash
   ssh -i your-key.pem ubuntu@13.126.220.175
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

3. Run the setup script:
   ```bash
   chmod +x scripts/setup_ec2.sh
   ./scripts/setup_ec2.sh
   ```

4. Deploy the application:
   ```bash
   chmod +x scripts/deploy.sh
   ./scripts/deploy.sh
   ```

### Option 2: GitHub Actions CI/CD (Recommended)

1. Fork this repository to your GitHub account

2. Add the required secrets to your GitHub repository:
   - Go to your repository → Settings → Secrets and variables → Actions
   - Add the following repository secrets:
     - `AWS_HOST`: Your EC2 IP address (e.g., 13.126.220.175)
     - `AWS_USERNAME`: Your EC2 username (usually 'ubuntu')
     - `AWS_SSH_KEY`: Your private SSH key (the content of your .pem file)
     - `SECRET_KEY`: A random string for Flask
     - `OPENAI_API_KEY`: Your OpenAI API key
     - `APIFY_API_TOKEN`: Your Apify API token

3. Push to the main or master branch to trigger the deployment workflow.

   The GitHub Actions workflow will:
   - Create necessary directories on your EC2 instance
   - Copy files to the EC2 instance
   - Install Docker and Docker Compose if needed
   - Build and start the Docker containers

## Deployment Process

The deployment process consists of:

1. **Environment Setup**: Creating directories and environment variables
2. **Docker Build**: Building the Docker images defined in docker-compose.prod.yml
3. **Container Deployment**: Running the containers with the correct configuration

## Architecture

The deployed application uses:

- **Flask App**: The main application running on port 5000
- **Nginx**: A reverse proxy running on port 80, forwarding requests to the Flask app
- **Docker Compose**: Orchestrating the containers and networking
- **Docker Volumes**: Persisting data between deployments

## Checking Deployment Status

To check if the deployment succeeded:

```bash
ssh -i your-key.pem ubuntu@13.126.220.175
cd ~/Insta_influ_analyser
docker-compose ps
```

You should see both the `flask_app` and `nginx` containers running.

The application will be accessible at:
- http://13.126.220.175 (via nginx)
- http://13.126.220.175:5000 (direct Flask access)

## Troubleshooting

### Common Issues

1. **Container fails to start**:
   ```bash
   docker logs flask_app
   ```

2. **Nginx configuration issues**:
   ```bash
   docker exec -it nginx nginx -t
   ```

3. **Permission issues**:
   ```bash
   sudo chown -R $USER:$USER ~/Insta_influ_analyser
   ```

4. **Deployment workflow fails**:
   - Check GitHub Actions logs
   - Ensure all secrets are correctly configured
   - Verify SSH access to the EC2 instance

## Maintenance

### Updating the Application

To update the application:

1. Push changes to the main/master branch (for CI/CD)
2. OR manually update on the server:
   ```bash
   cd ~/Insta_influ_analyser
   git pull
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d --build
   ```

### Monitoring Logs

```bash
docker logs flask_app
docker logs nginx
```

### Backup Data

Important data is stored in Docker volumes. To backup:

```bash
tar -czvf insta_influ_backup.tar.gz ~/Insta_influ_analyser/docker_volumes
```

## Security Considerations

- The application exposes ports 80 and 5000
- All API keys are stored as environment variables
- Static files are served by Nginx for better performance
- Regular backups are recommended

## Contact

For support, please reach out to the development team. 