import os
import json
import time
import uuid
import threading
from datetime import datetime
from functools import wraps
import shutil # Import shutil for directory operations

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

main_bp = Blueprint('main', __name__)

# Global data processor dictionary - maps user IDs to their DataProcessor instances
data_processors = {}

# Global progress data dictionary - maps user IDs to their progress data
progress_data_by_user = {}

# Global flags to track analysis completion - maps user IDs to completion status
analysis_complete_by_user = {}

processing_locks = {}

# Global variables to store data paths for background processing - maps user IDs to their data
background_data_by_user = {}

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
    if not hasattr(current_user, 'is_authenticated') or not current_user.is_authenticated:
        print("Warning: Attempting to update progress without authenticated user")
        return
        
    user_id = current_user.id
    lock = get_processing_lock()
    
    with lock:
        # Ensure the user has a progress data entry
        if user_id not in progress_data_by_user:
            progress_data_by_user[user_id] = {
                'step': 0,
                'progress': 0,
                'status': {},
                'message': 'Initializing...',
                'complete': False
            }
            
        progress_data = progress_data_by_user[user_id]
        progress_data['step'] = step
        progress_data['progress'] = progress
        if status:
            if 'status' not in progress_data:
                progress_data['status'] = {}
            progress_data['status'].update(status)
        if message:
            progress_data['message'] = message
        progress_data['complete'] = complete
        # Update global analysis_complete flag when processing finishes
        if complete:
            set_analysis_complete(True)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Landing page with URL input form for authenticated users or marketing content for guests"""
    # If user is not logged in, show marketing landing page without the form
    if not current_user.is_authenticated:
        return render_template('index.html', show_form=False)
    
    # For authenticated users, show the form for URL submission
    form = URLForm()
    
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
        
        # Start processing in a separate thread
        background_task = copy_current_request_context(lambda: process_urls_in_background(instagram_urls, max_posts, time_filter))
        processing_thread = threading.Thread(target=background_task)
        processing_thread.daemon = True
        processing_thread.start()
        
        return redirect(url_for('main.processing'))
    
    return render_template('index.html', form=form, show_form=True)

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
    
    return render_template('dashboard.html', influencers=influencers_data)

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
    
    # Ensure all engagement data keys exist with defaults
    default_engagement = {'dates': [], 'rates': [], 'likes': [], 'comments': []}
    post_engagement = influencer.get('post_engagement', default_engagement)
    
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
    
    # Create properly formatted data for the frontend
    weekly_engagement = influencer.get('weekly_engagement', {'dates': [], 'rates': []})
    monthly_engagement = influencer.get('monthly_engagement', {'dates': [], 'rates': []})
    quarterly_engagement = influencer.get('quarterly_engagement', {'dates': [], 'rates': []})
    
    # Remap the data to match expected frontend keys
    response_data = {
        'post_engagement': {
            'dates': clean_value(post_engagement.get('dates', [])),
            'engagement_rate': clean_value(post_engagement.get('rates', [])),
            'likes': clean_value(post_engagement.get('likes', [])),
            'comments': clean_value(post_engagement.get('comments', []))
        },
        'weekly_engagement': {
            'dates': clean_value(weekly_engagement.get('dates', [])),
            'engagement_rate': clean_value(weekly_engagement.get('rates', [])),
            'likes': clean_value(weekly_engagement.get('likes', [])) if 'likes' in weekly_engagement else [],
            'comments': clean_value(weekly_engagement.get('comments', [])) if 'comments' in weekly_engagement else []
        },
        'monthly_engagement': {
            'dates': clean_value(monthly_engagement.get('dates', [])),
            'engagement_rate': clean_value(monthly_engagement.get('rates', [])),
            'likes': clean_value(monthly_engagement.get('likes', [])) if 'likes' in monthly_engagement else [],
            'comments': clean_value(monthly_engagement.get('comments', [])) if 'comments' in monthly_engagement else []
        },
        'quarterly_engagement': {
            'dates': clean_value(quarterly_engagement.get('dates', [])),
            'engagement_rate': clean_value(quarterly_engagement.get('rates', [])),
            'likes': clean_value(quarterly_engagement.get('likes', [])) if 'likes' in quarterly_engagement else [],
            'comments': clean_value(quarterly_engagement.get('comments', [])) if 'comments' in quarterly_engagement else []
        }
    }
    
    # Additional error handling with try-except
    try:
        return jsonify(response_data)
    except Exception as e:
        print(f"Error serializing data for {username}: {e}")
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
    """Display user's analysis history"""
    data_processor = get_data_processor()
    runs = data_processor.get_runs_history()
    
    return render_template('history.html', runs=runs)

