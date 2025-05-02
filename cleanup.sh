#!/bin/bash
# Cleanup script for Instagram Influencer Analyzer
# Usage: 
#   ./cleanup.sh         - clean temporary files only
#   ./cleanup.sh --all   - clean all, including database and user data
#   ./cleanup.sh --db    - reset database only
#   ./cleanup.sh --help  - show this help message

set -e

# Print help message
if [ "$1" == "--help" ]; then
  echo "Usage:"
  echo "  ./cleanup.sh         - clean temporary files only"
  echo "  ./cleanup.sh --all   - clean all, including database and user data"
  echo "  ./cleanup.sh --db    - reset database only"
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