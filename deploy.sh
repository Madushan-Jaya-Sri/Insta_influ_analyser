#!/bin/bash
# Deployment script for Instagram Influencer Analyzer
# Usage:
#   ./deploy.sh           - normal deployment
#   CLEAN_DB=true ./deploy.sh - deploy with database reset

set -e

echo "=== Instagram Influencer Analyzer Deployment Tool ==="

# Run cleanup script to remove temporary files
echo "Cleaning up temporary files..."
./cleanup.sh

# Push changes to GitHub to trigger CI/CD
echo "Committing and pushing changes to GitHub..."

# Check if there are any changes to commit
if [ -n "$(git status --porcelain)" ]; then
  echo "Changes detected, committing..."
  
  # Add all changes
  git add .
  
  # Commit with timestamp
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
  git commit -m "Deployment update $TIMESTAMP"
  
  # Push to GitHub
  git push origin main
  
  echo "Changes pushed to GitHub."
  echo "CI/CD pipeline has been triggered."
  
  # Print message about database reset if CLEAN_DB is set
  if [ "$CLEAN_DB" = "true" ]; then
    echo "Database will be reset during deployment (CLEAN_DB=true)."
  fi
  
  echo "Deployment will be completed in a few minutes."
  echo "You can check the progress on GitHub Actions."
else
  echo "No changes to commit. Skipping deployment."
fi

echo "Deployment process completed locally." 