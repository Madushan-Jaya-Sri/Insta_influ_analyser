from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def soft_delete(self):
        self.is_deleted = True
        db.session.commit()

    @staticmethod
    def get_by_username(username):
        try:
            return User.query.filter_by(username=username, is_deleted=False).first()
        except Exception as e:
            print(f"Error getting user by username: {str(e)}")
            return None

    @staticmethod
    def get_by_email(email):
        try:
            return User.query.filter_by(email=email, is_deleted=False).first()
        except Exception as e:
            print(f"Error getting user by email: {str(e)}")
            return None

    @staticmethod
    def create_user(username, email, password):
        try:
            if User.get_by_username(username):
                raise ValueError(f"Username '{username}' is already taken")
            if User.get_by_email(email):
                raise ValueError(f"Email '{email}' is already registered")
            
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            # Create default settings for the user
            from app.models.models import UserSettings
            UserSettings.get_or_create(user.id)
            
            return user
        except Exception as e:
            db.session.rollback()
            print(f"Error creating user: {str(e)}")
            raise

    @staticmethod
    def authenticate(username_or_email, password):
        try:
            user = User.get_by_username(username_or_email)
            if not user:
                user = User.get_by_email(username_or_email)
            if user and user.check_password(password):
                return user
            return None
        except Exception as e:
            print(f"Error authenticating user: {str(e)}")
            return None

def init_db(app):
    try:
        db.init_app(app)
        with app.app_context():
            # Import models here to avoid circular imports
            from app.models.models import Influencer, Analysis, UserSettings
            
            # Create all tables
            db.create_all()
            
            # Apply indexes after table creation
            import app.models.indexes
            
            # Create test user if it doesn't exist
            if not User.get_by_username('testuser'):
                User.create_user(
                    username='testuser',
                    email='test@example.com',
                    password='password123'
                )
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise 