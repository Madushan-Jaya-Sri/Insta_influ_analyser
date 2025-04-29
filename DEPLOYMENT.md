# Deployment Guide

## Prerequisites
- Python 3.9 or higher
- pip
- Docker and Docker Compose (for containerized deployment)
- Nginx (for production deployment)
- SSL certificates (for HTTPS)

## Deployment Options

### 1. Simple Deployment (Development)
```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

### 2. Docker Deployment
```bash
# Build and start the containers
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Production Deployment (Systemd)
```bash
# Copy the application to /opt
sudo cp -r . /opt/insta-influ-analyser

# Copy the systemd service file
sudo cp insta-influ-analyser.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Start the service
sudo systemctl start insta-influ-analyser

# Enable automatic startup
sudo systemctl enable insta-influ-analyser
```

## SSL Certificate Setup
1. Generate SSL certificates:
```bash
mkdir -p ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem
```

2. Update Nginx configuration with your domain name
3. Restart Nginx:
```bash
sudo systemctl restart nginx
```

## Environment Variables
Create a `.env` file with the following variables:
```
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///instance/app.db
```

## Backup and Maintenance
1. Database backup:
```bash
# Create backup
cp instance/app.db instance/app.db.backup

# Restore from backup
cp instance/app.db.backup instance/app.db
```

2. Log rotation:
```bash
# Add to /etc/logrotate.d/insta-influ-analyser
/var/log/insta-influ-analyser/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
}
```

## Monitoring
1. Check service status:
```bash
sudo systemctl status insta-influ-analyser
```

2. View logs:
```bash
sudo journalctl -u insta-influ-analyser -f
```

## Troubleshooting
1. Check Nginx error logs:
```bash
sudo tail -f /var/log/nginx/error.log
```

2. Check application logs:
```bash
sudo journalctl -u insta-influ-analyser -f
```

3. Check Docker logs:
```bash
docker-compose logs -f
```

## Security Considerations
1. Keep all software up to date
2. Use strong passwords
3. Regularly backup the database
4. Monitor system logs
5. Use HTTPS only
6. Implement rate limiting
7. Regular security audits

## Performance Optimization
1. Enable Gzip compression
2. Use browser caching
3. Optimize database queries
4. Implement caching where appropriate
5. Use CDN for static files

## Contact

For support, please reach out to the development team. 