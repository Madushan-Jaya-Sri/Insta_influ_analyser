# Deploying to AWS EC2

This guide explains how to deploy the Instagram Influencer Analyzer to an AWS EC2 instance.

## Prerequisites

- An AWS account
- Basic knowledge of AWS services
- SSH client installed on your local machine
- Domain name (optional, but recommended)

## Step 1: Create an EC2 Instance

1. Log in to your AWS Management Console
2. Navigate to EC2 Dashboard
3. Click "Launch Instance"
4. Choose an Amazon Machine Image (AMI)
   - Recommended: Amazon Linux 2 or Ubuntu Server 22.04 LTS
5. Choose Instance Type 
   - Recommended: t2.micro (free tier) for testing, t2.small or better for production
6. Configure Instance Details (use defaults or customize as needed)
7. Add Storage (default 8GB is sufficient to start)
8. Add Tags (optional)
9. Configure Security Group
   - Allow SSH (port 22) from your IP
   - Allow HTTP (port 80) from anywhere
   - Allow HTTPS (port 443) from anywhere
10. Review and Launch
11. Create or select an existing key pair and download it
12. Launch Instance

## Step 2: Connect to Your EC2 Instance

1. Open your terminal
2. Change permissions for your key pair:
   ```bash
   chmod 400 your-key-pair.pem
   ```
3. Connect to your instance:
   ```bash
   ssh -i your-key-pair.pem ec2-user@your-instance-public-ip
   ```
   Note: Use `ubuntu` instead of `ec2-user` if you selected Ubuntu AMI

## Step 3: Set Up Server Environment

1. Update system packages:
   ```bash
   sudo yum update -y  # For Amazon Linux
   # OR
   sudo apt update && sudo apt upgrade -y  # For Ubuntu
   ```

2. Install required dependencies:
   ```bash
   # For Amazon Linux
   sudo yum install -y python3 python3-pip python3-devel git nginx
   sudo amazon-linux-extras install -y epel
   
   # For Ubuntu
   sudo apt install -y python3 python3-pip python3-venv git nginx
   ```

3. Install Python development tools and virtual environment:
   ```bash
   # For Amazon Linux
   sudo yum install -y python3-devel gcc
   
   # For Ubuntu
   sudo apt install -y python3-dev build-essential
   ```

## Step 4: Clone Repository and Set Up Application

1. Clone your repository:
   ```bash
   git clone https://github.com/your-username/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your actual credentials
   ```

## Step 5: Configure Gunicorn

1. Test Gunicorn to make sure it can serve your application:
   ```bash
   gunicorn --bind 0.0.0.0:8000 "app:create_app()"
   ```

2. Create a systemd service file to manage Gunicorn:
   ```bash
   sudo nano /etc/systemd/system/insta-analyzer.service
   ```

3. Add the following configuration (adjust paths as needed):
   ```
   [Unit]
   Description=Gunicorn instance to serve Instagram Influencer Analyzer
   After=network.target

   [Service]
   User=ec2-user
   Group=ec2-user
   WorkingDirectory=/home/ec2-user/Insta_influ_analyser
   Environment="PATH=/home/ec2-user/Insta_influ_analyser/venv/bin"
   EnvironmentFile=/home/ec2-user/Insta_influ_analyser/.env
   ExecStart=/home/ec2-user/Insta_influ_analyser/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 "app:create_app()"

   [Install]
   WantedBy=multi-user.target
   ```

4. Start and enable the Gunicorn service:
   ```bash
   sudo systemctl start insta-analyzer
   sudo systemctl enable insta-analyzer
   sudo systemctl status insta-analyzer  # Check if it's running
   ```

## Step 6: Configure Nginx as a Reverse Proxy

1. Create a new Nginx site configuration:
   ```bash
   sudo nano /etc/nginx/sites-available/insta-analyzer
   ```
   
   For Ubuntu, or:
   
   ```bash
   sudo nano /etc/nginx/conf.d/insta-analyzer.conf
   ```
   
   For Amazon Linux.

2. Add the following configuration:
   ```
   server {
       listen 80;
       server_name your-domain.com www.your-domain.com;  # Replace with your domain or server IP
       
       location /static {
           alias /home/ec2-user/Insta_influ_analyser/app/static;
       }
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

3. For Ubuntu, create a symbolic link:
   ```bash
   sudo ln -s /etc/nginx/sites-available/insta-analyzer /etc/nginx/sites-enabled
   ```

4. Test Nginx configuration:
   ```bash
   sudo nginx -t
   ```

5. Restart Nginx:
   ```bash
   sudo systemctl restart nginx
   ```

## Step 7: Set Up SSL with Let's Encrypt (Optional but Recommended)

1. Install Certbot:
   ```bash
   # For Amazon Linux
   sudo yum install -y certbot python3-certbot-nginx
   
   # For Ubuntu
   sudo apt install -y certbot python3-certbot-nginx
   ```

2. Obtain and install SSL certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com -d www.your-domain.com
   ```

3. Certbot will automatically update your Nginx configuration to use SSL

4. Set up auto-renewal:
   ```bash
   sudo certbot renew --dry-run
   ```
   
   Renewal will be handled automatically by a cron job installed by Certbot.

## Step 8: Firewall Configuration (If Using)

For Ubuntu:
```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
sudo ufw status
```

## Step 9: Test Your Deployment

1. Open your web browser and navigate to your domain or server IP
2. Verify that the application is working correctly

## Troubleshooting

- Check Gunicorn logs:
  ```bash
  sudo journalctl -u insta-analyzer
  ```

- Check Nginx logs:
  ```bash
  sudo tail -f /var/log/nginx/error.log
  ```

- Check application logs:
  ```bash
  tail -f /home/ec2-user/Insta_influ_analyser/app.log  # If you've set up logging to a file
  ```

## Maintenance

- Pulling updates from GitHub:
  ```bash
  cd ~/Insta_influ_analyser
  git pull
  source venv/bin/activate
  pip install -r requirements.txt
  sudo systemctl restart insta-analyzer
  ```

- Monitoring system resources:
  ```bash
  htop  # Install with: sudo yum install htop (Amazon Linux) or sudo apt install htop (Ubuntu)
  ```

This guide provides basic deployment steps. For a production environment, consider additional measures like:
- Setting up a database backup strategy
- Implementing monitoring solutions
- Configuring auto-scaling
- Setting up a CI/CD pipeline (see CICD.md) 