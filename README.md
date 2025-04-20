# Instagram Influencer Analyzer

A powerful tool for analyzing Instagram influencer profiles and their content using data science and AI. Created by Momentro.

## Features

- Upload Instagram data files or analyze profiles by URL
- Analyze engagement metrics, content, and audience insights
- Generate beautiful visualizations of influencer performance
- Identify trends and patterns across multiple influencers
- AI-powered content analysis for deeper insights

## Local Development

### Prerequisites

- Python 3.9+
- pip
- Virtual environment (recommended)

### Setup

1. Clone the repository
```bash
git clone https://github.com/your-username/Insta_influ_analyser.git
cd Insta_influ_analyser
```

2. Create and activate a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env  # And then edit the .env file with your credentials
```

5. Run the application
```bash
python app.py
```

The application will be available at http://localhost:5000

## Docker Deployment

### Local Docker Deployment

1. Prerequisites
   - Docker and Docker Compose installed

2. Build and run with Docker Compose
```bash
# For development
docker-compose -f docker-compose.dev.yml up -d

# For production (with Nginx)
docker-compose up -d
```

3. Access the application
   - Development: http://localhost:5000
   - Production: http://localhost

### Production Deployment

For detailed instructions on deploying to production environments, see:

- [Docker Deployment Guide](DOCKER-DEPLOYMENT.md)
- [EC2 Deployment Guide](EC2-DEPLOYMENT.md) 
- [CI/CD Pipeline Guide](CICD.md)

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment. See [CICD.md](CICD.md) for details.

## API Documentation

The application provides a REST API for accessing influencer data programmatically. See [API.md](API.md) for details.

## License

© 2025 Momentro. All rights reserved. 