FROM python:3.10-slim

# Install Nginx and required packages including build essential tools for wordcloud
RUN apt-get update && apt-get install -y nginx curl unzip gcc build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/app/static /app/app/uploads /app/app/data
RUN mkdir -p /app/app/static/css /app/app/static/js /app/app/static/images/profiles /app/app/static/images/posts /app/app/static/images/brand
RUN mkdir -p /app/app/static/font-awesome/4.3.0/css /app/app/static/font-awesome/4.3.0/fonts

# Download and install Font Awesome
RUN curl -L https://fontawesome.com/v4/assets/font-awesome-4.3.0.zip -o /tmp/font-awesome.zip \
    && unzip -q /tmp/font-awesome.zip -d /tmp \
    && cp -r /tmp/font-awesome-4.3.0/css/* /app/app/static/font-awesome/4.3.0/css/ \
    && cp -r /tmp/font-awesome-4.3.0/fonts/* /app/app/static/font-awesome/4.3.0/fonts/ \
    && rm -rf /tmp/font-awesome* || echo "Font Awesome download failed, continuing anyway"

# Create a basic style.css file
RUN echo "/* Basic styles */\nbody {\n  font-family: 'Arial', sans-serif;\n  line-height: 1.6;\n  margin: 0;\n  padding: 0;\n  color: #333;\n}\n.container {\n  width: 100%;\n  max-width: 1200px;\n  margin: 0 auto;\n  padding: 15px;\n}" > /app/app/static/css/style.css

# Create empty logo files (will be populated by start.sh)
RUN touch /app/app/static/images/brand/momentro-logo.png \
    && touch /app/app/static/images/brand/momentro_logo.png \
    && touch /app/app/static/favicon.ico

# Ensure directories have proper permissions
RUN chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Copy requirements first without installing (we'll modify it)
COPY requirements.txt /app/

# Modify requirements to remove wordcloud if needed
RUN sed -i 's/wordcloud-binary==1.8.1/# wordcloud-binary==1.8.1 - Will be installed separately/g' requirements.txt && \
    sed -i 's/wordcloud==1.8.1/# wordcloud==1.8.1 - Will be installed separately/g' requirements.txt

# Install dependencies with proper setup
RUN pip install --upgrade pip && \
    pip install --no-cache-dir gunicorn Flask==2.0.1 Flask-Login==0.5.0 Flask-SQLAlchemy==2.5.1 Werkzeug==2.0.3 && \
    # Install main requirements first
    pip install --no-cache-dir --prefer-binary -r requirements.txt && \
    # Now directly install wordcloud with build tools already installed
    pip install --no-cache-dir wordcloud==1.8.1

# Create database.py file first - this ensures proper imports
RUN mkdir -p /app/app && \
    echo '"""Database initialization module to prevent circular imports."""\n\nfrom flask_sqlalchemy import SQLAlchemy\nfrom flask_migrate import Migrate\n\n# Initialize extensions without app context\ndb = SQLAlchemy()\nmigrate = Migrate()\n\ndef init_db(app):\n    """Initialize database with Flask app."""\n    db.init_app(app)\n    migrate.init_app(app, db)\n    \n    # Create all tables\n    with app.app_context():\n        db.create_all()\n' > /app/app/database.py

# Copy application code
COPY . .

# Fix the auth.py file to use the centralized database
RUN if [ -f /app/app/routes/auth.py ]; then \
    # Make a backup
    cp /app/app/routes/auth.py /app/app/routes/auth.py.bak && \
    # Replace the problematic import line
    sed -i 's/from run import db/from app.database import db/g' /app/app/routes/auth.py && \
    echo "Fixed circular import in auth.py"; \
fi

# Update wsgi.py
RUN echo '"""WSGI entry point for the application."""\nimport os\nfrom dotenv import load_dotenv\n\n# Load environment variables\nload_dotenv()\n\n# Import application factory\nfrom app import create_app\n\n# Create app instance\napp = create_app()\n\n# This is the object imported by Gunicorn\napplication = app\n\nif __name__ == "__main__":\n    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))\n' > /app/wsgi.py

# Make scripts executable
COPY start.sh /start.sh
RUN chmod +x /start.sh
COPY cleanup.sh /cleanup.sh
RUN chmod +x /cleanup.sh
COPY fix_auth.sh /fix_auth.sh
RUN chmod +x /fix_auth.sh
COPY emergency_fix.py /emergency_fix.py
RUN chmod +x /emergency_fix.py

# Run both fix scripts to ensure auth.py is correct
RUN /fix_auth.sh
RUN python /emergency_fix.py

# Clean up unnecessary files
RUN find . -name "*.pyc" -delete && \
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true && \
    find . -name ".DS_Store" -delete && \
    rm -f *.log *.bak *.tmp && \
    echo "Cleaned up unnecessary files during build"

# Expose port
EXPOSE 80

# Run start script
CMD ["/start.sh"] 