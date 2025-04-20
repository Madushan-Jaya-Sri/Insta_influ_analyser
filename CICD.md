# CI/CD Pipeline with GitHub Actions

This guide explains how to set up a CI/CD pipeline for the Instagram Influencer Analyzer using GitHub Actions to automatically deploy to AWS EC2.

## Prerequisites

- GitHub repository containing your application code
- AWS EC2 instance set up (see [EC2-DEPLOYMENT.md](EC2-DEPLOYMENT.md))
- IAM user with appropriate permissions for deployment

## Overview of the CI/CD Pipeline

1. **Continuous Integration**: Every push to the repository will trigger automated tests
2. **Continuous Deployment**: Successful pushes to the main branch will be automatically deployed to EC2

## Step 1: Set Up GitHub Secrets

You'll need to store sensitive information as GitHub Secrets to use in your workflows:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Add the following secrets:
   - `AWS_SSH_KEY`: Your private SSH key (the content of your .pem file)
   - `AWS_HOST`: Your EC2 instance public IP or hostname
   - `AWS_USERNAME`: The username for SSH (e.g., ec2-user, ubuntu)
   - `OPENAI_API_KEY`: Your OpenAI API key (if applicable)
   - `APIFY_API_TOKEN`: Your Apify API token (if applicable)

## Step 2: Create GitHub Actions Workflow Files

Create a directory in your repository for GitHub Actions workflows:

```bash
mkdir -p .github/workflows
```

### CI Workflow

Create a file named `.github/workflows/ci.yml` for testing:

```yaml
name: CI - Test Application

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
        pip install pytest pytest-flask
        
    - name: Lint with flake8
      run: |
        pip install flake8
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Test with pytest
      run: |
        pytest -v
```

### CD Workflow

Create a file named `.github/workflows/cd.yml` for deployment:

```yaml
name: CD - Deploy to EC2

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install SSH key
      uses: shimataro/ssh-key-action@v2
      with:
        key: ${{ secrets.AWS_SSH_KEY }}
        known_hosts: 'just-a-placeholder-so-we-dont-get-errors'
        
    - name: Add to known_hosts
      run: ssh-keyscan -H ${{ secrets.AWS_HOST }} >> ~/.ssh/known_hosts
        
    - name: Deploy to EC2
      run: |
        ssh ${{ secrets.AWS_USERNAME }}@${{ secrets.AWS_HOST }} "
          cd ~/Insta_influ_analyser &&
          git pull &&
          source venv/bin/activate &&
          pip install -r requirements.txt &&
          sudo systemctl restart insta-analyzer
        "
        
    - name: Verify Deployment
      run: |
        echo "Deployment complete! Verifying service status..."
        ssh ${{ secrets.AWS_USERNAME }}@${{ secrets.AWS_HOST }} "sudo systemctl status insta-analyzer"
```

## Step 3: Create a Basic Test File

For the CI pipeline to work, you'll need at least a simple test file. Create a file named `test_app.py` in your repository:

```python
import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
```

## Step 4: Initial Push to GitHub

Push these changes to your GitHub repository:

```bash
git add .github/
git add test_app.py
git commit -m "Add CI/CD pipeline configuration"
git push
```

## Step 5: Set Up EC2 for Automated Deployments

On your EC2 instance, ensure Git is configured to avoid prompts during pulls:

```bash
git config --global pull.rebase false
```

Also make sure your repository directory has appropriate permissions:

```bash
chmod -R 755 ~/Insta_influ_analyser
```

## Step 6: Monitor Workflow Runs

1. Go to your GitHub repository
2. Click on "Actions" tab
3. You should see your workflows running after each push

## Advanced CI/CD Improvements

Once your basic CI/CD pipeline is working, consider these enhancements:

### 1. Environment Separation

Modify your workflows to deploy to different environments based on branches:
- `develop` branch → staging server
- `main` branch → production server

### 2. Database Migrations

If your application uses a database, include migration steps in your deployment:

```yaml
- name: Deploy to EC2
  run: |
    ssh ${{ secrets.AWS_USERNAME }}@${{ secrets.AWS_HOST }} "
      cd ~/Insta_influ_analyser &&
      git pull &&
      source venv/bin/activate &&
      pip install -r requirements.txt &&
      flask db upgrade &&
      sudo systemctl restart insta-analyzer
    "
```

### 3. Automatic Rollbacks

Add logic to roll back deployments if health checks fail:

```yaml
- name: Health Check
  id: health_check
  run: |
    for i in {1..5}; do
      response=$(curl -s -o /dev/null -w "%{http_code}" http://${{ secrets.AWS_HOST }})
      if [ "$response" == "200" ]; then
        echo "Health check passed!"
        exit 0
      fi
      echo "Waiting for service to start... attempt $i"
      sleep 10
    done
    echo "Health check failed after 5 attempts"
    exit 1
  continue-on-error: true

- name: Rollback if Failed
  if: steps.health_check.outcome == 'failure'
  run: |
    ssh ${{ secrets.AWS_USERNAME }}@${{ secrets.AWS_HOST }} "
      cd ~/Insta_influ_analyser &&
      git reset --hard HEAD~1 &&
      sudo systemctl restart insta-analyzer
    "
```

### 4. Slack or Email Notifications

Add notifications to alert your team about deployment status:

```yaml
- name: Slack Notification
  uses: rtCamp/action-slack-notify@v2
  env:
    SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
    SLACK_CHANNEL: deployments
    SLACK_COLOR: ${{ job.status }}
    SLACK_ICON: https://github.com/rtCamp.png?size=48
    SLACK_MESSAGE: 'Deployment ${{ job.status }} :rocket:'
    SLACK_TITLE: Deployment Status
    SLACK_USERNAME: GitHub Actions
```

## Troubleshooting Common Issues

- **Permission Denied**: Ensure your SSH key is correctly added to GitHub Secrets
- **Failed Git Pull**: If local changes exist on the server, you might need to add `git reset --hard origin/main` before `git pull`
- **Service Fails to Start**: Check logs with `sudo journalctl -u insta-analyzer`

## Monitoring Your Pipeline

Set up monitoring to track deployment performance:

1. Use GitHub Actions timing metrics to identify slow steps
2. Add performance testing to your CI pipeline
3. Use AWS CloudWatch to monitor EC2 health and performance

## Conclusion

With this CI/CD pipeline in place, your code will be automatically tested and deployed whenever changes are pushed to the main branch. This ensures consistent, reliable deployments and reduces manual intervention. 