import os
import json
import time
import uuid
import threading
from datetime import datetime
from functools import wraps
import shutil # Import shutil for directory operations
import traceback

from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app, jsonify, Response, copy_current_request_context
)
from werkzeug.utils import secure_filename
from wtforms import SelectField, validators
from flask_login import login_required, current_user

from app.models.forms import URLForm, CountryForm, UploadForm
from app.models.data_processor import DataProcessor
from app.models.apify_client_wrapper import ApifyWrapper
from app.models.history import History
from app import db

# Define APP_ROOT for use throughout this file
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Global data processor dictionary - maps user IDs to their DataProcessor instances
data_processors = {}

# Global progress data dictionary - maps user IDs to their progress data
progress_data_by_user = {}

# Global flags to track analysis completion - maps user IDs to completion status
analysis_complete_by_user = {}

processing_locks = {}

# Global variables to store data paths for background processing - maps user IDs to their data
background_data_by_user = {}

# Add this near the top with other global variables
processing_status_by_user = {}  # Maps user_id to processing status info

# Helper function to get the data processor for the current user
def get_data_processor():
    """Get the DataProcessor instance for the current user or create one if it doesn't exist"""
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        # Return a generic DataProcessor for unauthenticated users (should not be used)
        return DataProcessor()
        
    user_id = current_user.id
    if user_id not in data_processors:
        data_processors[user_id] = DataProcessor(user_id=user_id)
        
    return data_processors[user_id]

# Helper function to get or create a processing lock for the current user
def get_processing_lock():
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return threading.Lock()  # Return a temporary lock for unauthenticated users
        
    user_id = current_user.id
    if user_id not in processing_locks:
        processing_locks[user_id] = threading.Lock()
        
    return processing_locks[user_id]

# Helper function to get the progress data for the current user
def get_progress_data():
    if not current_user.is_authenticated:
        return {
            'step': 0,
            'progress': 0,
            'status': {},
            'message': 'Please log in to track progress',
            'complete': False
        }
        
    user_id = current_user.id
    if user_id not in progress_data_by_user:
        progress_data_by_user[user_id] = {
            'step': 0,
            'progress': 0,
            'status': {},
            'message': 'Initializing...',
            'complete': False
        }
        
    return progress_data_by_user[user_id]

# Helper function to check if analysis is complete for the current user
def is_analysis_complete():
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        return False
        
    user_id = current_user.id
    return analysis_complete_by_user.get(user_id, False)

# Helper function to set analysis complete status for the current user
def set_analysis_complete(value):
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        print("Warning: Attempting to set analysis complete status without authenticated user")
        return
        
    user_id = current_user.id
    analysis_complete_by_user[user_id] = value

# Helper function to get background data for the current user
def get_background_data():
    if not current_user.is_authenticated:
        return {
            'profile_path': None,
            'posts_path': None,
            'country_mapping': {}
        }
        
    user_id = current_user.id
    if user_id not in background_data_by_user:
        background_data_by_user[user_id] = {
            'profile_path': None,
            'posts_path': None,
            'country_mapping': {}
        }
        
    return background_data_by_user[user_id]

# Helper function to update progress
def update_progress(step, progress, status=None, message=None, complete=False):
    # Get current user ID - if there's no authenticated user, we can't update progress
    user_id = None
    try:
        if current_user.is_authenticated:
            user_id = current_user.id
        else:
            # Try to get user ID from the stored global state if needed
            print("User not authenticated in update_progress")
            return
    except Exception as e:
        print(f"Error getting user ID in update_progress: {str(e)}")
        traceback.print_exc()
        return
    
    # Check if this is the final update and we're setting complete=True
    if complete:
        try:
            # Set the complete flag directly in the global state too
            set_analysis_complete(True)
            
            # When complete, ensure progress is 100%
            progress = 100
            
            # If no message was provided for completion, add a default
            if not message:
                message = "Processing complete! Redirecting to dashboard..."
        except Exception as e:
            print(f"Error setting complete state: {str(e)}")
            traceback.print_exc()
    
    try:
        # Ensure progress_data_by_user exists
        if 'progress_data_by_user' not in globals():
            global progress_data_by_user
            progress_data_by_user = {}
        
        # Get a local copy of the progress data
        progress_data = {
            'step': step,
            'progress': progress,
            'status': status or {},
            'message': message or 'Processing...',
            'complete': complete,
            'timestamp': datetime.now().isoformat()
        }
            
        # Update progress data for this user in global dictionary
        progress_data_by_user[user_id] = progress_data
        
        print(f"Progress updated: Step {step}, {progress}%, Message: {message}, Complete: {complete}")
    except Exception as e:
        print(f"Error updating progress: {str(e)}")
        print(f"Step: {step}, Progress: {progress}, Message: {message}, Complete: {complete}")
        print(f"User ID: {user_id}")
        traceback.print_exc()

