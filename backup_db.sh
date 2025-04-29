#!/bin/bash
# Database Backup Script for Instagram Influencer Analyzer
# This script creates a backup of the application database and optionally uploads it to S3

# Configuration variables
BACKUP_DIR="/home/ubuntu/backups"
DB_FILE="/home/ubuntu/insta_influencer_analyzer/app/data/insta_analyser.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="influencer_db_backup_$TIMESTAMP.sql"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_FILENAME"

# Optional S3 configuration
S3_BUCKET="insta-analyzer-backups"  # Set this if you want to upload to S3
S3_ENABLED=false  # Set to true to enable S3 uploads

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database file exists
if [ ! -f "$DB_FILE" ]; then
    echo "Error: Database file not found at $DB_FILE"
    exit 1
fi

echo "Starting database backup..."

# For SQLite, we create a backup using the .backup command
sqlite3 "$DB_FILE" ".backup '$BACKUP_PATH'"
if [ $? -ne 0 ]; then
    echo "Error: Failed to backup database"
    exit 1
fi

# Compress the backup
gzip -f "$BACKUP_PATH"
COMPRESSED_BACKUP="$BACKUP_PATH.gz"

echo "Database backup created at $COMPRESSED_BACKUP"

# Upload to S3 if enabled
if [ "$S3_ENABLED" = true ]; then
    if [ -z "$S3_BUCKET" ]; then
        echo "Error: S3 bucket name not specified"
        exit 1
    fi
    
    echo "Uploading backup to S3..."
    aws s3 cp "$COMPRESSED_BACKUP" "s3://$S3_BUCKET/$BACKUP_FILENAME.gz"
    
    if [ $? -eq 0 ]; then
        echo "Backup uploaded to s3://$S3_BUCKET/$BACKUP_FILENAME.gz"
    else
        echo "Error: Failed to upload backup to S3"
        exit 1
    fi
fi

# Clean up old backups (keep the last 7 days)
find "$BACKUP_DIR" -name "influencer_db_backup_*.gz" -type f -mtime +7 -delete

echo "Backup process completed successfully" 