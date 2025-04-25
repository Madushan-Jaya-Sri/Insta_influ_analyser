# Deployment Guide for Instagram Influencer Analyzer

This guide explains how to deploy the application to an EC2 instance using Docker and GitHub Actions.

## Prerequisites

1. An AWS EC2 instance with a public IP address (13.126.220.175 in this case)
2. GitHub repository with the following secrets configured:
   - `AWS_HOST`: Your EC2 public IP address
   - `AWS_USERNAME`: SSH username for your EC2 instance (usually 'ubuntu' or 'ec2-user')
   - `AWS_SSH_KEY`: Private SSH key for connecting to your EC2 instance
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `APIFY_API_TOKEN`: Your Apify API token
   - `SECRET_KEY`: Application secret key

## Manual Deployment

If you want to deploy manually instead of using GitHub Actions:

1. Connect to your EC2 instance:
   ```
   ssh -i your-key.pem ubuntu@13.126.220.175
   ```

2. Clone the repository:
   ```
   git clone https://github.com/yourusername/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

3. Run the setup script:
   ```
   chmod +x scripts/setup_ec2.sh
   ./scripts/setup_ec2.sh
   ```

4. Create a `.env` file with your credentials:
   ```
   FLASK_ENV=production
   SECRET_KEY="your-secret-key"
   OPENAI_API_KEY="your-openai-api-key"
   APIFY_API_TOKEN="your-apify-api-token"
   APIFY_TOKEN="your-apify-token"
   ```

5. Run the deployment script:
   ```
   chmod +x scripts/deploy_to_ec2.sh
   ./scripts/deploy_to_ec2.sh
   ```

## Automated Deployment with GitHub Actions

1. Push changes to the `main` or `master` branch to trigger automatic deployment
2. The GitHub Actions workflow will:
   - Copy your environment variables to the EC2 instance
   - Pull the latest code
   - Build and run the Docker containers

## Accessing the Application

After deployment, the application will be available at:
```
http://13.126.220.175
```

## Troubleshooting

### Check Container Status

```
docker ps
docker logs insta_influ_analyser_app_1
```

### Restart Containers

```
cd ~/Insta_influ_analyser
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

### Check Nginx Configuration

```
docker exec -it insta_influ_analyser_nginx_1 nginx -t
``` 