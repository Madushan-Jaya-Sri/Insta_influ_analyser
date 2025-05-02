#!/bin/bash
# Cleanup script for Instagram Influencer Analyzer
# Usage: 
#   ./cleanup.sh         - clean temporary files only
#   ./cleanup.sh --all   - clean all, including database and user data
#   ./cleanup.sh --db    - reset database only
#   ./cleanup.sh --root  - clean root directory files that should be in app directory
#   ./cleanup.sh --data  - clean all data files (DB and JSON)
#   ./cleanup.sh --help  - show this help message

set -e

# Print help message
if [ "$1" == "--help" ]; then
  echo "Usage:"
  echo "  ./cleanup.sh         - clean temporary files only"
  echo "  ./cleanup.sh --all   - clean all, including database and user data"
  echo "  ./cleanup.sh --db    - reset database only"
  echo "  ./cleanup.sh --root  - clean root directory files that should be in app directory"
  echo "  ./cleanup.sh --data  - clean all data files (DB and JSON)"
  echo "  ./cleanup.sh --help  - show this help message"
  exit 0
fi

echo "=== Instagram Influencer Analyzer Cleanup Tool ==="
echo "Starting cleanup process..."

# Clean temporary files
echo "Cleaning temporary files..."
rm -f *.log *.bak *.tmp
rm -f momentro-logo.html
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".DS_Store" -delete
find . -name "*.swp" -delete
echo "Temporary files cleaned."

# Clean root directory if --root or --all is specified
if [ "$1" == "--root" ] || [ "$1" == "--all" ]; then
  echo "Cleaning root directory..."
  
  # Move app.db to app/data if it exists at root
  if [ -f "app.db" ]; then
    echo "Removing app.db from root directory..."
    rm -f app.db
    echo "app.db removed from root directory"
  fi
  
  # Remove static and uploads folders from root if they exist
  # (they should be in app directory)
  if [ -d "static" ] && [ -d "app/static" ]; then
    echo "Moving files from root static directory to app/static..."
    cp -r static/* app/static/ 2>/dev/null || true
    rm -rf static
    echo "Root static directory removed"
  fi
  
  if [ -d "uploads" ] && [ -d "app/uploads" ]; then
    echo "Moving files from root uploads directory to app/uploads..."
    cp -r uploads/* app/uploads/ 2>/dev/null || true
    rm -rf uploads
    echo "Root uploads directory removed"
  fi
  
  if [ -d "data" ] && [ -d "app/data" ]; then
    echo "Moving files from root data directory to app/data..."
    cp -r data/* app/data/ 2>/dev/null || true
    rm -rf data
    echo "Root data directory removed"
  fi
  
  echo "Root directory cleaned."
fi

# Clean all data files if --data or --all is specified
if [ "$1" == "--data" ] || [ "$1" == "--all" ]; then
  echo "Removing all data files (DB and JSON)..."
  
  # Remove database files
  find . -name "*.db" -delete
  echo "Database files removed."
  
  # Remove uploaded JSON files
  rm -rf app/uploads/*.json
  echo "Uploaded JSON files removed."
  
  # Remove saved data files in user directories
  rm -rf app/data/user_*
  echo "User data directories removed."
  
  # Remove any other JSON files in data directory
  rm -f app/data/*.json
  echo "Data JSON files removed."
  
  # Recreate necessary directories
  mkdir -p app/data
  mkdir -p app/uploads
  echo "All data files have been removed."
fi

# Clean user uploads if --all is specified
if [ "$1" == "--all" ]; then
  echo "Cleaning all user data..."
  rm -rf app/uploads/*
  mkdir -p app/uploads
  echo "User uploads cleaned."
  
  # Clean user-specific static files
  find app/static/images -path "*/user_*" -type d -exec rm -rf {} + 2>/dev/null || true
  echo "User-specific static files cleaned."
fi

# Reset database if --db or --all is specified
if [ "$1" == "--db" ] || [ "$1" == "--all" ]; then
  echo "Resetting database..."
  rm -rf app/data/*.db
  mkdir -p app/data
  
  # If we have a virtual environment, use it
  if [ -d "venv" ]; then
    source venv/bin/activate
  fi
  
  # Initialize an empty database
  python -c "from run import db, create_app; app = create_app(); with app.app_context(): db.create_all()"
  echo "Database reset complete."
fi

echo "Cleanup completed successfully!"
echo "Current root directory contents:"
ls -la | grep -v "^\."
echo ""
echo "To deploy with a clean database, run: CLEAN_DB=true ./deploy.sh"
echo "To deploy with all data removed, run: CLEAN_DATA=true ./deploy.sh" 