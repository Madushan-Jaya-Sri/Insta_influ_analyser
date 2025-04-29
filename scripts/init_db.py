import os
import sys
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