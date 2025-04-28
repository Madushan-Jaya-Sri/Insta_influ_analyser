#!/bin/bash

# SQLite-based authentication fix
set -e

echo "=== IMPLEMENTING SQLITE AUTHENTICATION FIX ==="

# Create a new user model with SQLite
cat > ~/Insta_influ_analyser/app/models/user.py << 'EOF'
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from pathlib import Path

class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def get_db():
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'users.db')
        Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(db_path)

    @staticmethod
    def init_db():
        conn = User.get_db()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(user_id):
        conn = User.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data:
            return User(*user_data)
        return None

    @staticmethod
    def get_by_username(username):
        conn = User.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data:
            return User(*user_data)
        return None

    @staticmethod
    def get_by_email(email):
        conn = User.get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE email = ?', (email,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data:
            return User(*user_data)
        return None

    @staticmethod
    def create_user(username, email, password):
        if User.get_by_username(username):
            raise ValueError(f"Username '{username}' is already taken")
        
        if User.get_by_email(email):
            raise ValueError(f"Email '{email}' is already registered")

        user_id = str(os.urandom(16).hex())
        password_hash = generate_password_hash(password)
        
        conn = User.get_db()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, email, password_hash))
        conn.commit()
        conn.close()
        
        return User(user_id, username, email, password_hash)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def authenticate(username_or_email, password):
        user = User.get_by_username(username_or_email)
        if not user:
            user = User.get_by_email(username_or_email)
        
        if user and user.check_password(password):
            return user
        return None

# Initialize the database
User.init_db()

# Create test user if it doesn't exist
if not User.get_by_username('testuser'):
    User.create_user(
        username='testuser',
        email='test@example.com',
        password='password123'
    )
EOF

# Create a new auth routes file
cat > ~/Insta_influ_analyser/app/routes/auth.py << 'EOF'
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from app.models.forms import LoginForm, RegistrationForm
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.authenticate(form.username.data, form.password.data)
        if user:
            login_user(user, remember=True)
            session['user_id'] = user.id
            session.permanent = True
            session.modified = True
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            user = User.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            login_user(user, remember=True)
            session['user_id'] = user.id
            session.permanent = True
            session.modified = True
            flash(f'Account created successfully. Welcome, {user.username}!', 'success')
            return redirect(url_for('main.dashboard'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/quick-login')
def quick_login():
    """Quick login without form"""
    user = User.get_by_username('testuser')
    if user:
        login_user(user, remember=True)
        session['user_id'] = user.id
        session.permanent = True
        session.modified = True
        flash('Quick login successful!', 'success')
        return redirect(url_for('main.dashboard'))
    else:
        flash('Test user not found', 'danger')
        return redirect(url_for('main.index'))
EOF

# Update docker-compose file
cat > ~/Insta_influ_analyser/docker-compose.prod.yml << 'EOF'
services:
  app:
    build: .
    restart: always
    container_name: flask_app
    user: "root"
    expose:
      - "5000"
    volumes:
      - ./uploads:/app/uploads
      - ./static:/app/static
      - ./app/static:/app/app/static
      - ./app/data:/app/app/data
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    networks:
      - app_network

  nginx:
    image: nginx:1.25-alpine
    restart: always
    container_name: nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./uploads:/app/uploads
      - ./static:/app/static
      - ./app/static:/app/app/static
    depends_on:
      - app
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
EOF

# Create data directory
mkdir -p ~/Insta_influ_analyser/app/data

# Set permissions
chmod -R 777 ~/Insta_influ_analyser/app/data

# Copy files to container
docker cp ~/Insta_influ_analyser/app/models/user.py flask_app:/app/app/models/user.py
docker cp ~/Insta_influ_analyser/app/routes/auth.py flask_app:/app/app/routes/auth.py

# Restart container
docker restart flask_app
sleep 5

echo "=== SQLITE AUTHENTICATION FIX COMPLETED ==="
echo "The registration and login should now work properly using SQLite database."
echo "Test user credentials:"
echo "Username: testuser"
echo "Password: password123"
echo "Quick login URL: http://13.126.220.175/auth/quick-login"
echo "Check logs with: docker logs flask_app" 