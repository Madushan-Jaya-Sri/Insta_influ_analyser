import os
import json
import time
import uuid
import threading
from datetime import datetime
from functools import wraps

from flask import (
    Blueprint, render_template, redirect, url_for, request,
    flash, session, current_app, jsonify, Response, copy_current_request_context
)
from werkzeug.utils import secure_filename
from wtforms import SelectField, validators

from app.models.forms import URLForm, CountryForm, UploadForm
from app.models.data_processor import DataProcessor
from app.models.apify_client_wrapper import ApifyWrapper

main_bp = Blueprint('main', __name__)

# Global data processor
data_processor = DataProcessor()

# Global progress data
progress_data = {
    'step': 0,
    'progress': 0,
    'status': {},
    'message': 'Initializing...',
    'complete': False
}

# Global flag to track analysis completion
analysis_complete = False

processing_lock = threading.Lock()

# Global variables to store data paths for background processing
background_data = {
    'profile_path': None,
    'posts_path': None,
    'country_mapping': {}
}

# Helper function to update progress
def update_progress(step, progress, status=None, message=None, complete=False):
    global progress_data
    with processing_lock:
        progress_data['step'] = step
        progress_data['progress'] = progress
        if status:
            if 'status' not in progress_data:
                progress_data['status'] = {}
            progress_data['status'].update(status)
        if message:
            progress_data['message'] = message
        progress_data['complete'] = complete

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    """Landing page with URL input form"""
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
        global progress_data
        with processing_lock:
            progress_data = {
                'step': 1,
                'progress': 0,
                'status': {},
                'message': 'Initializing data processing...',
                'complete': False
            }
        
        # Start processing in a separate thread
        background_task = copy_current_request_context(lambda: process_urls_in_background(instagram_urls, max_posts, time_filter))
        processing_thread = threading.Thread(target=background_task)
        processing_thread.daemon = True
        processing_thread.start()
        
        return redirect(url_for('main.processing'))
    
    return render_template('index.html', form=form)

@main_bp.route('/upload', methods=['GET', 'POST'])
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
            
            # Save the profile file
            profile_filename = secure_filename(profile_file.filename)
            profile_path = os.path.join(uploads_dir, profile_filename)
            profile_file.save(profile_path)
            
            # Save the posts file
            posts_filename = secure_filename(posts_file.filename)
            posts_path = os.path.join(uploads_dir, posts_filename)
            posts_file.save(posts_path)
            
            # Save the file paths in the session
            session['profile_path'] = profile_path
            session['posts_path'] = posts_path
            
            return redirect(url_for('main.select_countries'))
        
        except Exception as e:
            error = f"Error uploading files: {str(e)}"
    
    return render_template('upload.html', form=form, error=error)

@main_bp.route('/select-countries', methods=['GET', 'POST'])
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
            
            session['country_mapping'] = country_mapping
            
            # Reset progress data
            global progress_data
            with processing_lock:
                progress_data = {
                    'step': 1,
                    'progress': 0,
                    'status': {},
                    'message': 'Initializing data processing...',
                    'complete': False
                }
            
            # Create local variables from session data
            profile_path = session['profile_path']
            posts_path = session['posts_path']
            
            # Start processing in a separate thread
            background_task = copy_current_request_context(lambda: process_data_in_background(profile_path, posts_path, country_mapping))
            processing_thread = threading.Thread(target=background_task)
            processing_thread.daemon = True
            processing_thread.start()
            
            return redirect(url_for('main.processing'))
            
        except Exception as e:
            error = f"Error processing country selections: {str(e)}"
    
    # Render the country selection form
    return render_template('select_countries.html', form=form, error=error, usernames=usernames)

