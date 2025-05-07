"""
Database initialization module to prevent circular imports.
"""

import os
import logging
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
        try:
            # Check if database file exists and has proper permissions
            db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
            if db_path.startswith('/'):
                # Absolute path
                if not os.path.exists(os.path.dirname(db_path)):
                    os.makedirs(os.path.dirname(db_path), exist_ok=True)
                
                # Make sure db file can be written
                if os.path.exists(db_path):
                    os.chmod(db_path, 0o666)
            
            # Import all models to ensure they're registered with SQLAlchemy
            from app.models.user import User
            try:
                from app.models.profile import Profile
            except ImportError:
                app.logger.warning("Profile model not found")
            
            try:
                from app.models.post import Post
            except ImportError:
                app.logger.warning("Post model not found")
                
            try:
                from app.models.analysis import Analysis
            except ImportError:
                app.logger.warning("Analysis model not found")
                
            try:
                from app.models.history import History
            except ImportError:
                app.logger.warning("History model not found")
            
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            app.logger.info(f"Tables before create_all: {tables}")
            
            if 'user' not in tables:
                app.logger.info("Creating database tables...")
                db.create_all()
                app.logger.info("Database tables created successfully")
                
            # Verify tables were created
            tables = inspector.get_table_names()
            app.logger.info(f"Tables after create_all: {tables}")
            
            if 'user' not in tables:
                app.logger.error("Failed to create 'user' table!")
                
        except Exception as e:
            app.logger.error(f"Error initializing database: {str(e)}")
            import traceback
            app.logger.error(traceback.format_exc()) 