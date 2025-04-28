#!/bin/bash

# Complete SQLite migration script
set -e

echo "=== STARTING COMPLETE SQLITE MIGRATION ==="

# Create database directory with proper permissions
sudo mkdir -p ~/Insta_influ_analyser/app/data
sudo chown -R ubuntu:ubuntu ~/Insta_influ_analyser/app/data
sudo chmod -R 755 ~/Insta_influ_analyser/app/data

# Create database file
touch ~/Insta_influ_analyser/app/data/app.db
sudo chown ubuntu:ubuntu ~/Insta_influ_analyser/app/data/app.db
sudo chmod 644 ~/Insta_influ_analyser/app/data/app.db

# Create forms
cat > ~/Insta_influ_analyser/app/models/forms.py << 'EOF'
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.database import User

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Username must be between 3 and 20 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(message='Please enter a valid email address')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.get_by_username(username.data)
        if user:
            raise ValidationError('Username is already taken')

    def validate_email(self, email):
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError('Email is already registered')
EOF

# Create new database models
cat > ~/Insta_influ_analyser/app/models/database.py << 'EOF'
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

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def get_by_username(username):
        try:
            return User.query.filter_by(username=username).first()
        except Exception as e:
            print(f"Error getting user by username: {str(e)}")
            return None

    @staticmethod
    def get_by_email(email):
        try:
            return User.query.filter_by(email=email).first()
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

class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    username = db.Column(db.String(80), nullable=False)
    followers = db.Column(db.Integer)
    following = db.Column(db.Integer)
    posts = db.Column(db.Integer)
    engagement_rate = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('analyses', lazy=True))

def init_db(app):
    try:
        db.init_app(app)
        with app.app_context():
            db.create_all()
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
EOF

# Create new auth routes
cat > ~/Insta_influ_analyser/app/routes/auth.py << 'EOF'
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user
from app.models.forms import LoginForm, RegistrationForm
from app.models.database import User, db
from app.utils.security import csrf_protect

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
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
        except Exception as e:
            flash('An error occurred during login', 'danger')
            current_app.logger.error(f"Login error: {str(e)}")
    
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
            flash('An error occurred during registration', 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        session.clear()
        flash('You have been logged out.', 'info')
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
    return redirect(url_for('main.index'))

@auth_bp.route('/quick-login')
def quick_login():
    """Quick login without form"""
    try:
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
    except Exception as e:
        flash('An error occurred during quick login', 'danger')
        current_app.logger.error(f"Quick login error: {str(e)}")
    return redirect(url_for('main.index'))
EOF

# Create security utilities
cat > ~/Insta_influ_analyser/app/utils/security.py << 'EOF'
from functools import wraps
from flask import request, abort
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def csrf_protect(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get('csrf_token')
            if not token or not csrf._verify_token(token):
                abort(403)
        return f(*args, **kwargs)
    return decorated_function
EOF

# Update main routes to use SQLite
cat > ~/Insta_influ_analyser/app/routes/main.py << 'EOF'
from flask import (
    Blueprint, render_template, request, flash, redirect, url_for,
    current_app, session
)
from flask_login import login_required, current_user
from app.models.database import Analysis, db
from app.utils.instagram import get_user_data
from app.utils.security import csrf_protect
import json

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    try:
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
        return render_template('dashboard.html', analyses=analyses)
    except Exception as e:
        current_app.logger.error(f"Dashboard error: {str(e)}")
        flash('An error occurred while loading the dashboard', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/analyze', methods=['GET', 'POST'])
@login_required
@csrf_protect
def analyze():
    if request.method == 'POST':
        username = request.form.get('username')
        if not username:
            flash('Please enter a username', 'danger')
            return redirect(url_for('main.analyze'))
        
        try:
            data = get_user_data(username)
            if not data:
                flash('Could not fetch user data', 'danger')
                return redirect(url_for('main.analyze'))
            
            analysis = Analysis(
                user_id=current_user.id,
                username=username,
                followers=data.get('followers', 0),
                following=data.get('following', 0),
                posts=data.get('posts', 0),
                engagement_rate=data.get('engagement_rate', 0)
            )
            db.session.add(analysis)
            db.session.commit()
            
            flash('Analysis completed successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Analysis error: {str(e)}")
            flash('An error occurred during analysis', 'danger')
            return redirect(url_for('main.analyze'))
    
    return render_template('analyze.html')

@main_bp.route('/history')
@login_required
def history():
    try:
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
        return render_template('history.html', analyses=analyses)
    except Exception as e:
        current_app.logger.error(f"History error: {str(e)}")
        flash('An error occurred while loading history', 'danger')
        return redirect(url_for('main.dashboard'))
EOF

# Update app configuration
cat > ~/Insta_influ_analyser/app/__init__.py << 'EOF'
from flask import Flask
from flask_login import LoginManager
from app.models.database import db, init_db
from app.routes.auth import auth_bp
from app.routes.main import main_bp
from app.utils.security import csrf
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Initialize extensions
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        try:
            from app.models.database import User
            return User.query.get(int(user_id))
        except Exception as e:
            app.logger.error(f"Error loading user: {str(e)}")
            return None

    # Initialize database
    init_db(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
EOF

# Update requirements.txt
cat > ~/Insta_influ_analyser/requirements.txt << 'EOF'
Flask==2.0.1
Flask-Login==0.5.0
Flask-SQLAlchemy==2.5.1
Flask-WTF==1.0.0
Werkzeug==2.0.1
gunicorn==20.1.0
requests==2.26.0
python-dotenv==0.19.0
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
      - ./app/data:/app/app/data
      - ./static:/app/static
      - ./app/static:/app/app/static
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
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

# Set permissions inside container
docker exec flask_app chown -R root:root /app/app/data
docker exec flask_app chmod -R 755 /app/app/data

# Restart containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d

echo "=== SQLITE MIGRATION COMPLETED ==="
echo "The application has been migrated to use SQLite for all data storage."
echo "Test user credentials:"
echo "Username: testuser"
echo "Password: password123"
echo "Quick login URL: http://13.126.220.175/auth/quick-login"
echo "Check logs with: docker logs flask_app" 