@main_bp.route('/history/<run_id>')
@login_required
def view_historical_run(run_id):
    """View a specific historical analysis run"""
    data_processor = get_data_processor()
    
    # Attempt to load the historical run
    if not data_processor.load_run(run_id):
        flash("Analysis run not found or could not be loaded", "danger")
        return redirect(url_for('main.history'))
    
    # Get the loaded data
    influencers_data = data_processor.influencers_data
    
    # Render the dashboard with historical data
    return render_template('dashboard.html', influencers=influencers_data, historical=True, run_id=run_id)

@main_bp.route('/processing')
@login_required
def processing():
    if 'instagram_urls' not in session:
        flash('Please enter Instagram profile URLs first.', 'warning')
        return redirect(url_for('main.index'))
    
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
        # Get the data processor for the current user
        data_processor = get_data_processor()
        set_analysis_complete(False)  # Reset flag

        update_progress(1, 5, {'parsing': 'working'}, 'Initializing URL processing...')

        # Create ApifyWrapper instance
        try:
            apify_client = ApifyWrapper()
            update_progress(1, 10, {'parsing': 'working'}, 'Connected to Apify API')
        except Exception as e:
            error_msg = f"Failed to initialize Apify client: {str(e)}"
            print(error_msg)
            update_progress(1, 10, {'parsing': 'error'}, error_msg)
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
        user_id = current_user.id
        user_data_dir = os.path.join(current_app.config['DATA_FOLDER'], f'user_{user_id}')
        os.makedirs(user_data_dir, exist_ok=True)
        
        # Scrape profile data
        update_progress(1, 15, {'profile': 'working'}, f'Scraping {len(instagram_urls)} Instagram profiles...')
        try:
            # Remove output_dir parameter as it's not in the method signature
            temp_profile_path = apify_client.scrape_instagram_profiles(instagram_urls)
            
            # Move the temporary file to the user's directory
            profile_filename = f"profiles_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            profile_path = os.path.join(user_data_dir, profile_filename)
            shutil.copy2(temp_profile_path, profile_path)
            os.remove(temp_profile_path)  # Remove the temporary file
            
            update_progress(1, 30, {'profile': 'complete'}, 'Profile data scraped successfully')
        except Exception as e:
            error_msg = f"Failed to scrape profile data: {str(e)}"
            print(error_msg)
            update_progress(1, 30, {'profile': 'error'}, error_msg)
            return
        
        # Scrape posts data
        update_progress(1, 35, {'posts': 'working'}, f'Scraping posts (max {max_posts} per profile)...')
        try:
            # Remove output_dir parameter as it's not in the method signature
            temp_posts_path = apify_client.scrape_instagram_posts(
                instagram_urls, 
                max_posts, 
                posts_newer_than
            )
            
            # Move the temporary file to the user's directory
            posts_filename = f"posts_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            posts_path = os.path.join(user_data_dir, posts_filename)
            shutil.copy2(temp_posts_path, posts_path)
            os.remove(temp_posts_path)  # Remove the temporary file
            
            update_progress(1, 50, {'posts': 'complete'}, 'Posts data scraped successfully')
        except Exception as e:
            error_msg = f"Failed to scrape posts data: {str(e)}"
            print(error_msg)
            update_progress(1, 50, {'posts': 'error'}, error_msg)
            return
        
        # Save paths to background data
        background_data = get_background_data()
        background_data['profile_path'] = profile_path
        background_data['posts_path'] = posts_path
        
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
        
        update_progress(1, 55, {'stats': 'working'}, 'Processing scraped data...')
        
        # Load profile data
        data_processor.load_profile_data(profile_path)
        
        # Load posts data
        data_processor.load_posts_data(posts_path)
        
        # Set countries for influencers
        for username, country in country_mapping.items():
            data_processor.set_country(username, country)
        
        update_progress(1, 60, {'stats': 'working'}, 'Merging and analyzing data...')
        
        # Process data
        data_processor.merge_data()
        data_processor.process_influencer_data()
        
        update_progress(1, 70, {'stats': 'complete'}, 'Basic data processing complete')
        
        # Image processing is now handled in process_influencer_data
        update_progress(2, 80, {'profile_pics': 'complete', 'post_pics': 'complete'}, 'Image processing complete')
        
        # Content analysis with LLM
        update_progress(3, 90, {'captions': 'working'}, 'Analyzing content...')
        
        # Analyze with LLM
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            try:
                data_processor.analyze_with_llm(openai_api_key)
                update_progress(3, 95, {'interests': 'complete', 'brands': 'complete'}, 'Content analysis complete')
            except Exception as e:
                print(f"Error in LLM analysis: {str(e)}")
                update_progress(3, 95, {'interests': 'warning', 'brands': 'warning'}, 'Content analysis completed with warnings')
        else:
            update_progress(3, 95, {'interests': 'warning'}, 'OpenAI API key not found, using basic analysis')
        
        # Engagement metrics calculation already done in process_influencer_data
        update_progress(4, 99, {'rates': 'complete', 'metrics': 'complete'}, 'All metrics calculated')
        
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