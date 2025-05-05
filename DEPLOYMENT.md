# Deployment Guide for Instagram Influencer Analyzer

This guide provides instructions for deploying the Instagram Influencer Analyzer application to a production environment and troubleshooting common issues.

## Prerequisites

- Python 3.8 or higher
- pip for package installation
- git for version control
- Access to a server with SSH capabilities
- A database (SQLite for testing, PostgreSQL recommended for production)

## Deployment Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Insta_influ_analyser.git
cd Insta_influ_analyser
```

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables

Create a `.env` file in the root directory with the following variables:

```
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=your_secure_secret_key
DATABASE_URL=postgresql://username:password@localhost/dbname  # For PostgreSQL
OPENAI_API_KEY=your_openai_api_key
```

### 5. Initialize the Database

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 6. Create Required Directories

The application requires several directories for storing data. Run the diagnostic script to check and create them:

```bash
python check_deployment.py
```

### 7. Run the Deployment Diagnostics

This will ensure all prerequisites are met:

```bash
python check_deployment.py
```

### 8. Start the Application

For testing:
```bash
python run.py
```

For production with Gunicorn:
```bash
gunicorn --bind 0.0.0.0:8001 --workers 4 "app:create_app()"
```

## Common Deployment Issues and Solutions

### 1. Missing Directory Permissions

**Issue**: The application can't write to data directories.

**Solution**: 
- Ensure the application user has write permissions to all directories
- Run: `chmod -R 755 app/data app/static/images app/static/charts`

### 2. Background Processing Issues

**Issue**: Analysis processes start but don't complete, or updates don't appear in the UI.

**Solution**:
- Check if the server allows background threads
- Check for file writing permissions
- Visit the `/debug/logs` endpoint while logged in to view diagnostic information

### 3. OpenAI API Integration Issues

**Issue**: Content analysis doesn't work in production.

**Solution**:
- Verify the OpenAI API key is correctly set in the environment
- Check if the deployed server can access the OpenAI API (network restrictions)
- The application handles both old and new OpenAI SDK versions

### 4. Database Connection Issues

**Issue**: Application fails to connect to the database.

**Solution**:
- Verify the DATABASE_URL environment variable is correctly set
- Ensure the database server is accessible from the application server
- Check database user permissions

### 5. UI Not Updating

**Issue**: Actions happen in the background but UI doesn't update.

**Solution**:
- Check browser console for JavaScript errors
- Ensure the progress tracking API endpoint is accessible
- Verify that the server is responding to AJAX requests

## Monitoring and Logging

### Setting Up Logging

For better error tracking, add a logging configuration:

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Instagram Influencer Analyzer startup')
```

## Security Considerations

1. Always use HTTPS in production
2. Keep the SECRET_KEY secure and unique for each deployment
3. Use environment variables for sensitive credentials
4. Regularly update dependencies to patch security vulnerabilities
5. Consider adding rate limiting for the API endpoints

## Performance Optimization

1. Use a production-ready web server like Nginx in front of Gunicorn
2. Consider Redis for caching and session storage
3. Use a connection pool for database connections
4. Optimize static file delivery with proper caching headers

For any persistent issues, check the application logs and run the diagnostic script to gather debugging information. 