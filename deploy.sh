#!/bin/bash
# Deployment script for Instagram Influencer Analyzer
# Usage:
#   ./deploy.sh                  - normal deployment
#   CLEAN_DB=true ./deploy.sh    - deploy with database reset
#   CLEAN_DATA=true ./deploy.sh  - deploy with all data files removed

set -e

echo "=== Instagram Influencer Analyzer Deployment Tool ==="

# Run cleanup script to remove temporary files
echo "Cleaning up temporary files..."
if [ "$CLEAN_DATA" = "true" ]; then
  echo "CLEAN_DATA=true: Removing all data files (DB and JSON)..."
  ./cleanup.sh --data
elif [ "$CLEAN_DB" = "true" ]; then
  echo "CLEAN_DB=true: Resetting database..."
  ./cleanup.sh --db
else
  ./cleanup.sh
fi

# Run root cleanup to organize files
echo "Organizing project structure..."
./cleanup.sh --root

# Push changes to GitHub to trigger CI/CD
echo "Committing and pushing changes to GitHub..."

# Check if there are any changes to commit
if [ -n "$(git status --porcelain)" ]; then
  echo "Changes detected, committing..."
  
  # Add all changes
  git add .
  
  # Commit with timestamp
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
  COMMIT_MSG="Deployment update $TIMESTAMP"
  
  # Add information about the cleanup performed
  if [ "$CLEAN_DATA" = "true" ]; then
    COMMIT_MSG="$COMMIT_MSG (with all data removed)"
  elif [ "$CLEAN_DB" = "true" ]; then
    COMMIT_MSG="$COMMIT_MSG (with DB reset)"
  fi
  
  git commit -m "$COMMIT_MSG"
  
  # Push to GitHub
  git push origin main
  
  echo "Changes pushed to GitHub."
  echo "CI/CD pipeline has been triggered."
  
  # Print message about cleanup if enabled
  if [ "$CLEAN_DATA" = "true" ]; then
    echo "All data files will be removed during deployment (CLEAN_DATA=true)."
  elif [ "$CLEAN_DB" = "true" ]; then
    echo "Database will be reset during deployment (CLEAN_DB=true)."
  fi
  
  echo "Deployment will be completed in a few minutes."
  echo "You can check the progress on GitHub Actions."
else
  echo "No changes to commit. Skipping deployment."
fi

echo "Deployment process completed locally." 