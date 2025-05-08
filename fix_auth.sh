#!/bin/bash
set -e

# Check if we're running in the container
if [ ! -d "/app" ]; then
  echo "This script should be run inside the Docker container"
  exit 1
fi


echo "Fixing circular import in auth.py..."
cat > /app/app/routes/auth.py << 'EOF'
from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

try:
    from werkzeug.urls import url_parse
except ImportError:
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
EOF

echo "Checking the fixed auth.py file..."
grep -n "from run" /app/app/routes/auth.py || echo "No 'from run' imports found - file fixed correctly"

echo "Fix completed." 