from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app, jsonify
)
from flask_login import login_user, logout_user, login_required, current_user

from app.models.forms import LoginForm, RegistrationForm
from app.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        username_or_email = form.username.data
        password = form.password.data
        remember = form.remember_me.data
        
        # Authenticate the user
        user = User.authenticate(username_or_email, password)
        
        if user:
            # Login the user
            login_user(user, remember=remember)
            
            # Provide more informative welcome message with guidance to services
            flash(f'Welcome back, {user.username}! You now have full access to all Instagram Analyzer features including dashboard, data analysis, and history tracking.', 'success')
            
            # Redirect to the page requested before login, or dashboard if none
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid username/email or password', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
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
            login_user(user)
            
            # Enhanced welcome message with guidance
            flash(f'Welcome to Instagram Analyzer, {user.username}! Your account has been created successfully. You now have full access to analyze influencers, track engagement metrics, and save your analysis history.', 'success')
            
            # Redirect to dashboard
            return redirect(url_for('main.dashboard'))
        except ValueError as e:
            flash(str(e), 'danger')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index')) 