"""
Migration script to update history model schema
"""
import os
import sys
from datetime import datetime
from sqlalchemy import inspect

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app context and models
from run import create_app, db
from app.models.history import History, AnalysisImage
from app.models.user import User

def migrate_database():
    # Create app instance
    app = create_app()
    
    # Run within app context
    with app.app_context():
        print("Starting history model migration...")
        
        # Get inspector for checking tables and columns
        inspector = inspect(db.engine)
        
        # Check if tables exist
        history_exists = inspector.has_table('history')
        analysis_image_exists = inspector.has_table('analysis_image')
        
        print(f"History table exists: {history_exists}")
        print(f"AnalysisImage table exists: {analysis_image_exists}")
        
        if not history_exists:
            print("Creating all tables...")
            db.create_all()
            print("Done creating tables.")
            return
        
        if not analysis_image_exists:
            print("Creating AnalysisImage table...")
            # Create just the AnalysisImage table
            AnalysisImage.__table__.create(db.engine)
            print("Created AnalysisImage table.")
        
        # Add new columns to History table if needed
        columns_to_add = [
            ("profile_name", "VARCHAR(255)"),
            ("profile_url", "VARCHAR(255)"),
            ("profile_follower_count", "INTEGER"),
            ("profile_post_count", "INTEGER"),
            ("analysis_complete", "BOOLEAN DEFAULT 1"),
            ("error_message", "TEXT"),
            ("max_posts", "INTEGER"),
            ("time_filter", "VARCHAR(20)")
        ]
        
        print("Checking for missing columns...")
        # Get existing columns
        existing_columns = [col['name'] for col in inspector.get_columns('history')]
        print(f"Existing columns: {existing_columns}")
        
        # Add missing columns
        with db.engine.connect() as conn:
            for column_name, column_type in columns_to_add:
                if column_name.lower() not in [col.lower() for col in existing_columns]:
                    print(f"Adding column {column_name} to History table...")
                    conn.execute(f"ALTER TABLE history ADD COLUMN {column_name} {column_type}")
                    print(f"Added {column_name} column.")
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 