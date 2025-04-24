from flask_login import UserMixin
import os
import json
import uuid
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash

# User data file path
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_DATA_PATH = os.path.join(APP_ROOT, 'data', 'users.json')

class User(UserMixin):
    """Simple User class for authentication"""
    
    # Dictionary to store user objects in memory
    _users = {}
    
    def __init__(self, user_id, username, email, password_hash):
        self.id = user_id  # Required by Flask-Login
        self.username = username
        self.email = email
        self.password_hash = password_hash
    
    @staticmethod
    def load_users():
        """Load users from the JSON file"""
        if os.path.exists(USERS_DATA_PATH):
            try:
                with open(USERS_DATA_PATH, 'r') as f:
                    users_data = json.load(f)
                    
                User._users = {}
                for user_data in users_data:
                    user = User(
                        user_id=user_data['id'],
                        username=user_data['username'],
                        email=user_data['email'],
                        password_hash=user_data['password_hash']
                    )
                    User._users[user.id] = user
                    
                print(f"Loaded {len(User._users)} users from {USERS_DATA_PATH}")
            except Exception as e:
                print(f"Error loading users from {USERS_DATA_PATH}: {e}")
                User._users = {}
        else:
            print(f"Users file not found: {USERS_DATA_PATH}")
            User._users = {}
    
    @staticmethod
    def save_users():
        """Save users to the JSON file"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(USERS_DATA_PATH), exist_ok=True)
            
            users_data = []
            for user in User._users.values():
                users_data.append({
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password_hash': user.password_hash
                })
                
            with open(USERS_DATA_PATH, 'w') as f:
                json.dump(users_data, f, indent=4)
                
            print(f"Saved {len(User._users)} users to {USERS_DATA_PATH}")
        except Exception as e:
            print(f"Error saving users to {USERS_DATA_PATH}: {e}")
    
    @staticmethod
    def get_by_id(user_id):
        """Get a user by ID - required by Flask-Login"""
        return User._users.get(user_id)
    
    @staticmethod
    def get_by_username(username):
        """Get a user by username"""
        for user in User._users.values():
            if user.username.lower() == username.lower():
                return user
        return None
    
    @staticmethod
    def get_by_email(email):
        """Get a user by email"""
        for user in User._users.values():
            if user.email.lower() == email.lower():
                return user
        return None
    
    @staticmethod
    def create_user(username, email, password):
        """Create a new user"""
        # Check if username or email already exists
        if User.get_by_username(username):
            raise ValueError(f"Username '{username}' is already taken")
        
        if User.get_by_email(email):
            raise ValueError(f"Email '{email}' is already registered")
        
        # Create the user
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            password_hash=password_hash
        )
        
        # Add to users dictionary
        User._users[user_id] = user
        
        # Save the updated users
        User.save_users()
        
        return user
    
    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def authenticate(username_or_email, password):
        """Authenticate a user by username/email and password"""
        # Try to get the user by username
        user = User.get_by_username(username_or_email)
        
        # If not found by username, try email
        if not user:
            user = User.get_by_email(username_or_email)
        
        # If user exists and password is correct
        if user and user.check_password(password):
            return user
        
        return None

# Load users when module is imported
User.load_users() 