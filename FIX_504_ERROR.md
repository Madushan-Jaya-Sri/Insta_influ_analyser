# How to Fix 504 Timeout and Werkzeug Import Errors

This guide will help you fix the 504 Gateway Timeout error and the `ImportError: cannot import name 'url_decode' from 'werkzeug.urls'` error that occurs when running the Instagram Influencer Analyzer in production.

## Problem

The application is failing with these errors:
1. 504 Gateway Timeout - The server is not responding within the configured timeout period
2. ImportError for url_decode from werkzeug.urls - Dependency version mismatch issue

## Solution Steps

### 1. Fix Dependency Issues

There's a conflict with Flask, Werkzeug, and Flask-Login versions. Follow these steps to fix it:

```bash
# SSH into your server
ssh user@your-server-ip

# Navigate to your project directory
cd /path/to/Insta_influ_analyser

# Run the fix dependencies script
chmod +x fix_dependencies.sh
./fix_dependencies.sh
```

This script will:
- Uninstall potentially conflicting packages
- Install the correct versions of Werkzeug (2.0.3), Flask (2.0.1), and Flask-Login (0.5.0)
- Reinstall other required packages from requirements.txt

### 2. Setup Proper Server Configuration

#### Create a systemd service (for Ubuntu/Debian systems)

```bash
# Copy the service file to systemd
sudo cp insta_analyzer.service /etc/systemd/system/

# Modify paths if your installation is different from /home/ubuntu/Insta_influ_analyser
sudo nano /etc/systemd/system/insta_analyzer.service

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable insta_analyzer
sudo systemctl start insta_analyzer

# Check service status
sudo systemctl status insta_analyzer
```

#### Update Nginx Configuration

Make sure your Nginx configuration is correct:

```bash
# Edit the Nginx site configuration
sudo nano /etc/nginx/sites-available/insta_analyzer

# Make sure it matches the provided nginx_config.conf file
# Ensure the static path is correct
# Check that proxy timeouts are increased

# Test Nginx configuration
sudo nginx -t

# If everything looks good, restart Nginx
sudo systemctl restart nginx
```

### 3. Check Logs for Other Issues

If you still encounter problems, check these logs:

```bash
# Check application logs
sudo journalctl -u insta_analyzer.service

# Check Nginx error logs
sudo tail -f /var/log/nginx/insta_analyzer_error.log

# Check Nginx access logs
sudo tail -f /var/log/nginx/insta_analyzer_access.log
```

### 4. Ensure Directories Have Proper Permissions

Make sure all required directories exist and have the right permissions:

```bash
# Run the deploy fix script
cd /path/to/Insta_influ_analyser
chmod +x deploy_fix.sh
./deploy_fix.sh
```

## Expected Outcome

After following these steps, your application should start properly without any dependency errors, and Nginx should be able to proxy requests to it without 504 timeout errors.

## Additional Notes

- If running on a low-memory system, consider reducing the number of Gunicorn workers to 2 instead of 3
- Make sure your .env file has all necessary environment variables set
- Ensure your database is properly configured and accessible 