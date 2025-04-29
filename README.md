# Instagram Influencer Analyzer

A web application for analyzing Instagram influencer data, metrics, and engagement patterns.

## Features

- Track influencer engagement metrics
- Analyze follower growth and demographics
- Compare influencer performance
- Generate reports on campaign effectiveness
- Data visualization for key metrics

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (Flask)
- Database: SQLite
- Containerization: Docker
- CI/CD: GitHub Actions
- Deployment: AWS EC2

## Local Development

### Standard Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```
   python scripts/init_db.py
   ```

5. Start the development server:
   ```
   python run.py
   ```

### Docker Setup

1. Make sure Docker and Docker Compose are installed on your machine

2. For development environment:
   ```
   docker-compose -f docker-compose.dev.yml up --build
   ```

3. For production-like environment:
   ```
   docker-compose up --build
   ```

4. Access the application at http://localhost:8000

## Deployment

### Docker Deployment on EC2

1. Set up an EC2 instance with Docker and Docker Compose installed

2. Clone the repository on your EC2 instance:
   ```
   git clone https://github.com/yourusername/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

3. Create a `.env` file with your production settings:
   ```
   FLASK_ENV=production
   SECRET_KEY=your-secure-secret-key
   OPENAI_API_KEY=your-openai-api-key
   APIFY_API_TOKEN=your-apify-token
   ```

4. Deploy using Docker Compose:
   ```
   docker-compose -f docker-compose.prod.yml up -d
   ```

### CI/CD Pipeline

This project includes a CI/CD pipeline using GitHub Actions:

1. CI pipeline runs on all PRs to main/develop branches:
   - Runs tests
   - Checks code quality
   - Reports test coverage

2. CD pipeline runs on pushes to main branch:
   - Builds Docker image
   - Pushes to Docker Hub
   - Deploys to EC2 instance

Required GitHub Secrets for CD:
- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Your Docker Hub access token
- `EC2_HOST`: Your EC2 host IP address
- `EC2_SSH_KEY`: Your EC2 SSH private key
- `APP_SECRET_KEY`: Secret key for Flask
- `OPENAI_API_KEY`: Your OpenAI API key
- `APIFY_API_TOKEN`: Your Apify token

## Database Backups

Database backups are automatically handled in the Docker setup. To manually backup:

```
docker-compose -f docker-compose.prod.yml exec app /bin/bash -c "./backup_db.sh"
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

MIT

## Contact

Email: your.email@example.com 