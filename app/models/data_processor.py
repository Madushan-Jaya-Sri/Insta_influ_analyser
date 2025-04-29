import pandas as pd
import numpy as np
import json
import os
import datetime
import traceback
from wordcloud import WordCloud
import matplotlib
matplotlib.use('Agg')  # Set non-interactive backend globally
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from collections import defaultdict, Counter
import requests
import shutil # Added for clear_data potential image deletion
import uuid # For unique run IDs
from app.models.database import db
from app.models.models import Influencer, Analysis, UserSettings

# Define the path for the data file relative to the script's location
# This assumes run.py is in the root and calls create_app which sets up paths
# A more robust way might involve passing the data path from the app config
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DATA_DIR = os.path.join(APP_ROOT, 'data')
DEFAULT_IMAGES_PATH = os.path.join(APP_ROOT, 'static', 'images')


class DataProcessor:
    def __init__(self, user_id=None, data_dir=DEFAULT_DATA_DIR):
        self.profile_data = None
        self.posts_data = None
        self.merged_data = None
        self.influencers_data = {}
        self.countries = {}
        self.data_dir = data_dir
        self.user_id = user_id
        
        # Create user-specific data directory if a user_id is provided
        if user_id:
            self.user_data_dir = os.path.join(self.data_dir, f'user_{user_id}')
            os.makedirs(self.user_data_dir, exist_ok=True)
            
            # Create user-specific image directory
            self.user_images_dir = os.path.join(DEFAULT_IMAGES_PATH, f'user_{user_id}')
            os.makedirs(os.path.join(self.user_images_dir, 'profiles'), exist_ok=True)
            os.makedirs(os.path.join(self.user_images_dir, 'posts'), exist_ok=True)
            os.makedirs(os.path.join(self.user_images_dir, 'misc'), exist_ok=True)
        else:
            # Fallback to global data file for backward compatibility
            self.user_data_dir = self.data_dir
            self.user_images_dir = DEFAULT_IMAGES_PATH
            
        self._load_persistent_data()
        
    def _load_persistent_data(self):
        """Load data from the SQLite database if the user is authenticated."""
        if self.user_id:
            try:
                # Query the database for influencers
                influencers = Influencer.query.filter_by(
                    user_id=self.user_id,
                    is_deleted=False
                ).all()
                
                # Convert to dictionary for compatibility with existing code
                self.influencers_data = {}
                for influencer in influencers:
                    # Load the most recent analysis for this influencer
                    recent_analysis = Analysis.query.filter_by(
                        influencer_id=influencer.id,
                        is_deleted=False
                    ).order_by(Analysis.created_at.desc()).first()
                    
                    # Get the results from the analysis or set an empty dict
                    results = recent_analysis.results if recent_analysis else {}
                    
                    # Create the influencer data structure
                    self.influencers_data[influencer.username] = {
                        'username': influencer.username,
                        'full_name': influencer.full_name,
                        'followers_count': influencer.followers_count,
                        'following_count': influencer.following_count,
                        'posts_count': influencer.posts_count,
                        'bio': influencer.bio,
                        'is_private': influencer.is_private,
                        'profile_url': influencer.profile_url,
                        'country': results.get('country', ''),
                        'analysis': results,
                    }
                
                # Rebuild countries mapping from loaded data
                self.countries = {username: data.get('country', '') 
                                  for username, data in self.influencers_data.items()}
                
                print(f"Loaded {len(self.influencers_data)} influencers from database for user {self.user_id}")
            except Exception as e:
                print(f"Error loading data from database: {e}")
                traceback.print_exc()
                # If loading fails, start fresh
                self.influencers_data = {}
                self.countries = {}
        else:
            print("No user ID provided. Starting with empty data.")
            self.influencers_data = {}
            self.countries = {}
    
    def _save_persistent_data(self):
        """Save the current influencers_data to the database."""
        if not self.user_id:
            print("Cannot save data: No user ID provided")
            return

        try:
            for username, data in self.influencers_data.items():
                # Check if influencer already exists in the database
                influencer = Influencer.query.filter_by(
                    user_id=self.user_id,
                    username=username,
                    is_deleted=False
                ).first()
                
                if not influencer:
                    # Create new influencer record
                    influencer = Influencer(
                        user_id=self.user_id,
                        username=username,
                        full_name=data.get('full_name', ''),
                        profile_url=data.get('profile_url', f'https://instagram.com/{username}'),
                        followers_count=data.get('followers_count', 0),
                        following_count=data.get('following_count', 0),
                        posts_count=data.get('posts_count', 0),
                        bio=data.get('bio', ''),
                        is_private=data.get('is_private', False),
                        last_updated=datetime.datetime.now()
                    )
                    db.session.add(influencer)
                    db.session.flush()  # Flush to get the influencer ID
                else:
                    # Update existing influencer
                    influencer.full_name = data.get('full_name', influencer.full_name)
                    influencer.followers_count = data.get('followers_count', influencer.followers_count)
                    influencer.following_count = data.get('following_count', influencer.following_count)
                    influencer.posts_count = data.get('posts_count', influencer.posts_count)
                    influencer.bio = data.get('bio', influencer.bio)
                    influencer.is_private = data.get('is_private', influencer.is_private)
                    influencer.last_updated = datetime.datetime.now()
                
                # Add an analysis record with the full data
                if 'analysis' in data:
                    analysis = Analysis(
                        user_id=self.user_id,
                        influencer_id=influencer.id,
                        analysis_type='full',
                        results={
                            'country': data.get('country', ''),
                            **data.get('analysis', {})
                        }
                    )
                    db.session.add(analysis)
            
            # Commit all changes
            db.session.commit()
            print(f"Saved {len(self.influencers_data)} influencers to database for user {self.user_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error saving data to database: {e}")
            traceback.print_exc()
    
    def get_runs_history(self):
        """Get the history of analysis runs from the database"""
        if not self.user_id:
            return []
            
        try:
            # Get all analysis timestamps from the database
            analysis_records = db.session.query(
                Analysis.created_at,
                db.func.count(db.distinct(Analysis.influencer_id)).label('influencer_count')
            ).filter_by(
                user_id=self.user_id,
                is_deleted=False
            ).group_by(
                db.func.date(Analysis.created_at)
            ).order_by(
                Analysis.created_at.desc()
            ).all()
            
            # Format each record for display
            runs_history = []
            for record in analysis_records:
                timestamp = record.created_at
                run_id = timestamp.strftime('%Y%m%d%H%M')
                
                # Get list of influencers for this run date
                influencer_ids = Analysis.query.filter(
                    Analysis.user_id == self.user_id,
                    db.func.date(Analysis.created_at) == db.func.date(timestamp)
                ).with_entities(Analysis.influencer_id).distinct().all()
                
                influencer_usernames = []
                countries = []
                for id_tuple in influencer_ids:
                    influencer = Influencer.query.get(id_tuple[0])
                    if influencer:
                        influencer_usernames.append(influencer.username)
                        
                        # Get analysis for this influencer
                        analysis = Analysis.query.filter_by(
                            user_id=self.user_id,
                            influencer_id=influencer.id
                        ).order_by(Analysis.created_at.desc()).first()
                        
                        if analysis and analysis.results and 'country' in analysis.results:
                            countries.append(analysis.results['country'])
                
                # Deduplicate countries
                countries = list(set(filter(None, countries)))
                
                runs_history.append({
                    'run_id': run_id,
                    'timestamp': timestamp.isoformat(),
                    'formatted_date': timestamp.strftime('%B %d, %Y %I:%M %p'),
                    'influencer_count': record.influencer_count,
                    'influencers': influencer_usernames[:5] + ['...'] if len(influencer_usernames) > 5 else influencer_usernames,
                    'countries': countries
                })
            
            return runs_history
        
        except Exception as e:
            print(f"Error getting runs history from database: {e}")
            traceback.print_exc()
            return []
            
    def load_run(self, run_id):
        """Load a specific historical run from the database"""
        if not self.user_id:
            return False
        
        try:
            # Parse the run_id to get the date
            run_date = datetime.datetime.strptime(run_id, '%Y%m%d%H%M')
            
            # Find all analyses for this date
            analyses = Analysis.query.filter(
                Analysis.user_id == self.user_id,
                db.func.date(Analysis.created_at) == db.func.date(run_date)
            ).all()
            
            if not analyses:
                return False
            
            # Reset the current data
            self.influencers_data = {}
            self.countries = {}
            
            # Load data for each influencer in this run
            for analysis in analyses:
                influencer = Influencer.query.get(analysis.influencer_id)
                if influencer:
                    country = analysis.results.get('country', '') if analysis.results else ''
                    
                    self.influencers_data[influencer.username] = {
                        'username': influencer.username,
                        'full_name': influencer.full_name,
                        'followers_count': influencer.followers_count,
                        'following_count': influencer.following_count,
                        'posts_count': influencer.posts_count,
                        'bio': influencer.bio,
                        'is_private': influencer.is_private,
                        'profile_url': influencer.profile_url,
                        'country': country,
                        'analysis': analysis.results or {}
                    }
                    
                    if country:
                        self.countries[influencer.username] = country
            
            return True
            
        except Exception as e:
            print(f"Error loading run from database: {e}")
            traceback.print_exc()
            return False
    
    def _json_serializer(self, obj):
        """JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.isoformat()
        elif isinstance(obj, np.int64):
            return int(obj)
        elif isinstance(obj, np.float64):
            return float(obj)
        elif pd.isna(obj):
            return None
        raise TypeError(f"Type {type(obj)} not serializable")

    def clear_all_data(self, clear_images=False):
        """Clear all data for the current user"""
        if not self.user_id:
            return
            
        try:
            # Set is_deleted=True for all user's influencers and analyses
            Influencer.query.filter_by(user_id=self.user_id).update({'is_deleted': True})
            Analysis.query.filter_by(user_id=self.user_id).update({'is_deleted': True})
            db.session.commit()
            
            # Reset in-memory data
            self.influencers_data = {}
            self.countries = {}
            
            # Optionally clear images
            if clear_images:
                self._clear_user_images()
                
            print(f"Cleared all data for user {self.user_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing data: {e}")
            traceback.print_exc()
            
    def _clear_user_images(self):
        """Clear images for a user"""
        if self.user_id and os.path.exists(self.user_images_dir):
            try:
                shutil.rmtree(self.user_images_dir)
                # Recreate empty directories
                os.makedirs(os.path.join(self.user_images_dir, 'profiles'), exist_ok=True)
                os.makedirs(os.path.join(self.user_images_dir, 'posts'), exist_ok=True)
                os.makedirs(os.path.join(self.user_images_dir, 'misc'), exist_ok=True)
                print(f"Cleared images for user {self.user_id}")
            except Exception as e:
                print(f"Error clearing images: {e}")
                traceback.print_exc()

    def load_profile_data(self, file_path):
        """Load the Instagram profile data JSON file"""
        # Clear existing data before loading new profiles
        self.profile_data = None
        self.posts_data = None
        self.merged_data = None
        # Don't clear influencers_data here if we want to merge with existing persistent data
        # If each load should replace everything, uncomment the next two lines:
        # self.influencers_data = {}
        # self.countries = {}
        print("Cleared previous in-memory data before loading new profiles.")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.profile_data = pd.DataFrame(data)
            print(f"Profile data loaded: {len(self.profile_data)} rows")
            return self.profile_data['username'].tolist()
        except Exception as e:
            print(f"Error in load_profile_data: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Error loading profile data: {str(e)}")
    
    def load_posts_data(self, file_path):
        """Load the Instagram posts data JSON file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.posts_data = pd.DataFrame(data)
            print(f"Posts data loaded: {len(self.posts_data)} rows")
            return True
        except Exception as e:
            print(f"Error in load_posts_data: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Error loading posts data: {str(e)}")
    
    def merge_data(self):
        """Merge the profile and posts data"""
        if self.profile_data is None or self.posts_data is None:
            raise Exception("Profile and posts data must be loaded first")
        
        try:
            print("Starting data merge")
            print(f"Profile data columns: {self.profile_data.columns.tolist()}")
            print(f"Posts data columns: {self.posts_data.columns.tolist()}")
            
            self.merged_data = pd.merge(
                self.profile_data, 
                self.posts_data, 
                how='right', 
                left_on='username', 
                right_on='ownerUsername'
            )
            print(f"Merged data: {len(self.merged_data)} rows")
            return True
        except Exception as e:
            print(f"Error in merge_data: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Error merging data: {str(e)}")
    
    def set_country(self, username, country):
        """Set the country for a specific influencer"""
        self.countries[username] = country
        print(f"Set country for {username}: {country}")
    
    def download_profile_image(self, username, profile_pic_url):
        """Download profile image for a specific influencer using username as filename"""
        if not profile_pic_url or pd.isna(profile_pic_url):
            print(f"No profile picture URL for {username}")
            return None
        
        # Use user-specific directory if user_id is set
        if self.user_id:
            save_dir = os.path.join(self.user_images_dir, 'profiles')
        else:
            save_dir = os.path.join(DEFAULT_IMAGES_PATH, 'profiles')
            
        # Create profiles directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Use username as the filename
        filename = f"{username}.jpg"
        local_path = os.path.join(save_dir, filename)
        
        # Get the relative path for template usage
        if self.user_id:
            rel_path = os.path.join(f'images/user_{self.user_id}/profiles', filename)
        else:
            rel_path = os.path.join('images/profiles', filename)
        
        # Check if the profile image already exists
        if os.path.exists(local_path):
            print(f"Profile image for {username} already exists at {local_path}")
            return rel_path
        
        # Download image if it doesn't exist
        try:
            response = requests.get(profile_pic_url, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded profile image for {username} to {local_path}")
                return rel_path
            else:
                print(f"Failed to download profile image for {username}: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading profile image for {username}: {str(e)}")
            traceback.print_exc()
            return None

    def download_post_image(self, post_id, display_url):
        """Download post image using post ID as the filename"""
        if not display_url or pd.isna(display_url):
            print(f"No display URL for post {post_id}")
            return None
        
        # Use user-specific directory if user_id is set
        if self.user_id:
            save_dir = os.path.join(self.user_images_dir, 'posts')
        else:
            save_dir = os.path.join(DEFAULT_IMAGES_PATH, 'posts')
            
        # Create posts directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)
        
        # Use post ID as the filename
        filename = f"{post_id}.jpg"
        local_path = os.path.join(save_dir, filename)
        
        # Get the relative path for template usage
        if self.user_id:
            rel_path = os.path.join(f'images/user_{self.user_id}/posts', filename)
        else:
            rel_path = os.path.join('images/posts', filename)
        
        # Check if the post image already exists
        if os.path.exists(local_path):
            print(f"Post image {post_id} already exists at {local_path}")
            return rel_path
        
        # Download image if it doesn't exist
        try:
            response = requests.get(display_url, timeout=10)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"Downloaded post image {post_id} to {local_path}")
                return rel_path
            else:
                print(f"Failed to download post image {post_id}: Status code {response.status_code}")
                return None
        except Exception as e:
            print(f"Error downloading post image {post_id}: {str(e)}")
            traceback.print_exc()
            return None

    def download_images(self, image_urls, save_dir='app/static/images/misc'):
        """Legacy method for batch downloading images - kept for backward compatibility"""
        os.makedirs(save_dir, exist_ok=True)
        local_paths = []
        
        for i, url in enumerate(image_urls):
            try:
                if not url or pd.isna(url):
                    print(f"Skipping empty URL at index {i}")
                    continue
                    
                # Create a unique filename based on the URL
                filename = f"img_{abs(hash(url))}.jpg"
                local_path = os.path.join(save_dir, filename)
                rel_path = os.path.join('images/misc', filename)
                
                # Check if the image already exists
                if os.path.exists(local_path):
                    print(f"Image already exists, skipping download: {local_path}")
                    local_paths.append(rel_path)
                    continue
                    
                # Download image if it doesn't exist
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Store the relative path for use with url_for in templates
                    local_paths.append(rel_path)
                    print(f"Downloaded {url} to {local_path}")
                else:
                    print(f"Failed to download {url}: Status code {response.status_code}")
            except Exception as e:
                print(f"Error downloading {url}: {str(e)}")
                traceback.print_exc()
        
        return local_paths
    
    def process_influencer_data(self):
        """Process data for each influencer"""
        if self.merged_data is None:
            raise Exception("Data must be merged first")
        
        print("Starting process_influencer_data")
        influencers = {}
        
        # Group data by username
        try:
            grouped_data = self.merged_data.groupby('username')
            print(f"Found {len(grouped_data)} influencer groups")
            
            for username, group in grouped_data:
                print(f"Processing influencer: {username}")
                if username not in self.countries:
                    print(f"Skipping {username} - no country set")
                    continue
                    
                # Basic information
                print(f"Creating basic info for {username}")
                try:
                    # Check for any problematic data types
                    for col in ['followersCount', 'followsCount', 'postsCount']:
                        val = group[col].iloc[0]
                        print(f"{username} {col}: {val} (type: {type(val)})")
                        if isinstance(val, np.ndarray):
                            print(f"Warning: {col} is an ndarray with shape {val.shape}")
                    
                    influencer = {
                        'username': username,
                        'country': self.countries.get(username, ''),
                        'full_name': group['fullName'].iloc[0],
                        'biography': group['biography'].iloc[0],
                        'business_category': group['businessCategoryName'].iloc[0],
                        'followers_count': group['followersCount'].iloc[0],
                        'follows_count': group['followsCount'].iloc[0],
                        'posts_count': group['postsCount'].iloc[0],
                        'profile_pic_url': group['profilePicUrl'].iloc[0],
                        'is_verified': bool(group['verified'].iloc[0]),
                        'external_url': group.get('externalUrl', {}).iloc[0] if 'externalUrl' in group.columns else None,
                    }
                    
                    # Ensure numeric values are scalar
                    for key in ['followers_count', 'follows_count', 'posts_count']:
                        if hasattr(influencer[key], 'item'):
                            print(f"Converting {key} from {type(influencer[key])} to scalar")
                            influencer[key] = influencer[key].item()
                    
                except Exception as e:
                    print(f"Error creating basic info for {username}: {str(e)}")
                    traceback.print_exc()
                    continue
                
                # Download profile picture
                if pd.notna(influencer['profile_pic_url']):
                    influencer['profile_pic_local'] = self.download_profile_image(username, influencer['profile_pic_url'])
                    print(f"Downloaded profile picture for {username}: {influencer['profile_pic_local']}")
                else:
                    influencer['profile_pic_local'] = None
                
                # Process posts
                posts = []
                all_captions = []
                all_hashtags = []
                all_mentions = []
                engagement_data = []
                
                print(f"Processing {len(group)} posts for {username}")
                for idx, (_, post) in enumerate(group.iterrows()):
                    if idx % 20 == 0:
                        print(f"Processing post {idx+1}/{len(group)} for {username}")
                    
                    # Combine all captions for LLM analysis
                    if pd.notna(post.get('caption')):
                        all_captions.append(post['caption'])
                    
                    # SAFELY process hashtags - NO ambiguous truth value checks
                    try:
                        hashtags = post.get('hashtags')
                        # Only proceed if hashtags exists
                        if hashtags is not None:
                            # Handle different data types without any ambiguous truth checks
                            if isinstance(hashtags, list):
                                all_hashtags.extend(hashtags)
                            elif isinstance(hashtags, np.ndarray):
                                if hashtags.size == 1:
                                    # Single item array - extract and use if it's a list
                                    item = hashtags.item()
                                    if isinstance(item, list):
                                        all_hashtags.extend(item)
                                    else:
                                        # If a single non-list item, add directly
                                        all_hashtags.append(item)
                                elif hashtags.size > 1:
                                    # Multi-item array - convert to list
                                    all_hashtags.extend(hashtags.tolist())
                    except Exception as e:
                        print(f"Error processing hashtags for post {idx}: {str(e)}")
                        traceback.print_exc()
                    
                    # SAFELY process mentions - NO ambiguous truth value checks
                    try:
                        mentions = post.get('mentions')
                        # Only proceed if mentions exists
                        if mentions is not None:
                            # Handle different data types without any ambiguous truth checks
                            if isinstance(mentions, list):
                                all_mentions.extend(mentions)
                            elif isinstance(mentions, np.ndarray):
                                if mentions.size == 1:
                                    # Single item array - extract and use if it's a list
                                    item = mentions.item()
                                    if isinstance(item, list):
                                        all_mentions.extend(item)
                                    else:
                                        # If a single non-list item, add directly
                                        all_mentions.append(item)
                                elif mentions.size > 1:
                                    # Multi-item array - convert to list
                                    all_mentions.extend(mentions.tolist())
                    except Exception as e:
                        print(f"Error processing mentions for post {idx}: {str(e)}")
                        traceback.print_exc()
                    
                    # Calculate engagement rate
                    try:
                        # Get the basic values
                        likes_count = post.get('likesCount', 0)
                        comments_count = post.get('commentsCount', 0)
                        followers_count = influencer['followers_count']
                        timestamp = post.get('timestamp', None)
                        
                        # Ensure values are numeric and convert if needed
                        if hasattr(likes_count, 'item'):
                            likes_count = likes_count.item()
                        if hasattr(comments_count, 'item'):
                            comments_count = comments_count.item()
                        
                        # Convert to float for calculation
                        likes_count = float(likes_count) if isinstance(likes_count, (int, float, np.number)) else 0
                        comments_count = float(comments_count) if isinstance(comments_count, (int, float, np.number)) else 0
                        followers_count = float(followers_count)
                        
                        # Only add to engagement data if we have all necessary values and followers > 0
                        if followers_count > 0 and pd.notna(timestamp):
                            # Calculate engagement rate as (likes + comments) / followers * 100
                            engagement_rate = (likes_count + comments_count) / followers_count * 100
                            
                            # Convert timestamp to datetime object if it's not already
                            if isinstance(timestamp, (int, float)):
                                post_date = datetime.datetime.fromtimestamp(timestamp)
                            elif isinstance(timestamp, str):
                                post_date = pd.to_datetime(timestamp)
                            else:
                                post_date = pd.to_datetime(timestamp)
                            
                            engagement_data.append({
                                'date': post_date,
                                'engagement_rate': engagement_rate,
                                'likes': likes_count,
                                'comments': comments_count
                            })
                    except Exception as e:
                        print(f"Error in engagement calculation for post {idx}: {str(e)}")
                        traceback.print_exc()
                    
                    try:
                        # Get a sample of posts with images
                        if pd.notna(post.get('displayUrl')):
                            # Convert numerical values to Python native types to prevent serialization issues
                            likes_count = post.get('likesCount', 0)
                            if hasattr(likes_count, 'item'):
                                # Handle multi-element arrays
                                if isinstance(likes_count, np.ndarray) and likes_count.size > 1:
                                    likes_count = float(np.mean(likes_count))
                                else:
                                    likes_count = likes_count.item()
                                
                            comments_count = post.get('commentsCount', 0)
                            if hasattr(comments_count, 'item'):
                                # Handle multi-element arrays
                                if isinstance(comments_count, np.ndarray) and comments_count.size > 1:
                                    comments_count = float(np.mean(comments_count))
                                else:
                                    comments_count = comments_count.item()
                            
                            # Ensure values are scalar
                            likes_count = float(likes_count) if isinstance(likes_count, (int, float, np.number)) else 0
                            comments_count = float(comments_count) if isinstance(comments_count, (int, float, np.number)) else 0
                            
                            # Only download the first 5 post images to conserve resources
                            if len(posts) < 5:
                                # Get post ID safely
                                post_id = post.get('id', f"{username}_{idx}")
                                # Download the post image
                                post_image_local = self.download_post_image(post_id, post.get('displayUrl'))
                            else:
                                post_image_local = None
                            
                            posts.append({
                                'id': post.get('id', ''),
                                'shortCode': post.get('shortCode', ''),
                                'caption': post.get('caption', ''),
                                'likes_count': likes_count,
                                'comments_count': comments_count,
                                'display_url': post.get('displayUrl', ''),
                                'display_url_local': post_image_local,
                                'timestamp': post.get('timestamp', ''),
                            })
                    except Exception as e:
                        print(f"Error processing post display for post {idx}: {str(e)}")
                        traceback.print_exc()
                
                # Store all processed data
                influencer['posts'] = posts[:5]  # Only store 5 sample posts
                influencer['all_captions'] = ' '.join(all_captions)
                
                # Hashtag analysis
                hashtag_counts = Counter(all_hashtags)
                influencer['top_hashtags'] = dict(hashtag_counts.most_common(10))
                influencer['hashtags_wordcloud'] = self._generate_wordcloud(hashtag_counts) if hashtag_counts else None
                
                # Mentions analysis
                mention_counts = Counter(all_mentions)
                influencer['top_mentions'] = dict(mention_counts.most_common(10))
                
                # Engagement analysis
                try:
                    if engagement_data:
                        print(f"Processing engagement data for {username}: {len(engagement_data)} data points")
                        # Convert to DataFrame for easier manipulation
                        engagement_df = pd.DataFrame(engagement_data)
                        print(f"Engagement DataFrame columns: {engagement_df.columns.tolist()}")
                        
                        # Ensure date column is datetime type and sort
                        engagement_df['date'] = pd.to_datetime(engagement_df['date'])
                        engagement_df = engagement_df.sort_values('date')
                        
                        # Create a formatted version of the dates for display
                        engagement_df['date_str'] = engagement_df['date'].dt.strftime('%Y-%m-%d')
                        
                        # Handle NaN values in numeric columns
                        engagement_df['engagement_rate'] = engagement_df['engagement_rate'].fillna(0)
                        engagement_df['likes'] = engagement_df['likes'].fillna(0)
                        engagement_df['comments'] = engagement_df['comments'].fillna(0)
                        
                        # Basic daily engagement (post by post)
                        influencer['post_engagement'] = {
                            'dates': engagement_df['date_str'].tolist(),
                            'rates': engagement_df['engagement_rate'].tolist(),
                            'engagement_rate': engagement_df['engagement_rate'].tolist(),  # Add for frontend compatibility
                            'likes': engagement_df['likes'].tolist(),
                            'comments': engagement_df['comments'].tolist()
                        }
                        
                        # Weekly engagement
                        if len(engagement_df) > 1:  # Only aggregate if we have more than one data point
                            # Set up numeric-only DataFrame for resampling
                            numeric_df = engagement_df.set_index('date')
                            numeric_cols = ['engagement_rate', 'likes', 'comments']
                            
                            # Weekly - keep only numeric columns for resampling
                            weekly_data = numeric_df[numeric_cols].resample('W').mean()
                            weekly_data.reset_index(inplace=True)
                            weekly_data['date_str'] = weekly_data['date'].dt.strftime('%Y-%m-%d')
                            
                            # Handle NaN values in resampled data
                            weekly_data = weekly_data.fillna(0)
                            
                            influencer['weekly_engagement'] = {
                                'dates': weekly_data['date_str'].tolist(),
                                'rates': weekly_data['engagement_rate'].tolist(),
                                'engagement_rate': weekly_data['engagement_rate'].tolist(),  # Add for frontend compatibility
                                'likes': weekly_data['likes'].tolist(),
                                'comments': weekly_data['comments'].tolist()
                            }
                            
                            # Monthly engagement
                            monthly_data = numeric_df[numeric_cols].resample('M').mean()
                            monthly_data.reset_index(inplace=True)
                            monthly_data['date_str'] = monthly_data['date'].dt.strftime('%Y-%m-%d')
                            
                            # Handle NaN values in monthly data
                            monthly_data = monthly_data.fillna(0)
                            
                            influencer['monthly_engagement'] = {
                                'dates': monthly_data['date_str'].tolist(),
                                'rates': monthly_data['engagement_rate'].tolist(),
                                'engagement_rate': monthly_data['engagement_rate'].tolist(),  # Add for frontend compatibility
                                'likes': monthly_data['likes'].tolist(),
                                'comments': monthly_data['comments'].tolist()
                            }
                            
                            # Quarterly engagement
                            quarterly_data = numeric_df[numeric_cols].resample('Q').mean()
                            quarterly_data.reset_index(inplace=True)
                            quarterly_data['date_str'] = quarterly_data['date'].dt.strftime('%Y-%m-%d')
                            
                            # Handle NaN values in quarterly data
                            quarterly_data = quarterly_data.fillna(0)
                            
                            influencer['quarterly_engagement'] = {
                                'dates': quarterly_data['date_str'].tolist(),
                                'rates': quarterly_data['engagement_rate'].tolist(),
                                'engagement_rate': quarterly_data['engagement_rate'].tolist(),  # Add for frontend compatibility
                                'likes': quarterly_data['likes'].tolist(),
                                'comments': quarterly_data['comments'].tolist()
                            }
                        else:
                            # If there's just one post, use the same data for all timeframes
                            influencer['weekly_engagement'] = influencer['post_engagement']
                            influencer['monthly_engagement'] = influencer['post_engagement']
                            influencer['quarterly_engagement'] = influencer['post_engagement']
                        
                        # Overall engagement stats
                        influencer['avg_engagement_rate'] = float(engagement_df['engagement_rate'].mean())
                        influencer['max_engagement_rate'] = float(engagement_df['engagement_rate'].max())
                        influencer['avg_likes'] = float(engagement_df['likes'].mean())
                        influencer['avg_comments'] = float(engagement_df['comments'].mean())
                except Exception as e:
                    print(f"Error in engagement analysis for {username}: {str(e)}")
                    traceback.print_exc()
                    # Set fallback values in case of error
                    influencer['post_engagement'] = {'dates': [], 'rates': [], 'engagement_rate': [], 'likes': [], 'comments': []}
                    influencer['weekly_engagement'] = {'dates': [], 'rates': [], 'engagement_rate': [], 'likes': [], 'comments': []}
                    influencer['monthly_engagement'] = {'dates': [], 'rates': [], 'engagement_rate': [], 'likes': [], 'comments': []}
                    influencer['quarterly_engagement'] = {'dates': [], 'rates': [], 'engagement_rate': [], 'likes': [], 'comments': []}
                
                influencers[username] = influencer
                print(f"Completed processing for {username}")
            
        except Exception as e:
            print(f"Error in process_influencer_data: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Error processing data: {str(e)}")
        
        self.influencers_data = influencers
        print(f"Processed {len(influencers)} influencers successfully")

        # Save the processed data
        self._save_persistent_data()

        return influencers
    
    def analyze_with_llm(self, openai_api_key):
        """Analyze influencer content using OpenAI LLM"""
        print("Starting LLM analysis")
        
        # Try importing OpenAI and setting up client with proper method
        api_available = False
        
        try:
            import openai
            openai.api_key = openai_api_key
            api_available = True
            print("Successfully set OpenAI API key")
        except Exception as e:
            print(f"Error importing OpenAI: {str(e)}")
            traceback.print_exc()
            api_available = False
        
        for username, influencer in self.influencers_data.items():
            print(f"Analyzing content for {username} with LLM")
            if not influencer.get('all_captions'):
                print(f"No captions found for {username}, skipping LLM analysis")
                influencer['main_interests'] = []
                influencer['related_interests'] = []
                influencer['key_topics'] = []
                influencer['affiliated_brands'] = []
                continue
            
            text = influencer['all_captions']
            biography = influencer.get('biography', '')
            business_category = influencer.get('business_category', '')
            
            if api_available:
                try:
                    print(f"Sending request to OpenAI for {username}")
                    prompt = f"""
                    I need to analyze content from an Instagram influencer with:
                    - Username: {username}
                    - Biography: {biography}
                    - Business Category: {business_category}
                    
                    Based on the following content from their posts:
                    {text[:3000]}
                    
                    Please identify:
                    1) Main interests and related interests of this influencer
                    2) Key topics they discuss or care about
                    3) Brands or companies they appear to be affiliated with or mention frequently
                    
                    Format your response as JSON with "main_interests", "related_interests", "key_topics", and "affiliated_brands" as lists.
                    """
                    
                    # Use the new ChatCompletion API
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a social media analyst specializing in influencer marketing."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=500
                    )
                    
                    # Log the raw response for debugging
                    print(f"Raw response for {username}: {response}")
                    
                    # Check if the response contains the expected content
                    if 'choices' in response and response.choices:
                        # Extract JSON content from within the backticks
                        content = response.choices[0].message['content']
                        json_content = content.strip('```json\n').strip('\n```')
                        result = json.loads(json_content)
                        print(f"Received response from OpenAI for {username}")
                        
                        influencer['main_interests'] = result.get('main_interests', [])
                        influencer['related_interests'] = result.get('related_interests', [])
                        influencer['key_topics'] = result.get('key_topics', [])
                        influencer['affiliated_brands'] = result.get('affiliated_brands', [])
                    else:
                        print(f"Unexpected response format for {username}: {response}")
                        self._set_mock_analysis(influencer, text)
                
                except Exception as e:
                    print(f"Error analyzing content for {username} with OpenAI: {str(e)}")
                    traceback.print_exc()
                    self._set_mock_analysis(influencer, text)
            else:
                print(f"Using simple analysis for {username} (OpenAI API not available)")
                self._set_mock_analysis(influencer, text)
        
        print("LLM analysis complete")
        return self.influencers_data
    
    def _set_mock_analysis(self, influencer, text):
        """Set mock analysis data when OpenAI API is unavailable"""
        # Simple analysis based on basic keyword frequency
        text_lower = text.lower()
        
        # Default interests
        influencer['main_interests'] = ["Social Media", "Photography"]
        influencer['related_interests'] = ["Travel", "Fashion"]
        influencer['key_topics'] = ["Lifestyle", "Content Creation"]
        influencer['affiliated_brands'] = []
        
        # Basic keyword detection
        if "travel" in text_lower or "trip" in text_lower or "vacation" in text_lower:
            influencer['main_interests'].append("Travel")
            influencer['key_topics'].append("Travel")
            
        if "food" in text_lower or "recipe" in text_lower or "delicious" in text_lower:
            influencer['main_interests'].append("Food")
            influencer['key_topics'].append("Culinary")
        
        if "fashion" in text_lower or "style" in text_lower or "outfit" in text_lower:
            influencer['main_interests'].append("Fashion") 
            influencer['key_topics'].append("Style")
        
        # Remove duplicates
        influencer['main_interests'] = list(set(influencer['main_interests']))
        influencer['related_interests'] = list(set(influencer['related_interests']))
        influencer['key_topics'] = list(set(influencer['key_topics']))
        influencer['affiliated_brands'] = list(set(influencer['affiliated_brands']))
    
    def _generate_wordcloud(self, word_counts):
        """Generate a word cloud image from word counts"""
        try:
            # Create word cloud
            wordcloud = WordCloud(width=400, height=200, background_color='white').generate_from_frequencies(word_counts)
            
            # Convert to image using non-GUI approach
            plt.figure(figsize=(4, 2))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            
            # Save to base64 for embedding in HTML
            buffer = BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0)
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"Error generating word cloud: {str(e)}")
            traceback.print_exc()
            return None 