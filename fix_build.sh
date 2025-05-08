#!/bin/bash

# Fix Docker build errors by creating necessary files
echo "Starting build fix script..."

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "requirements.txt not found, creating it..."
    cat > requirements.txt << 'EOF'
# Flask and extensions
Flask==2.0.1
Flask-Login==0.5.0
Flask-WTF==1.0.1
Flask-Session==0.4.0
email-validator==1.1.3
Werkzeug==2.0.3

# Database
SQLAlchemy==1.4.39
Flask-SQLAlchemy==2.5.1
Flask-Migrate==3.1.0
alembic==1.7.7

# Data processing
numpy==1.22.4
pandas==1.4.2
matplotlib==3.5.2
scikit-learn==1.0.2
scipy==1.8.1
# wordcloud will be installed separately in the Dockerfile with proper build tools
# wordcloud==1.8.1
Pillow==9.1.1

# HTTP requests
requests==2.27.1
beautifulsoup4==4.11.1

# API integrations
openai==0.28.0  # Using old version for compatibility
apify-client==1.1.0  # Required for Instagram data scraping

# Others
python-dotenv==0.20.0
tqdm==4.64.0
Jinja2==3.1.1
gunicorn==20.1.0  # For production deployment
EOF
    echo "✓ requirements.txt created successfully"
else
    echo "✓ requirements.txt already exists"
fi

# Check if wsgi.py exists, create if not
if [ ! -f "wsgi.py" ]; then
    echo "wsgi.py not found, creating it..."
    cat > wsgi.py << 'EOF'
from app import create_app

application = create_app()

if __name__ == "__main__":
    application.run(host='0.0.0.0', port=8001)
EOF
    echo "✓ wsgi.py created successfully"
else
    echo "✓ wsgi.py already exists"
fi

# Check if Dockerfile exists, create if not
if [ ! -f "Dockerfile" ]; then
    echo "Dockerfile not found, creating it..."
    cat > Dockerfile << 'EOF'
FROM python:3.10-slim

# Install Nginx and required packages for wordcloud and other dependencies
RUN apt-get update && apt-get install -y nginx curl unzip gcc g++ build-essential \
    python3-dev default-libmysqlclient-dev libpng-dev \
    libfreetype6-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/app/static /app/app/uploads /app/app/data
RUN chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Copy requirements first without installing
COPY requirements.txt /app/

# Install basic requirements first
RUN pip install --upgrade pip && \
    pip install --no-cache-dir gunicorn Flask==2.0.1 Flask-Login==0.5.0 Flask-SQLAlchemy==2.5.1 Werkzeug==2.0.3

# Install numpy, matplotlib, and other numerical packages first
RUN pip install --no-cache-dir numpy pandas matplotlib pillow

# Install wordcloud specifically with all dependencies
RUN pip install --no-cache-dir wordcloud==1.8.1

# Install Flask-Migrate for database migrations
RUN pip install --no-cache-dir Flask-Migrate==3.1.0

# Now install remaining requirements
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN if [ -f /app/fix_auth.sh ]; then chmod +x /app/fix_auth.sh; fi
RUN if [ -f /app/emergency_fix.py ]; then chmod +x /app/emergency_fix.py; fi

# Create a simple test to verify wordcloud is installed properly
RUN python -c "import wordcloud; print('Wordcloud installed successfully!')"

# Expose port
EXPOSE 8001

# Command to run the application - hardcoded to bind to 0.0.0.0
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--timeout", "120", "--workers", "3", "wsgi:application"]
EOF
    echo "✓ Dockerfile created successfully"
else
    echo "✓ Dockerfile already exists"
fi

