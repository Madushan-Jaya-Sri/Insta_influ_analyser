import os
import sys
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from run import create_app
from app.models.database import db, User

def init_db():
    app = create_app()
    with app.app_context():
        # Create database directory if it doesn't exist
        db_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'data')
        os.makedirs(db_dir, exist_ok=True)
        
        # Create all tables
        db.create_all()
        
        # Check for existing file-based users to migrate
        users_json_path = os.path.join(db_dir, 'users.json')
        
        if os.path.exists(users_json_path):
            try:
                # Load existing users from JSON file
                with open(users_json_path, 'r') as f:
                    users_data = json.load(f)
                
                # Migrate each user to the database
                migrated_count = 0
                for user_data in users_data:
                    # Check if user already exists
                    existing_user = User.get_by_username(user_data['username'])
                    if not existing_user:
                        # Create the user in the database
                        user = User(
                            username=user_data['username'], 
                            email=user_data['email'],
                            password_hash=user_data['password_hash']  # Reuse the existing hash
                        )
                        db.session.add(user)
                        migrated_count += 1
                
                if migrated_count > 0:
                    db.session.commit()
                    print(f"Migrated {migrated_count} users from file-based storage to SQLite")
                    
                    # Rename the original file to avoid duplicates
                    os.rename(users_json_path, f"{users_json_path}.bak")
                    print(f"Renamed {users_json_path} to {users_json_path}.bak")
                
            except Exception as e:
                print(f"Error migrating users: {str(e)}")
        
        # Create test user if it doesn't exist
        if not User.get_by_username('testuser'):
            User.create_user(
                username='testuser',
                email='test@example.com',
                password='password123'
            )
            print("Created test user: testuser / password123")

if __name__ == '__main__':
    init_db() 