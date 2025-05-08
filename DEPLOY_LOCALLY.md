# Local Deployment Guide

This guide explains how to deploy the Instagram Influencer Analyzer application locally using Docker.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Deployment Steps

1. **Clone the repository:**

```bash
git clone https://github.com/madushan-jaya-sri/Insta_influ_analyser.git
cd Insta_influ_analyser
```

2. **Create persistent data directories:**

```bash
mkdir -p ./app/static/images/brand
mkdir -p ./app/uploads
mkdir -p ./app/data
mkdir -p ./logs
```

3. **Ensure the centralized database module is set up correctly:**

Create `app/database.py` with the following content:

```python
"""Database initialization module to prevent circular imports."""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with Flask app."""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create all tables
    with app.app_context():
        db.create_all()
```

4. **Fix any circular imports in auth.py (if needed):**

If you see circular import errors, edit `app/routes/auth.py` and change:

```python
from run import db
```

to:

```python
from app.database import db
```

5. **Build and run with Docker Compose:**

```bash
docker-compose build --no-cache
docker-compose up -d
```

6. **Access the Application:**

Open your browser and navigate to:

```
http://localhost:8000
```

## Troubleshooting

### If containers fail to start:

Check logs with:

```bash
docker-compose logs
```

### If you encounter circular import errors:

Run the fix script:

```bash
bash fix_auth.sh
```

### To restart the application:

```bash
docker-compose restart
```

### To completely reset (including removing containers):

```bash
docker-compose down
docker-compose up -d
```

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Flask Configuration
FLASK_APP=app
FLASK_ENV=production
FLASK_DEBUG=0

# Security - CHANGE IN PRODUCTION
SECRET_KEY=super-secret-key-please-change-in-prod

# Database Configuration
DATABASE_URL=sqlite:///app.db

# Logging
LOG_LEVEL=INFO
``` 