# Helper function to get/set processing status
def get_processing_status():
    """Get the current processing status for the current user"""
    if not current_user.is_authenticated:
        return None
        
    user_id = current_user.id
    if user_id not in processing_status_by_user:
        return None
        
    return processing_status_by_user[user_id]

def set_processing_status(status, message=None, urls=None, redirect_url=None):
    """Set the processing status for the current user"""
    if not current_user.is_authenticated:
        return
        
    user_id = current_user.id
    processing_status_by_user[user_id] = {
        'status': status,  # 'processing', 'complete', 'error'
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'urls': urls,
        'redirect_url': redirect_url
    }

def clear_processing_status():
    """Clear the processing status for the current user"""
    if not current_user.is_authenticated:
        return
        
    user_id = current_user.id
    if user_id in processing_status_by_user:
        del processing_status_by_user[user_id]

# Decorator to inject processing status into templates
def inject_processing_status():
    """Inject processing status into all templates"""
    status = get_processing_status()
    return dict(processing_status=status)

# Modify the index route to handle form submission and allow navigation
@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Landing page with URL input form for authenticated users or marketing content for guests"""
    # If user is not logged in, show marketing landing page without the form
    if not current_user.is_authenticated:
        return render_template('index.html', show_form=False)
    
    # For authenticated users, show the form for URL submission
    form = URLForm()
    
    # Get current processing status
    processing_status = get_processing_status()
    
    if form.validate_on_submit():
        # Get Instagram URLs
        instagram_urls = form.instagram_urls.data.strip().split('\n')
        max_posts = form.max_posts.data
        time_filter = form.time_filter.data
        
        # Store settings in session
        session['instagram_urls'] = instagram_urls
        session['max_posts'] = max_posts
        session['time_filter'] = time_filter
        
        # Reset progress data
        update_progress(1, 0, {}, 'Initializing data processing...', False)
        set_analysis_complete(False)
        
        # Set processing status
        set_processing_status('processing', 
                             f'Processing {len(instagram_urls)} Instagram profiles...', 
                             instagram_urls,
                             redirect_url=url_for('main.dashboard'))
        
        # Start processing in a separate thread
        background_task = copy_current_request_context(lambda: process_urls_in_background(instagram_urls, max_posts, time_filter))
        processing_thread = threading.Thread(target=background_task)
        processing_thread.daemon = True
        processing_thread.start()
        
        # Redirect to processing page
        flash('Analysis started! You can navigate to other pages while processing continues.', 'info')
        return redirect(url_for('main.processing'))
    
    return render_template('index.html', form=form, show_form=True, processing_status=processing_status)

@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_files():
    form = UploadForm()
    error = None
    
    if form.validate_on_submit():
        try:
            # Create uploads directory if it doesn't exist
            uploads_dir = current_app.config['UPLOAD_FOLDER']
            if not os.path.exists(uploads_dir):
                os.makedirs(uploads_dir)
            
            # Get the uploaded files
            profile_file = form.profile_file.data
            posts_file = form.posts_file.data
            
            # Create user-specific directory for uploads
            user_uploads_dir = os.path.join(uploads_dir, f'user_{current_user.id}')
            os.makedirs(user_uploads_dir, exist_ok=True)
            
            # Save the profile file
            profile_filename = secure_filename(profile_file.filename)
            profile_path = os.path.join(user_uploads_dir, profile_filename)
            profile_file.save(profile_path)
            
            # Save the posts file
            posts_filename = secure_filename(posts_file.filename)
            posts_path = os.path.join(user_uploads_dir, posts_filename)
            posts_file.save(posts_path)
            
            # Save the file paths in the session
            session['profile_path'] = profile_path
            session['posts_path'] = posts_path
            
            return redirect(url_for('main.select_countries'))
        
        except Exception as e:
            error = f"Error uploading files: {str(e)}"
    
    return render_template('upload.html', form=form, error=error)

@main_bp.route('/select-countries', methods=['GET', 'POST'])
@login_required
def select_countries():
    if 'profile_path' not in session or 'posts_path' not in session:
        flash('Please upload your Instagram data files first.', 'warning')
        return redirect(url_for('main.upload_files'))
    
    # Create a base form
    form = CountryForm()
    error = None
    usernames = []
    
    # Dynamically add country fields based on the uploaded profile data
    try:
        # Read the profile data file
        with open(session['profile_path'], 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Extract usernames from the profile data
        for profile in profile_data:
            if 'username' in profile:
                username = profile['username']
                usernames.append(username)
                
                # Create the field name
                field_name = f'country_{username}'
                
                # Add the field to the form class if it doesn't exist
                if field_name not in form._fields:
                    country_choices = [
                        ('', 'Select Country'),
                        ('Australia', 'Australia'),
                        ('Canada', 'Canada'),
                        ('India', 'India'),
                        ('Malaysia', 'Malaysia'),
                        ('Singapore', 'Singapore'),
                        ('Sri Lanka', 'Sri Lanka'),
                        ('United Kingdom', 'United Kingdom'),
                        ('United States', 'United States'),
                        ('Other', 'Other')
                    ]
                    
                    setattr(CountryForm, field_name, SelectField(
                        f'Country for @{username}',
                        choices=country_choices,
                        validators=[validators.DataRequired(message='Please select a country')]
                    ))
        
        # Re-instantiate the form to include the new fields
        form = CountryForm()
        
    except Exception as e:
        error = f"Error processing profile data: {str(e)}"
    
    if form.validate_on_submit():
        try:
            # Save country selections
            country_mapping = {}
            for username in usernames:
                field_name = f'country_{username}'
                if field_name in form._fields:
                    country_mapping[username] = form[field_name].data
            
            # Store country mapping in background data
            background_data = get_background_data()
            background_data['profile_path'] = session['profile_path']
            background_data['posts_path'] = session['posts_path']
            background_data['country_mapping'] = country_mapping
            
            # Reset progress data
            update_progress(1, 0, {}, 'Initializing data processing...', False)
            set_analysis_complete(False)
            
            # Start processing in a separate thread
            background_task = copy_current_request_context(lambda: process_data_in_background(
                session['profile_path'], 
                session['posts_path'],
                country_mapping
            ))
            processing_thread = threading.Thread(target=background_task)
            processing_thread.daemon = True
            processing_thread.start()
            
            return redirect(url_for('main.processing'))
            
        except Exception as e:
            error = f"Error processing country selections: {str(e)}"
    
    # Render the country selection form
    return render_template('select_countries.html', form=form, error=error, usernames=usernames)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard displaying influencer analysis"""
    data_processor = get_data_processor()
    
    # Check if data exists, either from current run or loaded file
    if not data_processor.influencers_data:
        flash("No influencer data available. Please process data first.", 'warning')
        return redirect(url_for('main.index'))
    
    # Get processed data from the user's data processor
    influencers_data = data_processor.influencers_data
    
    # Clear completed processing status when user views dashboard
    processing_status = get_processing_status()
    if processing_status and processing_status['status'] == 'complete':
        clear_processing_status()
    
    # Add a reset button to the template context
    return render_template('dashboard.html', influencers=influencers_data, show_reset=True)

