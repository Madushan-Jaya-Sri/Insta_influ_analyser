# Deployment Guide for Instagram Influencer Analyzer

This document provides detailed instructions for deploying the Instagram Influencer Analyzer application to an AWS EC2 instance.

## Prerequisites

1. AWS Account with EC2 instance created
2. EC2 instance with Ubuntu Linux distribution
3. SSH key pair for accessing the EC2 instance
4. The SSH key file saved at `~/.ssh/insta_analyzer_key.pem`
5. Python 3.8+ installed on the EC2 instance
6. Proper security groups configured on the EC2 instance (see `ec2_security_instructions.md`)

## Deployment Steps

### 1. Prepare Local Environment

Before deployment, ensure:
1. All code changes are committed
2. Tests are passing
3. All dependencies are listed in `requirements.txt`

### 2. Run Deployment Script

The application includes a deployment script that automates the process:

```bash
chmod +x deploy.sh
./deploy.sh
```

This script performs the following actions:
- Packages the application code (excluding development files)
- Transfers the package to the EC2 instance
- Installs necessary dependencies
- Sets up the application with Gunicorn as the WSGI server
- Configures Nginx as a reverse proxy
- Creates a systemd service for automatic startup
- Sets appropriate permissions

### 3. Verify Deployment

After deployment, verify the application is running correctly:

```bash
./check_deployment.sh
```

This script checks:
- Application service status
- Nginx status
- Application logs
- Open ports

### 4. Manual Deployment (If Script Fails)

If the script fails, follow these manual steps:

1. SSH into the EC2 instance:
   ```bash
   ssh -i ~/.ssh/insta_analyzer_key.pem ubuntu@13.126.220.175
   ```

2. Create application directory:
   ```bash
   mkdir -p ~/insta_influencer_analyzer
   ```

3. Clone the repository or upload files (if not using the script):
   ```bash
   git clone https://github.com/yourusername/Insta_influ_analyser.git ~/insta_influencer_analyzer
   ```

4. Install dependencies:
   ```bash
   cd ~/insta_influencer_analyzer
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. Set up systemd service:
   ```bash
   sudo cp systemd_service.conf /etc/systemd/system/insta_analyzer.service
   sudo systemctl daemon-reload
   sudo systemctl enable insta_analyzer.service
   sudo systemctl start insta_analyzer.service
   ```

6. Set up Nginx:
   ```bash
   sudo apt-get update
   sudo apt-get install -y nginx
   sudo cp nginx_config.conf /etc/nginx/sites-available/insta_analyzer
   sudo ln -sf /etc/nginx/sites-available/insta_analyzer /etc/nginx/sites-enabled/
   sudo rm -f /etc/nginx/sites-enabled/default
   sudo systemctl enable nginx
   sudo systemctl restart nginx
   ```

## Maintenance

### Database Backups

Automatic database backups are configured via the `backup_db.sh` script.
To manually trigger a backup:

```bash
./backup_db.sh
```

### Updating the Application

To update the deployed application:

1. Make and test changes locally
2. Run the deployment script again:
   ```bash
   ./deploy.sh
   ```

### Troubleshooting

Common issues and their solutions:

1. Application not accessible:
   - Check security groups in AWS console
   - Verify nginx and gunicorn services are running
   - Check application logs with `sudo journalctl -u insta_analyzer.service`

2. Database issues:
   - Check database permissions
   - Ensure database path is correctly set in the application config

3. Static files not loading:
   - Check Nginx configuration for the static files location
   - Ensure proper permissions on static directories

### Resources

For more information, see:
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [Gunicorn Documentation](https://docs.gunicorn.org/en/stable/)
- [Nginx Documentation](https://nginx.org/en/docs/) 