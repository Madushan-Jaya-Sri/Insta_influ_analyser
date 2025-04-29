from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app, jsonify, make_response
)
from flask_login import login_user, logout_user, login_required, current_user
import os
import json
from functools import wraps  # For restricting debug endpoint

from app.models.forms import LoginForm, RegistrationForm
from app.models.database import User, db

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
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            user = User.authenticate(form.username.data, form.password.data)
            if user:
                # Get response ready
                response = make_response(redirect(url_for('main.dashboard')))
                
                # Login user with remember me
                login_user(user, remember=True)
                
                # Set session data
                session['user_id'] = user.id
                session.permanent = True
                session.modified = True
                
                flash(f'Welcome back, {user.username}!', 'success')
                return response
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
        # Get response object ready
        response = make_response(redirect(url_for('main.index')))
        
        # Clear Flask-Login
        logout_user()
        
        # Clear session
        session.clear()
        
        # Clear remember me cookie
        response.delete_cookie('remember_token')
        
        # Clear session cookie
        response.delete_cookie('session')
        
        flash('You have been logged out.', 'info')
        return response
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return redirect(url_for('main.index'))

@auth_bp.route('/quick-login')
def quick_login():
    """Quick login without form"""
    try:
        user = User.get_by_username('testuser')
        if user:
            # Get response ready
            response = make_response(redirect(url_for('main.dashboard')))
            
            # Login user with remember me
            login_user(user, remember=True)
            
            # Set session data
            session['user_id'] = user.id
            session.permanent = True
            session.modified = True
            
            flash('Quick login successful!', 'success')
            return response
        else:
            flash('Test user not found', 'danger')
    except Exception as e:
        flash('An error occurred during quick login', 'danger')
        current_app.logger.error(f"Quick login error: {str(e)}")
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