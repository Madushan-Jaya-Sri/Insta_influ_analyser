#!/usr/bin/env python3
"""
Emergency fix script for circular imports and other critical issues.
This can be run directly in the container to fix issues.
"""

import os
import sys
import shutil
import subprocess

def fix_auth_py():
    """Fix the circular import in auth.py"""
    auth_py_path = '/app/app/routes/auth.py'
    
    if not os.path.exists(auth_py_path):
        print(f"ERROR: {auth_py_path} does not exist!")
        return False
    
    # Create backup
    backup_path = f"{auth_py_path}.bak"
    shutil.copy2(auth_py_path, backup_path)
    print(f"Created backup: {backup_path}")
    
    # Write the correct content
    with open(auth_py_path, 'w') as f:
        f.write('''from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

try:
    from werkzeug.urls import url_parse
except ImportError:
    # Fallback for older versions
    from werkzeug.urls import url_decode as _url_decode
    from werkzeug.urls import url_split
    
    def url_parse(url):
        return url_split(url)

from app.forms import LoginForm, RegistrationForm
from app.models.user import User
from app.models.history import History
# Import db from app package directly
from app import db

# Create the blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(db.select(User).where(User.username == form.username.data))

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')

        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'Congratulations, {user.username}, you are now a registered user!', 'success')
            login_user(user)
            return redirect(url_for('main.index'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
''')
    
    # Verify the fix
    with open(auth_py_path, 'r') as f:
        content = f.read()
        if 'from run import db' in content:
            print("ERROR: Fix failed! auth.py still contains 'from run import db'")
            return False
        else:
            print("SUCCESS: auth.py now correctly uses 'from app import db'")
            return True

def main():
    """Run all emergency fixes"""
    print("Running emergency fixes...")
    
    # Fix auth.py
    if fix_auth_py():
        print("auth.py fix completed successfully")
    else:
        print("auth.py fix FAILED")
    
    print("Emergency fixes completed")

if __name__ == "__main__":
    main() 