# Check if docker-compose.yml exists, create if not
if [ ! -f "docker-compose.yml" ]; then
    echo "docker-compose.yml not found, creating it..."
    cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  app:
    container_name: instagram-app
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    environment:
      - FLASK_APP=app
      - FLASK_ENV=production
      - FLASK_DEBUG=0
      - SECRET_KEY=${SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL:-sqlite:///app.db}
      - LOG_LEVEL=INFO
      - PYTHONUNBUFFERED=1
      - APIFY_API_TOKEN=${APIFY_API_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./app/static:/app/app/static
      - ./app/uploads:/app/app/uploads
      - ./app/data:/app/app/data
      - ./logs:/app/logs
      - ./app.db:/app/app.db
    networks:
      - instagram_network

  nginx:
    container_name: instagram-nginx
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
      - ./app/static:/app/app/static
      - ./app/uploads:/app/app/uploads
    depends_on:
      - app
    networks:
      - instagram_network

networks:
  instagram_network:
    driver: bridge
EOF
    echo "✓ docker-compose.yml created successfully"
else
    echo "✓ docker-compose.yml already exists"
fi

# Check if nginx.conf exists, create if not
if [ ! -f "nginx.conf" ]; then
    echo "nginx.conf not found, creating it..."
    cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name localhost;
    
    # Serve static files directly
    location /static/ {
        alias /app/app/static/;
        expires 30d;
        try_files $uri =404;
    }
    
    location /uploads/ {
        alias /app/app/uploads/;
        expires 30d;
    }
    
    # Everything else to Flask app - use service name instead of 127.0.0.1
    location / {
        proxy_pass http://app:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
    echo "✓ nginx.conf created successfully"
else
    echo "✓ nginx.conf already exists"
fi

# Make sure the fix_database.py script is in the repository
if [ ! -f "fix_database.py" ]; then
    echo "fix_database.py not found, creating it..."
    cat > fix_database.py << 'EOF'
#!/usr/bin/env python3
"""
Database fix script - run this if you encounter 'no such table' errors.
This script will create all necessary database tables by directly using SQLAlchemy.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("database_fix.log")
    ]
)

logger = logging.getLogger("database_fix")

def fix_database():
    """Create all database tables directly."""
    try:
        # First, check if app.db exists and has proper permissions
        if os.path.exists("app.db"):
            logger.info("Found existing app.db file, setting permissions to 666")
            os.chmod("app.db", 0o666)
        else:
            logger.info("app.db not found, it will be created")
            with open("app.db", "w") as f:
                pass
            os.chmod("app.db", 0o666)
            
        # Now import Flask app and create the tables
        from app import create_app
        from app.database import db
        
        # Import all models to ensure they're registered
        from app.models.user import User
        try:
            from app.models.profile import Profile
            logger.info("Imported Profile model")
        except ImportError:
            logger.warning("Profile model not found or not needed")
        
        try:
            from app.models.post import Post
            logger.info("Imported Post model")
        except ImportError:
            logger.warning("Post model not found or not needed")
            
        try:
            from app.models.analysis import Analysis
            logger.info("Imported Analysis model")
        except ImportError:
            logger.warning("Analysis model not found or not needed")
            
        try:
            from app.models.history import History
            logger.info("Imported History model")
        except ImportError:
            logger.warning("History model not found or not needed")
        
        app = create_app()
        logger.info("Created Flask app instance")
        
        with app.app_context():
            # Check if tables exist before creating
            logger.info("Checking database table status")
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {existing_tables}")
            
            try:
                if 'user' not in existing_tables:
                    logger.info("Creating all database tables...")
                    db.create_all()
                    logger.info("Tables created successfully")
                    
                    # Verify tables were created
                    inspector = db.inspect(db.engine)
                    tables = inspector.get_table_names()
                    logger.info(f"Tables after create_all: {tables}")
                    
                    if 'user' in tables:
                        logger.info("SUCCESS: User table was created")
                    else:
                        logger.error("FAILED: User table was not created")
                else:
                    logger.info("User table already exists, no action needed")
            except Exception as e:
                if "table user already exists" in str(e):
                    logger.info("Table already exists error caught, this is normal and can be ignored")
                    # Even if we get this error, we should still have the table
                    logger.info("SUCCESS: User table exists")
                else:
                    logger.error(f"Error creating tables: {str(e)}")
                    import traceback
                    logger.error(traceback.format_exc())
                    return False
                
            return True
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting database fix script")
    if fix_database():
        logger.info("Database fix completed successfully")
        sys.exit(0)
    else:
        logger.error("Database fix failed")
        sys.exit(1)
EOF
    chmod +x fix_database.py
    echo "✓ fix_database.py created successfully"
else
    chmod +x fix_database.py
    echo "✓ fix_database.py already exists"
fi

echo "All files have been created. Try running the Docker build again."
echo "To run this fix: bash fix_build.sh" 