@main_bp.route('/influencer/<username>')
@login_required
def influencer_detail(username):
    """Detailed view for a specific influencer"""
    data_processor = get_data_processor()
    
    # Check if data exists, either from current run or loaded file
    if not data_processor.influencers_data:
        flash("No influencer data available. Please process data first.", 'warning')
        return redirect(url_for('main.dashboard'))

    # Get data from the user's data processor
    influencer = data_processor.influencers_data.get(username)

    if not influencer:
        flash(f"Influencer @{username} not found", 'warning')
        return redirect(url_for('main.dashboard'))

    return render_template('influencer_detail.html', influencer=influencer)

@main_bp.route('/api/influencer/<username>')
@login_required
def influencer_api(username):
    """API endpoint for fetching influencer data for charts"""
    data_processor = get_data_processor()
    
    # Check if data exists
    if not data_processor.influencers_data:
        return jsonify({'error': 'No influencer data available. Please process data first.'}), 400

    # Get data from the global data processor
    influencers_data = data_processor.influencers_data

    if username not in influencers_data:
        return jsonify({'error': 'Influencer not found'}), 404
    
    influencer = influencers_data[username]
    
    # Custom JSON serialization function to handle NaN, Infinity values
    def clean_value(value):
        import math
        import numpy as np
        
        # Handle nan, infinity, numpy-specific types
        if isinstance(value, (float, np.float32, np.float64)):
            if math.isnan(value) or math.isinf(value):
                return 0
            return float(value)
        elif isinstance(value, (int, np.int32, np.int64)):
            return int(value)
        elif isinstance(value, (list, tuple)):
            return [clean_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: clean_value(v) for k, v in value.items()}
        else:
            return value
    
    # Extract post-level engagement data from the posts
    post_engagement = {
        'dates': [],
        'engagement_rate': [],
        'likes': [],
        'comments': []
    }
    
    # Extract post-level data if available
    if 'posts' in influencer and influencer['posts']:
        for post in influencer['posts']:
            # Skip posts without necessary data
            if not post.get('timestamp'):
                continue
                
            # Add post data
            post_engagement['dates'].append(post.get('timestamp'))
            post_engagement['engagement_rate'].append(post.get('engagement_rate', 0))
            post_engagement['likes'].append(post.get('likes_count', 0))
            post_engagement['comments'].append(post.get('comments_count', 0))
    
    # Process time-based metrics (weekly, monthly, quarterly)
    # The new format has proper structured objects with date, likes, comments, etc.
    
    # Process weekly data
    weekly_engagement = {
        'dates': [],
        'engagement_rate': [],
        'likes': [],
        'comments': []
    }
    
    if 'engagement_weekly' in influencer and influencer['engagement_weekly']:
        for item in influencer['engagement_weekly']:
            weekly_engagement['dates'].append(item.get('date'))
            weekly_engagement['engagement_rate'].append(item.get('engagement_rate', 0))
            weekly_engagement['likes'].append(item.get('likes', 0))
            weekly_engagement['comments'].append(item.get('comments', 0))
    
    # Process monthly data
    monthly_engagement = {
        'dates': [],
        'engagement_rate': [],
        'likes': [],
        'comments': []
    }
    
    if 'engagement_monthly' in influencer and influencer['engagement_monthly']:
        for item in influencer['engagement_monthly']:
            monthly_engagement['dates'].append(item.get('date'))
            monthly_engagement['engagement_rate'].append(item.get('engagement_rate', 0))
            monthly_engagement['likes'].append(item.get('likes', 0))
            monthly_engagement['comments'].append(item.get('comments', 0))
    
    # Process quarterly data
    quarterly_engagement = {
        'dates': [],
        'engagement_rate': [],
        'likes': [],
        'comments': []
    }
    
    if 'engagement_quarterly' in influencer and influencer['engagement_quarterly']:
        for item in influencer['engagement_quarterly']:
            quarterly_engagement['dates'].append(item.get('date'))
            quarterly_engagement['engagement_rate'].append(item.get('engagement_rate', 0))
            quarterly_engagement['likes'].append(item.get('likes', 0))
            quarterly_engagement['comments'].append(item.get('comments', 0))
    
    # Create response data
    response_data = {
        'post_engagement': clean_value(post_engagement),
        'weekly_engagement': clean_value(weekly_engagement),
        'monthly_engagement': clean_value(monthly_engagement),
        'quarterly_engagement': clean_value(quarterly_engagement),
        'avg_engagement_rate': clean_value(influencer.get('avg_engagement_rate', 0)),
        'max_engagement_rate': clean_value(influencer.get('max_engagement_rate', 0)),
        'avg_likes': clean_value(influencer.get('avg_likes', 0)),
        'avg_comments': clean_value(influencer.get('avg_comments', 0)),
        'total_engagement': clean_value(influencer.get('total_engagement', 0)),
        'top_hashtags': clean_value(influencer.get('top_hashtags', [])),
        'top_mentions': clean_value(influencer.get('top_mentions', []))
    }
    
    # Additional error handling with try-except
    try:
        return jsonify(response_data)
    except Exception as e:
        print(f"Error serializing data for {username}: {e}")
        traceback.print_exc()
        # Fallback with minimal data
        return jsonify({
            'error': str(e),
            'post_engagement': {'dates': [], 'engagement_rate': [], 'likes': [], 'comments': []},
            'weekly_engagement': {'dates': [], 'engagement_rate': [], 'likes': [], 'comments': []},
            'monthly_engagement': {'dates': [], 'engagement_rate': [], 'likes': [], 'comments': []},
            'quarterly_engagement': {'dates': [], 'engagement_rate': [], 'likes': [], 'comments': []}
        })

