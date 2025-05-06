#!/bin/bash
# Script to fix dependency issues with Flask, Werkzeug and related packages

echo "===== Fixing dependencies for Instagram Influencer Analyzer ====="

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip is not installed. Please install Python and pip."
    exit 1
fi

# Uninstall problematic packages to avoid conflicts
echo "Uninstalling potentially conflicting packages..."
pip uninstall -y werkzeug flask flask-login

# Install correct versions
echo "Installing correct package versions..."
pip install Werkzeug==2.0.3
pip install Flask==2.0.1
pip install Flask-Login==0.5.0

# Install other required packages from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "Installing other dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "ERROR: requirements.txt not found. Please make sure you're in the project root directory."
    exit 1
fi

echo "===== Dependency fix completed ====="
echo ""
echo "Now try running the application again with:"
echo "gunicorn --bind 0.0.0.0:8001 wsgi:app" 