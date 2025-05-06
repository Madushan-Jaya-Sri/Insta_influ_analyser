#!/bin/bash
# Deployment fix script for Instagram Influencer Analyzer
# Run this on your server to fix common 502 errors

echo "===== Instagram Influencer Analyzer Deployment Fix ====="
echo "Starting diagnostic and fix process..."

# Check if we're in the correct directory
if [ ! -f "run.py" ] || [ ! -d "app" ]; then
    echo "ERROR: This script must be run from the root directory of the Instagram Influencer Analyzer project."
    exit 1
fi

# Make sure directories exist
echo "Creating required directories..."
mkdir -p app/data
mkdir -p app/static/images/profiles
mkdir -p app/static/images/posts
mkdir -p app/static/images/misc
mkdir -p app/uploads
mkdir -p app/data/sessions

# Set correct permissions
echo "Setting correct permissions..."
chmod -R 755 app/data
chmod -R 755 app/static/images
chmod -R 755 app/uploads
chmod -R 755 app/data/sessions

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating a default .env file..."
    cat > .env << EOL
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 24)
PORT=8001
EOL
    echo "NOTE: Please update the .env file with your specific settings."
fi

# Check if Python modules are installed
echo "Checking Python modules..."
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip is not installed. Please install Python and pip."
    exit 1
fi

echo "Installing required Python modules..."
pip install -r requirements.txt

# Check if gunicorn is installed
if ! command -v gunicorn &> /dev/null; then
    echo "Installing gunicorn..."
    pip install gunicorn
fi

# Create a test database if needed
echo "Making sure database can be created..."
python -c "from app import create_app, db; app=create_app(); app.app_context().push(); db.create_all()"

echo "===== Fix process completed ====="
echo ""
echo "To start the application using Gunicorn, run:"
echo "gunicorn --bind 0.0.0.0:8001 wsgi:app"
echo ""
echo "Or if you want to run in development mode:"
echo "python run.py"
echo ""
echo "If you're still seeing a 502 error, check your logs with:"
echo "tail -f /var/log/nginx/error.log # If using nginx" 