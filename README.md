# Instagram Influencer Analyzer

A tool for analyzing Instagram influencer profiles and engagement metrics, developed by Momentro.

## Features

- Analyze Instagram influencers based on profile URLs or data files
- Calculate engagement metrics and visualize trends
- Generate content analysis and audience insights
- Display detailed dashboards for each influencer

## Deployment with Docker on EC2

### Prerequisites

- An EC2 instance running Ubuntu
- SSH access to the EC2 instance
- GitHub repository for the project
- Docker and Docker Compose installed on the EC2 instance

### Setting Up the EC2 Instance

1. SSH into your EC2 instance:
   ```bash
   ssh -i /path/to/your/key.pem ubuntu@65.0.181.3
   ```

2. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

3. Run the setup script:
   ```bash
   chmod +x deploy_ec2.sh
   ./deploy_ec2.sh
   ```

4. Create a `.env` file with your API keys:
   ```bash
   cp .env.example .env
   nano .env
   ```
   Update with your actual API keys for OpenAI and Apify.

### Manual Deployment

1. Build and start Docker containers:
   ```bash
   docker-compose up --build -d
   ```

2. Check if the application is running:
   ```bash
   docker-compose ps
   ```

3. View logs if needed:
   ```bash
   docker-compose logs -f
   ```

### CI/CD with GitHub Actions

To set up automatic deployment with GitHub Actions:

1. Add the following secrets to your GitHub repository:
   - `AWS_SSH_KEY`: Your EC2 SSH private key (contents of the .pem file)
   - `AWS_HOST`: Your EC2 instance hostname or IP (e.g., 65.0.181.3)
   - `AWS_USERNAME`: Your EC2 username (e.g., ubuntu)
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `APIFY_API_TOKEN`: Your Apify API token
   - `SECRET_KEY`: A secure random string for Flask

2. Push to the main branch to trigger deployment, or manually trigger the workflow from the GitHub Actions tab.

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file with your API keys
   ```

3. Run the application:
   ```bash
   python app.py
   ```

## License

© 2025 Momentro. All rights reserved. 