@main_bp.route('/history')
@login_required
def history():
    """Display user's analysis history from the database"""
    from app.models.history import History
    user_history = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).all()
    return render_template('history.html', history=user_history)

@main_bp.route('/history/<int:history_id>')
@login_required
def view_historical_analysis(history_id):
    """View a specific historical analysis"""
    data_processor = get_data_processor()
    
    # Attempt to load the historical analysis
    if not data_processor.load_analysis_from_history(history_id):
        flash("Analysis not found or could not be loaded", "danger")
        return redirect(url_for('main.history'))
    
    # Get the loaded data
    influencers_data = data_processor.influencers_data
    
    # Mark as loaded from history
    from app.models.history import History
    history_record = History.query.get_or_404(history_id)
    
    # Render the dashboard with historical data
    return render_template(
        'dashboard.html', 
        influencers=influencers_data, 
        historical=True, 
        history_id=history_id,
        profile_username=history_record.profile_username,
        history_date=history_record.timestamp
    )

@main_bp.route('/processing')
@login_required
def processing():
    """Show processing page - can be accessed at any time during processing"""
    # Check if there's an active processing task
    processing_status = get_processing_status()
    if not processing_status or processing_status['status'] != 'processing':
        # No active processing or it's complete
        flash('No active processing found.', 'info')
        return redirect(url_for('main.dashboard'))
    
    return render_template('processing.html')

