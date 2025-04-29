#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting deployment process..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install -r requirements.txt

# Set up environment variables
echo "🔑 Setting up environment variables..."
if [ ! -f .env ]; then
    cat > .env << EOL
FLASK_APP=app
FLASK_ENV=production
SECRET_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///instance/app.db
EOL
fi

# Initialize database
echo "🗄️ Initializing database..."
flask db upgrade

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p instance
mkdir -p app/static/uploads
mkdir -p app/static/images

# Set permissions
echo "🔒 Setting permissions..."
chmod -R 755 app/static/uploads
chmod -R 755 app/static/images

# Start the application
echo "🚀 Starting the application..."
if command -v gunicorn &> /dev/null; then
    gunicorn -w 4 -b 0.0.0.0:5000 app:app
else
    echo "⚠️ Gunicorn not found. Starting with Flask development server..."
    flask run --host=0.0.0.0
fi 