@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard displaying influencer analysis"""
    global data_processor
    global analysis_complete
    
    # Check if we have processed data in memory or saved
    if data_processor.influencers_data:
        analysis_complete = True
        influencers_data = data_processor.influencers_data
        return render_template('dashboard.html', influencers=influencers_data)
    else:
        # No data available
        flash("Please complete the analysis first", 'warning')
        return redirect(url_for('main.index'))

@main_bp.route('/influencer/<username>')
def influencer_detail(username):
    """Detailed view for a specific influencer"""
    if not analysis_complete:
        flash("Please complete the analysis first", 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Get data from the global data processor
    global data_processor
    influencer = data_processor.influencers_data.get(username)
    
    if not influencer:
        flash(f"Influencer @{username} not found", 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('influencer_detail.html', influencer=influencer)

@main_bp.route('/api/influencer/<username>')
def influencer_api(username):
    """API endpoint for fetching influencer data for charts"""
    if not analysis_complete:
        return jsonify({'error': 'Analysis not complete. Please process data first.'}), 400
    
    # Get data from the global data processor
    global data_processor
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

@main_bp.route('/processing')
def processing():
    if 'instagram_urls' not in session:
        flash('Please enter Instagram profile URLs first.', 'warning')
        return redirect(url_for('main.index'))
    
    return render_template('processing.html')

@main_bp.route('/progress-stream')
def progress_stream():
    def generate():
        last_data = None
        retry_count = 0
        while True:
            try:
                with processing_lock:
                    current_data = json.dumps(progress_data)
                    
                if current_data != last_data:
                    last_data = current_data
                    yield f"data: {current_data}\n\n"
                    retry_count = 0
                
                if progress_data['complete']:
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
        # Use the existing global data processor
        global data_processor
        global analysis_complete
        
        update_progress(1, 5, {'parsing': 'working'}, 'Parsing JSON files...')
        time.sleep(0.5)  # Simulate processing time
        
        # Load profile data
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
        
        # Process data
        data_processor.merge_data()
        data_processor.process_influencer_data()
        
        update_progress(1, 70, {'stats': 'complete'}, 'Basic data processing complete')
        
        # Image processing
        update_progress(2, 75, {'profile_pics': 'working'}, 'Downloading profile pictures...')
        time.sleep(0.5)  # Simulate processing time
        
        # Download images is now handled in process_influencer_data
        # No need to call download_images separately
        
        update_progress(2, 80, {'profile_pics': 'complete', 'post_pics': 'working'}, 'Downloading post images...')
        time.sleep(0.5)  # Simulate processing time
        
        update_progress(2, 85, {'post_pics': 'complete', 'optimize': 'working'}, 'Optimizing images...')
        time.sleep(0.5)  # Simulate processing time
        
        update_progress(2, 90, {'optimize': 'complete'}, 'Image processing complete')
        
        # Content analysis with LLM
        update_progress(3, 91, {'captions': 'working'}, 'Analyzing captions and hashtags...')
        time.sleep(0.5)  # Simulate processing time
        
        update_progress(3, 93, {'captions': 'complete', 'interests': 'working'}, 'Identifying main interests...')
        time.sleep(0.5)  # Simulate processing time
        
        # Analyze with LLM
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if openai_api_key:
            data_processor.analyze_with_llm(openai_api_key)
        
        update_progress(3, 95, {'interests': 'complete', 'brands': 'working'}, 'Identifying brand affiliations...')
        time.sleep(0.5)  # Simulate processing time
        
        update_progress(3, 97, {'brands': 'complete'}, 'Content analysis complete')
        
        # Engagement metrics calculation
        update_progress(4, 98, {'rates': 'working'}, 'Computing engagement rates...')
        time.sleep(0.5)  # Simulate processing time
        
        # Calculate engagement metrics
        # Engagement metrics already calculated in process_influencer_data
        
        update_progress(4, 99, {'rates': 'complete', 'metrics': 'working'}, 'Generating time-based metrics...')
        time.sleep(0.5)  # Simulate processing time
        
        update_progress(4, 99.5, {'metrics': 'complete', 'visualization': 'working'}, 'Preparing visualization data...')
        time.sleep(0.5)  # Simulate processing time
        
        # Set the analysis complete flag using the global variable
        analysis_complete = True
        
        update_progress(4, 100, {'visualization': 'complete'}, 'Processing complete!', True)
        
    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        update_progress(
            max(progress_data['step'], 1),  # Keep current step
            progress_data['progress'],  # Keep current progress
            None,
            f"Error during processing: {str(e)}",
            False
        )

# New function to process Instagram URLs
def process_urls_in_background(instagram_urls, max_posts, time_filter):
    try:
        # Use the existing global data processor
        global data_processor
        global analysis_complete
        global background_data
        
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
        
        # Scrape profile data
        update_progress(1, 15, {'profile': 'working'}, f'Scraping {len(instagram_urls)} Instagram profiles...')
        try:
            profile_path = apify_client.scrape_instagram_profiles(instagram_urls)
            update_progress(1, 30, {'profile': 'complete'}, 'Profile data scraped successfully')
        except Exception as e:
            error_msg = f"Failed to scrape profile data: {str(e)}"
            print(error_msg)
            update_progress(1, 30, {'profile': 'error'}, error_msg)
            return
        
        # Scrape posts data
        update_progress(1, 35, {'posts': 'working'}, f'Scraping posts (max {max_posts} per profile)...')
        try:
            posts_path = apify_client.scrape_instagram_posts(instagram_urls, max_posts, posts_newer_than)
            update_progress(1, 50, {'posts': 'complete'}, 'Posts data scraped successfully')
        except Exception as e:
            error_msg = f"Failed to scrape posts data: {str(e)}"
            print(error_msg)
            update_progress(1, 50, {'posts': 'error'}, error_msg)
            return
        
        # Save paths to global variable instead of session
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
        
        # Store country mapping in global variable instead of session
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
        
        # Set the analysis complete flag using the global variable
        analysis_complete = True
        
        update_progress(4, 100, {'visualization': 'complete'}, 'Processing complete!', True)
        
    except Exception as e:
        print(f"Error in background processing: {str(e)}")
        update_progress(
            max(progress_data['step'], 1),  # Keep current step
            progress_data['progress'],  # Keep current progress
            None,
            f"Error during processing: {str(e)}",
            False
        ) 

# Add a new route for clearing data
@main_bp.route('/clear-data', methods=['POST'])
def clear_data():
    """Clear all processed data"""
    global data_processor
    global analysis_complete
    
    if request.method == 'POST':
        try:
            # Clear data processor data
            result = data_processor.clear_processed_data()
            
            # Reset the analysis complete flag
            analysis_complete = False
            
            if result:
                flash("All analysis data has been cleared successfully.", 'success')
            else:
                flash("Failed to clear analysis data. Please try again.", 'danger')
        except Exception as e:
            flash(f"Error clearing data: {str(e)}", 'danger')
    
    return redirect(url_for('main.index')) 