@main_bp.route('/progress-stream')
@login_required
def progress_stream():
    # Capture authentication state and user_id BEFORE entering the generator
    # This ensures we have the values before any yielding happens
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
        
    # Store user_id from the authenticated user
    user_id = current_user.id
    
    def generate():
        last_data = None
        retry_count = 0
        
        while True:
            try:
                # Check if user ID is still valid in our progress data
                if user_id not in progress_data_by_user:
                    print(f"User ID {user_id} not found in progress data")
                    yield f"data: {json.dumps({'error': 'User data not found'})}\n\n"
                    break
                    
                # Get progress data directly using stored user_id
                progress_data = progress_data_by_user[user_id]
                current_data = json.dumps(progress_data)
                    
                if current_data != last_data:
                    last_data = current_data
                    yield f"data: {current_data}\n\n"
                    retry_count = 0
                
                if progress_data.get('complete', False):
                    print("Processing complete, ending SSE stream")
                    break
                    
                time.sleep(0.5)
            except Exception as e:
                print(f"Error in SSE stream: {str(e)}")
                retry_count += 1
                if retry_count > 5:  # After 5 retries, give up
                    print("Too many errors in SSE stream, closing connection")
                    break
                time.sleep(1)  # Wait a bit longer on error
    
    response = Response(generate(), mimetype='text/event-stream')
    # Add headers to prevent caching
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response

@main_bp.route('/check-progress')
@login_required
def check_progress():
    """Simple endpoint to check current progress data via AJAX"""
    try:
        # Get progress data for the current user
        user_id = current_user.id
        
        # If data doesn't exist for this user, return a default structure
        if user_id not in progress_data_by_user:
            return jsonify({
                'step': 1,
                'progress': 0,
                'status': {},
                'message': 'Initializing...',
                'complete': False
            })
            
        # Otherwise return the actual progress data
        return jsonify(progress_data_by_user[user_id])
        
    except Exception as e:
        print(f"Error in check_progress endpoint: {str(e)}")
        return jsonify({
            'step': 1,
            'progress': 0,
            'status': {'error': 'yes'},
            'message': f'Error retrieving progress: {str(e)}',
            'complete': False
        }), 500

def process_data_in_background(profile_path, posts_path, country_mapping):
    try:
        # Get the data processor for the current user
        data_processor = get_data_processor()
        set_analysis_complete(False)  # Reset flag at the start of processing

        update_progress(1, 5, {'parsing': 'working'}, 'Parsing JSON files...')
        time.sleep(0.5)  # Simulate processing time

        # Load profile data (this now clears previous data)
        update_progress(1, 20, {'parsing': 'complete', 'profile': 'working'}, 'Extracting profile data...')
        data_processor.load_profile_data(profile_path)
        time.sleep(0.5)  # Simulate processing time

        # Load posts data
        update_progress(1, 35, {'profile': 'complete', 'posts': 'working'}, 'Extracting post data...')
        data_processor.load_posts_data(posts_path)
        time.sleep(0.5)  # Simulate processing time

        # Set countries for influencers
        for username, country in country_mapping.items():
            data_processor.set_country(username, country)

        update_progress(1, 50, {'posts': 'complete', 'stats': 'working'}, 'Calculating statistics...')
        time.sleep(0.5)  # Simulate processing time

        # Process data (this now saves the data at the end)
        data_processor.merge_data()
        data_processor.process_influencer_data()

        # update_progress calls will happen inside process_influencer_data if needed
        # Simplified progress updates here

        # Set the analysis complete flag
        set_analysis_complete(True)

        update_progress(4, 100, {'visualization': 'complete'}, 'Processing complete!', True)

    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        update_progress(
            max(get_progress_data()['step'], 1),  # Keep current step
            get_progress_data()['progress'],  # Keep current progress
            None,
            f"Error during processing: {str(e)}",
            False
        )

