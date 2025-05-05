#!/usr/bin/env python3
"""
Script to run database migration for Instagram Influencer Analyzer
"""
import os
import sqlite3
from run import create_app

def run_migrations():
    app = create_app()
    with app.app_context():
        # Get the database path from the app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"Using database at: {db_path}")
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='history'")
        if not cursor.fetchone():
            print("Creating history table...")
            cursor.execute('''
            CREATE TABLE history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER NOT NULL,
                profile_username TEXT NOT NULL,
                profile_name TEXT,
                profile_url TEXT,
                profile_follower_count INTEGER,
                profile_post_count INTEGER,
                analysis_results JSON,
                analysis_complete BOOLEAN DEFAULT 1,
                error_message TEXT,
                max_posts INTEGER,
                time_filter TEXT,
                FOREIGN KEY (user_id) REFERENCES user(id)
            )
            ''')
            print("History table created successfully")
        else:
            print("History table already exists")
            
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_image'")
        if not cursor.fetchone():
            print("Creating analysis_image table...")
            cursor.execute('''
            CREATE TABLE analysis_image (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                history_id INTEGER NOT NULL,
                image_type TEXT NOT NULL,
                image_url TEXT,
                image_path TEXT NOT NULL,
                image_data BLOB,
                image_metadata JSON,
                FOREIGN KEY (history_id) REFERENCES history(id) ON DELETE CASCADE
            )
            ''')
            print("Analysis_image table created successfully")
        else:
            print("Analysis_image table already exists")
            
        # Create index for faster queries
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_user_id ON history (user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_image_history_id ON analysis_image (history_id)")
            print("Indexes created successfully")
        except Exception as e:
            print(f"Error creating indexes: {str(e)}")
            
        # Commit changes and close connection
        conn.commit()
        conn.close()
        
        print("Database migrations completed successfully")

if __name__ == '__main__':
    run_migrations() 