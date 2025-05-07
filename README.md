# Instagram Influencer Analyzer

A Flask-based web application for analyzing Instagram influencer profiles and generating insights.

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/madushan-jaya-sri/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python run.py
   ```

5. Access the application at [http://localhost:8001](http://localhost:8001)

## Docker Deployment

1. Build and run using Docker Compose:
   ```bash
   docker-compose up -d --build
   ```

2. Access the application at [http://localhost:8000](http://localhost:8000)

## CI/CD Deployment

The application uses GitHub Actions for continuous deployment to AWS EC2:

1. Push changes to the main branch:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

2. GitHub Actions will automatically deploy the changes to the configured EC2 instance.

## Project Structure

```
.
├── app/                      # Main application package
│   ├── database.py           # Centralized database module
│   ├── __init__.py           # Application factory
│   ├── forms.py              # Form definitions
│   ├── models/               # Database models
│   ├── routes/               # Route blueprints
│   ├── static/               # Static files
│   ├── templates/            # HTML templates
│   └── utils/                # Utility functions
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Development entry point
└── wsgi.py                   # Production WSGI entry point
```

## Troubleshooting

If you encounter any circular import issues during deployment, run the fix script:

```bash
chmod +x fix_deployment.sh
./fix_deployment.sh
```

## Environment Variables

Create a `.env` file with the following variables:

```
# Flask Configuration
FLASK_APP=app
FLASK_ENV=development  # Use 'production' for deployment
FLASK_DEBUG=1  # Set to 0 in production

# Security
SECRET_KEY=your-secret-key

# Database Configuration
DATABASE_URL=sqlite:///app.db  # Use a different database in production

# Application Configuration
LOG_SESSIONS=false
``` 