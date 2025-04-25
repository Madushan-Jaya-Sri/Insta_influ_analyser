#!/bin/bash
set -e

echo "This script will clean up the Insta_influ_analyser directory for a fresh deployment."
echo "It will back up any existing files before removing them."
echo ""
read -p "Are you sure you want to continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Operation cancelled."
    exit 1
fi

# Create a backup folder with timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="$HOME/backups/insta_influ_${TIMESTAMP}"
APP_DIR="$HOME/Insta_influ_analyser"

echo "Creating backup directory at $BACKUP_DIR"
mkdir -p "$BACKUP_DIR"

# Check if the app directory exists
if [ -d "$APP_DIR" ]; then
    echo "Backing up existing files from $APP_DIR to $BACKUP_DIR"
    
    # Copy everything to backup
    cp -R "$APP_DIR/"* "$BACKUP_DIR/" 2>/dev/null || true
    cp -R "$APP_DIR/".* "$BACKUP_DIR/" 2>/dev/null || true
    
    # Remove the app directory
    echo "Removing $APP_DIR"
    rm -rf "$APP_DIR"
    
    # Recreate empty directory
    echo "Creating empty $APP_DIR"
    mkdir -p "$APP_DIR"
    
    echo "Cleanup completed successfully!"
    echo "Your old files are backed up at $BACKUP_DIR"
    echo "The system is now ready for a fresh deployment."
else
    echo "Directory $APP_DIR does not exist. Nothing to clean up."
    mkdir -p "$APP_DIR"
    echo "Created empty $APP_DIR directory."
fi 