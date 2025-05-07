"""
Database initialization and configuration module.
This module provides a central location for database setup to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize extensions without app context
db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with the Flask app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all() 