# New function to process Instagram URLs
def process_urls_in_background(instagram_urls, max_posts, time_filter):
    try:
        # Deployment debugging logs
        print("\n==== DEPLOYMENT DEBUG INFO ====")
        print(f"Starting background processing at: {datetime.now().isoformat()}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"App root: {APP_ROOT}")
        print(f"User ID: {current_user.id if current_user.is_authenticated else 'Not authenticated'}")
        print(f"URLs to process: {instagram_urls}")
        print(f"Max posts: {max_posts}")
        print(f"Time filter: {time_filter}")
        
        # Check for required directories
        user_id = current_user.id if current_user.is_authenticated else None
        if user_id:
            data_dir = os.path.join(current_app.config['DATA_FOLDER'], f'user_{user_id}')
            images_dir = os.path.join(current_app.config['IMAGES_FOLDER'], f'user_{user_id}')
            
            print(f"Data directory: {data_dir} (exists: {os.path.exists(data_dir)})")
            print(f"Images directory: {images_dir} (exists: {os.path.exists(images_dir)})")
            
            # Try to create directories if they don't exist
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
                print(f"Created data directory: {data_dir}")
            
            if not os.path.exists(images_dir):
                os.makedirs(images_dir, exist_ok=True)
                print(f"Created images directory: {images_dir}")
        
        # Check OpenAI API key
        openai_api_key = os.getenv('OPENAI_API_KEY')
        print(f"OpenAI API key available: {'Yes' if openai_api_key else 'No'}")
        
        # Update processing status
        set_processing_status('processing', f'Processing {len(instagram_urls)} Instagram profiles...', instagram_urls)
        
        # Get the data processor for the current user
        data_processor = get_data_processor()
        set_analysis_complete(False)  # Reset flag

        # Initial progress - Step 1: Initialization (0-15%)
        update_progress(1, 0, {'init': 'working'}, 'Initializing Instagram analysis...', False)
        time.sleep(0.5)  # Small delay for visual effect
        
        update_progress(1, 5, {'init': 'working', 'apify': 'working'}, 'Connecting to data services...')

        # Create ApifyWrapper instance
        try:
            apify_client = ApifyWrapper()
            update_progress(1, 10, {'init': 'complete', 'apify': 'complete'}, 'Connected to Apify API successfully')
            time.sleep(0.5)  # Small delay for visual effect
        except Exception as e:
            error_msg = f"Failed to initialize Apify client: {str(e)}"
            print(error_msg)
            update_progress(1, 10, {'init': 'complete', 'apify': 'error'}, error_msg)
            return
        
        # Convert time filter to appropriate format for Apify
        posts_newer_than = None
        if time_filter == '1m':
            posts_newer_than = "1 month"
        elif time_filter == '3m':
            posts_newer_than = "3 months"
        elif time_filter == '6m':
            posts_newer_than = "6 months"
        elif time_filter == '1y':
            posts_newer_than = "1 year"
        
        # Get user-specific directory for downloads
        user_data_dir = os.path.join(current_app.config['DATA_FOLDER'], f'user_{user_id}')
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Step 1: Profile Scraping (15-40%)
        update_progress(1, 15, {'profile': 'working', 'urls': 'working'}, f'Fetching {len(instagram_urls)} Instagram profiles...')
        time.sleep(0.7)  # Small delay for visual effect
        
        try:
            # Simulated progress updates during profile scraping
            update_progress(1, 20, {'profile': 'working', 'urls': 'complete'}, 'URLs validated, retrieving profile data...')
            time.sleep(0.5)
            
            # Remove output_dir parameter as it's not in the method signature
            temp_profile_path = apify_client.scrape_instagram_profiles(instagram_urls)
            
            update_progress(1, 30, {'profile': 'working'}, 'Processing profile information...')
            time.sleep(0.5)
            
            # Move the temporary file to the user's directory
            profile_filename = f"profiles_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            profile_path = os.path.join(user_data_dir, profile_filename)
            shutil.copy2(temp_profile_path, profile_path)
            os.remove(temp_profile_path)  # Remove the temporary file
            
            update_progress(1, 40, {'profile': 'complete'}, 'Profile data retrieved successfully')
            time.sleep(0.5)
        except Exception as e:
            error_msg = f"Failed to scrape profile data: {str(e)}"
            print(error_msg)
            update_progress(1, 30, {'profile': 'error'}, error_msg)
            return
        
        # Step 2: Posts Scraping (40-60%)
        update_progress(2, 40, {'posts': 'working'}, f'Retrieving posts (max {max_posts} per profile)...')
        time.sleep(0.5)
        
        try:
            # Simulated progress updates during posts scraping
            update_progress(2, 45, {'posts': 'working', 'media': 'working'}, 'Connecting to Instagram data APIs...')
            time.sleep(0.5)
            
            # Remove output_dir parameter as it's not in the method signature
            temp_posts_path = apify_client.scrape_instagram_posts(
                instagram_urls, 
                max_posts, 
                posts_newer_than
            )
            
            update_progress(2, 50, {'posts': 'working', 'media': 'complete'}, 'Downloading post content...')
            time.sleep(0.5)
            
            update_progress(2, 55, {'posts': 'working'}, 'Processing post data...')
            
            # Move the temporary file to the user's directory
            posts_filename = f"posts_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            posts_path = os.path.join(user_data_dir, posts_filename)
            shutil.copy2(temp_posts_path, posts_path)
            os.remove(temp_posts_path)  # Remove the temporary file
            
            update_progress(2, 60, {'posts': 'complete'}, 'Post data retrieved successfully')
            time.sleep(0.5)
        except Exception as e:
            error_msg = f"Failed to scrape posts data: {str(e)}"
            print(error_msg)
            update_progress(2, 50, {'posts': 'error'}, error_msg)
            return
        
        # Save paths to background data
        background_data = get_background_data()
        background_data['profile_path'] = profile_path
        background_data['posts_path'] = posts_path
        
        # Step 3: Data Processing (60-80%)
        update_progress(3, 60, {'stats': 'working', 'parsing': 'working'}, 'Parsing Instagram data...')
        time.sleep(0.5)
        
        # Create default country mapping (use "Other" for all profiles)
        country_mapping = {}
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
                for profile in profile_data:
                    if 'username' in profile:
                        country_mapping[profile['username']] = 'Other'
        except Exception as e:
            print(f"Error creating country mapping: {str(e)}")
        
        # Store country mapping in background data
        background_data['country_mapping'] = country_mapping
        
        update_progress(3, 65, {'stats': 'working', 'parsing': 'complete', 'profile_data': 'working'}, 'Loading profile data...')
        time.sleep(0.5)
        
        # Load profile data
        data_processor.load_profile_data(profile_path)
        
        update_progress(3, 70, {'stats': 'working', 'profile_data': 'complete', 'post_data': 'working'}, 'Loading post data...')
        time.sleep(0.5)
        
        # Load posts data
        data_processor.load_posts_data(posts_path)
        
        update_progress(3, 73, {'stats': 'working', 'post_data': 'complete', 'geo': 'working'}, 'Assigning geographical data...')
        time.sleep(0.5)
        
        # Set countries for influencers
        for username, country in country_mapping.items():
            data_processor.set_country(username, country)
        
        update_progress(3, 75, {'stats': 'working', 'geo': 'complete', 'merging': 'working'}, 'Merging profile and post data...')
        time.sleep(0.5)
        
        # Process data
        data_processor.merge_data()
        
        update_progress(3, 78, {'stats': 'working', 'merging': 'complete', 'analysis': 'working'}, 'Analyzing engagement patterns...')
        time.sleep(0.5)
        
        data_processor.process_influencer_data()
        
        update_progress(3, 80, {'stats': 'complete', 'analysis': 'complete'}, 'Data analysis complete')
        time.sleep(0.5)
        
        # Step 4: Image Processing and Content Analysis (80-100%)
        update_progress(4, 80, {'images': 'working', 'profile_pics': 'working'}, 'Processing profile images...')
        time.sleep(0.5)
        
        update_progress(4, 85, {'images': 'working', 'profile_pics': 'complete', 'post_pics': 'working'}, 'Processing post images...')
        time.sleep(0.5)
        
        update_progress(4, 90, {'images': 'complete', 'post_pics': 'complete', 'ai': 'working'}, 'Running AI content analysis...')
        time.sleep(0.5)
        
        # Content analysis with LLM
        if openai_api_key:
            try:
                data_processor.analyze_with_llm(openai_api_key)
                update_progress(4, 95, {'ai': 'complete', 'interests': 'complete'}, 'AI content analysis complete')
                time.sleep(0.5)
            except Exception as e:
                print(f"Error in LLM analysis: {str(e)}")
                update_progress(4, 95, {'ai': 'warning', 'interests': 'warning'}, 'Content analysis completed with warnings')
        else:
            update_progress(4, 95, {'ai': 'warning', 'interests': 'warning'}, 'OpenAI API key not found, using basic analysis only')
        
        # Final steps
        update_progress(4, 97, {'finalizing': 'working'}, 'Finalizing analysis results...')
        time.sleep(0.5)
        
        # Set the analysis complete flag
        set_analysis_complete(True)
        
        # Save to history database for later retrieval
        data_processor.save_to_history_db(time_filter=time_filter, max_posts=max_posts)
        
        # Set processing complete status
        set_processing_status('complete', 'Analysis complete! View results on dashboard.', 
                             instagram_urls, redirect_url=url_for('main.dashboard'))
        
    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        # Update progress and set error status
        update_progress(
            max(get_progress_data()['step'], 1),  # Keep current step
            get_progress_data()['progress'],  # Keep current progress
            None,
            f"Error during processing: {str(e)}",
            False
        )
        set_processing_status('error', f'Error during processing: {str(e)}', instagram_urls)

@main_bp.route('/clear-data', methods=['POST'])
@login_required
def clear_data():
    try:
        data_processor = get_data_processor()

        # Always clear images when this endpoint is called
        clear_images = True

        # Use the clear_all_data method from DataProcessor
        data_processor.clear_all_data(clear_images=clear_images)

        # Reset the analysis complete flag
        set_analysis_complete(False)

        flash('All application data and images have been cleared.', 'success')
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error clearing data: {e}")
        flash('An error occurred while clearing data.', 'danger')
        return jsonify({'success': False}), 500

@main_bp.route('/reset-dashboard', methods=['POST'])
@login_required
def reset_dashboard():
    try:
        data_processor = get_data_processor()
        # Always clear images when this endpoint is called
        clear_images = True

        # Use the clear_all_data method from DataProcessor
        data_processor.clear_all_data(clear_images=clear_images)

        # Reset the analysis complete flag
        set_analysis_complete(False)

        flash('All application data and images have been cleared.', 'success')
        return redirect(url_for('main.dashboard'))
    except Exception as e:
        print(f"Error clearing data: {e}")
        flash('An error occurred while clearing data.', 'danger')
        return redirect(url_for('main.dashboard'))

# Add a status check endpoint for AJAX polling
@main_bp.route('/api/processing-status')
@login_required
def check_processing_status():
    """API endpoint to check processing status"""
    status = get_processing_status()
    if status:
        return jsonify(status)
    return jsonify({'status': 'none'})

# New debug endpoint to view logs
@main_bp.route('/debug/logs')
@login_required
def debug_logs():
    """View application logs for debugging deployment issues"""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401
        
    # Only return logs for the current user
    user_id = current_user.id
    
    # Return debugging information
    debug_info = {
        'current_time': datetime.now().isoformat(),
        'progress_data': progress_data_by_user.get(user_id, {}),
        'is_analysis_complete': analysis_complete_by_user.get(user_id, False),
        'background_data': background_data_by_user.get(user_id, {}),
        'processing_status': processing_status_by_user.get(user_id, {})
    }
    
    # Include environment info
    debug_info['environment'] = {
        'app_root': os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        'current_directory': os.getcwd(),
        'data_folder': current_app.config.get('DATA_FOLDER', 'Not set'),
        'images_folder': current_app.config.get('IMAGES_FOLDER', 'Not set'),
        'openai_api_available': bool(os.getenv('OPENAI_API_KEY')),
    }
    
    # Check important directories
    data_dir = os.path.join(current_app.config.get('DATA_FOLDER', ''), f'user_{user_id}')
    images_dir = os.path.join(current_app.config.get('IMAGES_FOLDER', ''), f'user_{user_id}')
    
    debug_info['directories'] = {
        'data_dir': {
            'path': data_dir,
            'exists': os.path.exists(data_dir),
            'is_writable': os.access(data_dir, os.W_OK) if os.path.exists(data_dir) else False
        },
        'images_dir': {
            'path': images_dir,
            'exists': os.path.exists(images_dir),
            'is_writable': os.access(images_dir, os.W_OK) if os.path.exists(images_dir) else False
        }
    }
    
    return jsonify(debug_info) 