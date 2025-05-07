from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app
)
from flask_login import login_user, logout_user, login_required, current_user

# Fix for werkzeug url_parse compatibility
try:
    from werkzeug.urls import url_parse
except ImportError:
    # Fallback for older versions
    from werkzeug.urls import url_decode as _url_decode
    from werkzeug.urls import url_split
    
    def url_parse(url):
        return url_split(url)

# Updated imports for models and forms
from app.forms import LoginForm, RegistrationForm
from app.models.user import User
from app.models.history import History
# Import db from app package directly
from app import db

# Create the blueprint directly here
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Redirect to main index or dashboard
    
    form = LoginForm()
    if form.validate_on_submit():
        # Use SQLAlchemy query to find the user
        user = db.session.scalar(db.select(User).where(User.username == form.username.data))

        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))

        # Log the user in using Flask-Login
        login_user(user, remember=form.remember_me.data)
        flash(f'Welcome back, {user.username}!', 'success')

        # Redirect to the page the user was trying to access, or index
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index') # Or main.dashboard if that exists
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Sign In', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index')) # Redirect to main index or dashboard
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash(f'Congratulations, {user.username}, you are now a registered user!', 'success')
            # Log the user in immediately after registration
            login_user(user)
            return redirect(url_for('main.index')) # Redirect to main index or dashboard
        except Exception as e:
            db.session.rollback() # Rollback in case of error
            flash('An error occurred during registration. Please try again.', 'danger')
            current_app.logger.error(f"Registration error: {str(e)}")
    
    return render_template('auth/register.html', title='Register', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))