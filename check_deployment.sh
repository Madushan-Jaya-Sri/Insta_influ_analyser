#!/bin/bash

# Instagram Influencer Analyzer Deployment Status Check Script
# This script checks the status of the deployed application on the EC2 instance

# Configuration variables
EC2_HOST="13.126.220.175"
EC2_USER="ubuntu"
SSH_KEY_PATH="$HOME/.ssh/insta_analyzer_key.pem"

# Check if key file exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key not found at $SSH_KEY_PATH"
    exit 1
fi

# Ensure SSH key has correct permissions
chmod 400 "$SSH_KEY_PATH"

echo "===== Checking Deployment Status ====="

# Connect to EC2 and check service status
echo "Checking service status..."
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" "sudo systemctl status insta_analyzer.service | head -20"

echo
echo "Checking Nginx status..."
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" "sudo systemctl status nginx | head -20"

echo
echo "Checking application logs..."
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" "sudo journalctl -u insta_analyzer.service -n 50 --no-pager"

echo
echo "Checking open ports..."
ssh -i "$SSH_KEY_PATH" "$EC2_USER@$EC2_HOST" "sudo ss -tunlp | grep -E ':(80|8000)'"

echo
echo "===== Status Check Complete ====="
echo "Application URL: http://$EC2_HOST" 