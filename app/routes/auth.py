from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user
import os
import json
from functools import wraps  # For restricting debug endpoint

from app.models.forms import LoginForm, RegistrationForm
from app.models.user import User, USERS_DATA_PATH

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Restrict debug endpoint to specific IPs (e.g., localhost or your IP)
def restrict_to_localhost(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_ips = ['127.0.0.1', '::1', '13.126.220.175']  # Add your IP if needed
        if request.remote_addr not in allowed_ips:
            current_app.logger.warning("Unauthorized access to debug endpoint from %s", request.remote_addr)
            return jsonify({'error': 'Unauthorized'}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        current_app.logger.debug("User %s already authenticated, redirecting to dashboard", current_user.username)
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        
        current_app.logger.debug("Attempting to authenticate: %s", username_or_email)
        user = User.authenticate(username_or_email, password)
        
        if user:
            # Login the user
            login_user(user, remember=remember)
            session.permanent = True  # Ensure session persists for 7 days (per run.py)
            current_app.logger.debug("Authentication successful for: %s, Session: %s", username_or_email, session)
            
            # Provide welcome message
            flash(f'Welcome back, {user.username}! You now have full access to all Instagram Analyzer features.', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page and url_for('main.index', _external=True) in next_page:  # Basic validation
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            current_app.logger.debug("Authentication failed for: %s", username_or_email)
            flash('Invalid username/email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        current_app.logger.debug("User %s already authenticated, redirecting to dashboard", current_user.username)
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create the user
            user = User.create_user(
                username=form.username.data,
                email=form.email.data,
                password=form.password.data
            )
            
            # Log the user in
            login_user(user, remember=True)
            session.permanent = True  # Ensure session persists
            current_app.logger.debug("Registered and logged in user: %s, Session: %s", user.username, session)
            
            # Welcome message
            flash(f'Welcome to Instagram Analyzer, {user.username}! Your account has been created successfully.', 'success')
            
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            current_app.logger.error("Registration failed: %s", str(e))
            flash(f'Registration failed: {str(e)}', 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    current_app.logger.debug("Logging out user: %s", current_user.username)
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/debug')
@restrict_to_localhost
def debug_users():
    """Debug endpoint to check user data (RESTRICTED TO LOCALHOST)"""
    try:
        # Force reload users from file
        User.load_users()
        
        # Check if file exists
        file_exists = os.path.exists(USERS_DATA_PATH)
        
        # Get file stats if it exists
        file_stats = None
        if file_exists:
            file_stats = {
                'size': os.path.getsize(USERS_DATA_PATH),
                'mod_time': os.path.getmtime(USERS_DATA_PATH),
                'permissions': oct(os.stat(USERS_DATA_PATH).st_mode)[-3:]
            }
        
        # Read file content if it exists
        file_content = None
        if file_exists:
            try:
                with open(USERS_DATA_PATH, 'r') as f:
                    file_content = json.load(f)
            except json.JSONDecodeError:
                file_content = "Invalid JSON format"
        
        # Get data from memory
        memory_users = {uid: {'username': user.username, 'email': user.email} 
                       for uid, user in User._users.items()}
        
        return jsonify({
            'file_path': USERS_DATA_PATH,
            'file_exists': file_exists,
            'file_stats': file_stats,
            'file_content': file_content,
            'memory_users': memory_users,
            'user_count': len(User._users),
            'data_dir_contents': os.listdir(os.path.dirname(USERS_DATA_PATH)) if os.path.exists(os.path.dirname(USERS_DATA_PATH)) else 'Directory not found',
            'session': dict(session)
        })
    except Exception as e:
        current_app.logger.error("Debug endpoint error: %s", str(e))
        return jsonify({
            'error': str(e),
            'users_data_path': USERS_DATA_PATH
        }), 500