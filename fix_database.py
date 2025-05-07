#!/usr/bin/env python3
"""
Database fix script - run this if you encounter 'no such table' errors.
This script will create all necessary database tables by directly using SQLAlchemy.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("database_fix.log")
    ]
)

logger = logging.getLogger("database_fix")

def fix_database():
    """Create all database tables directly."""
    try:
        # First, check if app.db exists and has proper permissions
        if os.path.exists("app.db"):
            logger.info("Found existing app.db file, setting permissions to 666")
            os.chmod("app.db", 0o666)
        else:
            logger.info("app.db not found, it will be created")
            with open("app.db", "w") as f:
                pass
            os.chmod("app.db", 0o666)
            
        # Now import Flask app and create the tables
        from app import create_app
        from app.database import db
        
        # Import all models to ensure they're registered
        from app.models.user import User
        try:
            from app.models.profile import Profile
            logger.info("Imported Profile model")
        except ImportError:
            logger.warning("Profile model not found or not needed")
        
        try:
            from app.models.post import Post
            logger.info("Imported Post model")
        except ImportError:
            logger.warning("Post model not found or not needed")
            
        try:
            from app.models.analysis import Analysis
            logger.info("Imported Analysis model")
        except ImportError:
            logger.warning("Analysis model not found or not needed")
            
        try:
            from app.models.history import History
            logger.info("Imported History model")
        except ImportError:
            logger.warning("History model not found or not needed")
        
        app = create_app()
        logger.info("Created Flask app instance")
        
        with app.app_context():
            # Check if tables exist before creating
            logger.info("Checking database table status")
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"Existing tables: {existing_tables}")
            
            if 'user' not in existing_tables:
                logger.info("Creating all database tables...")
                db.create_all()
                logger.info("Tables created successfully")
                
                # Verify tables were created
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()
                logger.info(f"Tables after create_all: {tables}")
                
                if 'user' in tables:
                    logger.info("SUCCESS: User table was created")
                else:
                    logger.error("FAILED: User table was not created")
            else:
                logger.info("User table already exists, no action needed")
                
            return True
    except Exception as e:
        logger.error(f"Error fixing database: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting database fix script")
    if fix_database():
        logger.info("Database fix completed successfully")
        sys.exit(0)
    else:
        logger.error("Database fix failed")
        sys.exit(1) 