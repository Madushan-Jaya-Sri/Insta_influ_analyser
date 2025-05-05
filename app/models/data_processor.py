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
import re

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
        
        # Debug info for deployment
        print(f"\n== DataProcessor Initialization ==")
        print(f"APP_ROOT: {APP_ROOT}")
        print(f"DEFAULT_DATA_DIR: {DEFAULT_DATA_DIR}")
        print(f"DEFAULT_IMAGES_PATH: {DEFAULT_IMAGES_PATH}")
        print(f"User ID: {user_id}")
        
        # Create user-specific data directory if a user_id is provided
        if user_id:
            self.user_data_dir = os.path.join(self.data_dir, f'user_{user_id}')
            try:
                os.makedirs(self.user_data_dir, exist_ok=True)
                print(f"Created/verified user data directory: {self.user_data_dir}")
            except Exception as e:
                print(f"ERROR creating user data directory {self.user_data_dir}: {str(e)}")
                traceback.print_exc()
                # Fall back to default directory
                self.user_data_dir = self.data_dir
                print(f"Using fallback directory: {self.user_data_dir}")
                
            self.data_file_path = os.path.join(self.user_data_dir, 'influencers.json')
            
            # Create user-specific image directory
            self.user_images_dir = os.path.join(DEFAULT_IMAGES_PATH, f'user_{user_id}')
            try:
                os.makedirs(os.path.join(self.user_images_dir, 'profiles'), exist_ok=True)
                os.makedirs(os.path.join(self.user_images_dir, 'posts'), exist_ok=True)
                os.makedirs(os.path.join(self.user_images_dir, 'misc'), exist_ok=True)
                print(f"Created/verified user image directories under: {self.user_images_dir}")
            except Exception as e:
                print(f"ERROR creating user image directories {self.user_images_dir}: {str(e)}")
                traceback.print_exc()
                # Fall back to default images directory
                self.user_images_dir = DEFAULT_IMAGES_PATH
                print(f"Using fallback image directory: {self.user_images_dir}")
        else:
            # Fallback to global data file for backward compatibility
            self.data_file_path = os.path.join(self.data_dir, 'influencers.json')
            self.user_data_dir = self.data_dir
            self.user_images_dir = DEFAULT_IMAGES_PATH
            
        # Check directories are writable
        self._check_directory_permissions()
        self._load_persistent_data()
        
    def _check_directory_permissions(self):
        """Verify directories have proper read/write permissions"""
        try:
            # Check user data directory
            print(f"Checking permissions for {self.user_data_dir}")
            if os.path.exists(self.user_data_dir):
                if os.access(self.user_data_dir, os.W_OK):
                    print(f"✓ User data directory is writable: {self.user_data_dir}")
                else:
                    print(f"✗ User data directory is NOT writable: {self.user_data_dir}")
            else:
                print(f"✗ User data directory does not exist: {self.user_data_dir}")
                
            # Check user images directory
            print(f"Checking permissions for {self.user_images_dir}")
            if os.path.exists(self.user_images_dir):
                if os.access(self.user_images_dir, os.W_OK):
                    print(f"✓ User images directory is writable: {self.user_images_dir}")
                else:
                    print(f"✗ User images directory is NOT writable: {self.user_images_dir}")
            else:
                print(f"✗ User images directory does not exist: {self.user_images_dir}")
                
            # Check if we can write a test file
            test_file_path = os.path.join(self.user_data_dir, 'write_test.txt')
            try:
                with open(test_file_path, 'w') as f:
                    f.write('write test')
                os.remove(test_file_path)
                print(f"✓ Successfully wrote and deleted test file in {self.user_data_dir}")
            except Exception as e:
                print(f"✗ Failed to write test file in {self.user_data_dir}: {str(e)}")
                
        except Exception as e:
            print(f"Error checking directory permissions: {str(e)}")
            traceback.print_exc()
    
    def _get_runs_dir(self):
        """Get the directory for storing run history"""
        runs_dir = os.path.join(self.user_data_dir, 'runs')
        os.makedirs(runs_dir, exist_ok=True)
        return runs_dir
    
    def _load_persistent_data(self):
        """Load data from the persistent JSON file if it exists."""
        if os.path.exists(self.data_file_path):
            try:
                with open(self.data_file_path, 'r', encoding='utf-8') as f:
                    self.influencers_data = json.load(f)
                # Rebuild countries mapping from loaded data
                self.countries = {username: data.get('country', '') 
                                  for username, data in self.influencers_data.items()}
                print(f"Loaded {len(self.influencers_data)} influencers from {self.data_file_path}")
            except (FileNotFoundError, json.JSONDecodeError, Exception) as e:
                print(f"Error loading persistent data from {self.data_file_path}: {e}")
                # If loading fails, start fresh
                self.influencers_data = {}
                self.countries = {}
        else:
            print(f"Persistent data file not found: {self.data_file_path}. Starting fresh.")
    
    def _save_persistent_data(self):
        """Save the current influencers_data to the JSON file."""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.data_file_path), exist_ok=True)
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                # Use custom default handler for non-serializable types if needed
                json.dump(self.influencers_data, f, indent=4, default=self._json_serializer)
            print(f"Saved {len(self.influencers_data)} influencers to {self.data_file_path}")
            
            # Also save this as a new run in the history
            self._save_run()
        except Exception as e:
            print(f"Error saving persistent data to {self.data_file_path}: {e}")
            traceback.print_exc()
    
    def _save_run(self):
        """Save the current analysis as a history entry"""
        if not self.user_id or not self.influencers_data:
            return
            
        try:
            # Create a run ID and timestamp
            run_id = str(uuid.uuid4())
            timestamp = datetime.datetime.now().isoformat()
            
            # Extract summary information for the run
            influencer_count = len(self.influencers_data)
            influencer_names = list(self.influencers_data.keys())
            countries = list(set(data.get('country', '') for data in self.influencers_data.values()))
            
            # Create the run data
            run_data = {
                'run_id': run_id,
                'timestamp': timestamp,
                'influencer_count': influencer_count,
                'influencers': influencer_names,
                'countries': countries,
                'snapshot': self.influencers_data  # Store full data for historical reference
            }
            
            # Save to a run-specific file
            runs_dir = self._get_runs_dir()
            run_file = os.path.join(runs_dir, f"{run_id}.json")
            
            with open(run_file, 'w', encoding='utf-8') as f:
                json.dump(run_data, f, indent=4, default=self._json_serializer)
                
            # Also update the runs index file
            self._update_runs_index(run_id, timestamp, influencer_count, influencer_names, countries)
            
        except Exception as e:
            print(f"Error saving run history: {e}")
            traceback.print_exc()
    
    def _update_runs_index(self, run_id, timestamp, influencer_count, influencers, countries):
        """Update the index of all runs"""
        index_file = os.path.join(self._get_runs_dir(), "index.json")
        runs_index = []
        
        # Load existing index if it exists
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    runs_index = json.load(f)
            except Exception as e:
                print(f"Error loading runs index: {e}")
                runs_index = []
        
        # Add the new run to the index
        runs_index.append({
            'run_id': run_id,
            'timestamp': timestamp,
            'influencer_count': influencer_count,
            'influencers': influencers[:5] + ['...'] if len(influencers) > 5 else influencers,  # Limit displayed influencers
            'countries': countries
        })
        
        # Sort by timestamp (newest first)
        runs_index.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Save the updated index
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(runs_index, f, indent=4)
            
    def get_runs_history(self):
        """Get the history of analysis runs"""
        index_file = os.path.join(self._get_runs_dir(), "index.json")
        if not os.path.exists(index_file):
            return []
            
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                runs_index = json.load(f)
                
            # Convert ISO timestamps to formatted dates
            for run in runs_index:
                timestamp = datetime.datetime.fromisoformat(run['timestamp'])
                run['formatted_date'] = timestamp.strftime('%B %d, %Y %I:%M %p')
                
            return runs_index
        except Exception as e:
            print(f"Error loading runs history: {e}")
            return []
            
    def load_run(self, run_id):
        """Load a specific historical run"""
        if not self.user_id:
            return False
            
        run_file = os.path.join(self._get_runs_dir(), f"{run_id}.json")
        if not os.path.exists(run_file):
            return False
            
        try:
            with open(run_file, 'r', encoding='utf-8') as f:
                run_data = json.load(f)
                
            # Load the snapshot data
            self.influencers_data = run_data.get('snapshot', {})
            # Rebuild countries mapping
            self.countries = {username: data.get('country', '') 
                             for username, data in self.influencers_data.items()}
                             
            return True
        except Exception as e:
            print(f"Error loading run {run_id}: {e}")
            return False

    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code"""
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        # Handle numpy types if they appear
        if isinstance(obj, (np.int_, np.intc, np.intp, np.int8,
                            np.int16, np.int32, np.int64, np.uint8,
                            np.uint16, np.uint32, np.uint64)):
            return int(obj)
        elif isinstance(obj, (np.float_, np.float16, np.float32,
                              np.float64)):
            # Handle NaN and Inf
            if np.isnan(obj):
                return None  # Or 0, or 'NaN' as a string
            if np.isinf(obj):
                # Represent infinity appropriately, e.g., None or a large number string
                return None # Or str(obj)
            return float(obj)
        elif isinstance(obj, (np.ndarray,)): # Handle arrays if needed
            return obj.tolist() # Convert arrays to lists
        elif isinstance(obj, (np.bool_)):
            return bool(obj)
        elif isinstance(obj, (np.void)): # Handle numpy void types
            return None
        # Add more types here if needed
        print(f"Warning: Cannot serialize type {type(obj)}: {obj}")
        return str(obj) # Fallback to string representation

    def clear_all_data(self, clear_images=False):
        """Clears persisted data and optionally images."""
        # Clear in-memory data
        self.profile_data = None
        self.posts_data = None
        self.merged_data = None
        self.influencers_data = {}
        self.countries = {}
        
        # Delete the JSON data file
        if os.path.exists(self.data_file_path):
            try:
                os.remove(self.data_file_path)
                print(f"Deleted persistent data file: {self.data_file_path}")
            except OSError as e:
                print(f"Error deleting data file {self.data_file_path}: {e}")

        # Optionally clear images
        if clear_images and self.user_id:
            user_images_path = self.user_images_dir
            for subdir in ['profiles', 'posts', 'misc']:
                dir_to_clear = os.path.join(user_images_path, subdir)
                if os.path.exists(dir_to_clear):
                    try:
                        # Remove all files within the directory
                        for filename in os.listdir(dir_to_clear):
                            file_path = os.path.join(dir_to_clear, filename)
                            try:
                                if os.path.isfile(file_path) or os.path.islink(file_path):
                                    os.unlink(file_path)
                            except Exception as e:
                                print(f'Failed to delete {file_path}. Reason: {e}')
                        print(f"Cleared image files in: {dir_to_clear}")
                    except OSError as e:
                        print(f"Error clearing images in {dir_to_clear}: {e}")
        
        print("All data cleared.")


    def load_profile_data(self, file_path):
        """Load the Instagram profile data JSON file"""
        # Only clear working data variables, not the final results
        self.profile_data = None
        self.posts_data = None
        self.merged_data = None
        
        # Maintain existing influencers_data to accumulate profiles across sessions
        # Initialize with empty dictionaries if they don't exist yet
        if not hasattr(self, 'influencers_data') or self.influencers_data is None:
            self.influencers_data = {}
            
        if not hasattr(self, 'countries') or self.countries is None:
            self.countries = {}
            
        print("Loading new profile data while preserving existing influencers.")
        
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
        
        # Use post ID as the filename, but ensure it's a valid filename
        # Replace any characters that might be invalid in a filename
        safe_id = str(post_id).replace('/', '_').replace('\\', '_').replace(':', '_')
        filename = f"{safe_id}.jpg"
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
        """Process the merged data to generate the influencers report"""
        if self.merged_data is None and self.profile_data is None:
            raise Exception("No data to process. Please load profile and posts data first.")
        
        try:
            # Create a copy of the existing influencers_data to preserve old profiles
            influencers = self.influencers_data.copy() if hasattr(self, 'influencers_data') and self.influencers_data else {}
            
            # Get unique influencers from profile data
            if self.profile_data is not None:
                print(f"Processing {len(self.profile_data)} profiles")
                
                # Process each profile
                for _, profile in self.profile_data.iterrows():
                    username = profile['username']
                    
                    # For new profiles or to update existing ones
                    print(f"Processing profile: {username}")
                    
                    # Initialize influencer data structure if this is a new profile
                    # or preserve existing structure if it's being updated
                    if username not in influencers:
                        # New profile - create new entry
                        influencers[username] = {
                            'username': username,
                            'full_name': profile.get('fullName', ''),
                            'biography': profile.get('biography', ''),
                            'external_url': profile.get('externalUrl', ''),
                            'followers_count': profile.get('followersCount', 0),
                            'follows_count': profile.get('followsCount', 0),
                            'is_verified': profile.get('isVerified', False),
                            'posts_count': profile.get('postsCount', 0),
                            'profile_pic_url': profile.get('profilePicUrl', ''),
                            'business_category': profile.get('categoryName', ''),
                            'country': self.countries.get(username, 'Unknown'),
                            'processed_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'posts': []  # Will be populated with post data
                        }
                    else:
                        # Existing profile - update basic info but preserve advanced metrics
                        # and analyses that may have been previously calculated
                        existing = influencers[username]
                        existing.update({
                            'full_name': profile.get('fullName', existing.get('full_name', '')),
                            'biography': profile.get('biography', existing.get('biography', '')),
                            'external_url': profile.get('externalUrl', existing.get('external_url', '')),
                            'followers_count': profile.get('followersCount', existing.get('followers_count', 0)),
                            'follows_count': profile.get('followsCount', existing.get('follows_count', 0)),
                            'is_verified': profile.get('isVerified', existing.get('is_verified', False)),
                            'posts_count': profile.get('postsCount', existing.get('posts_count', 0)),
                            'profile_pic_url': profile.get('profilePicUrl', existing.get('profile_pic_url', '')),
                            'business_category': profile.get('categoryName', existing.get('business_category', '')),
                            'country': self.countries.get(username, existing.get('country', 'Unknown')),
                            'processed_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        })
                        
                        # Keep track of previous posts if any
                        if 'posts' not in existing:
                            existing['posts'] = []
                    
                    # Download and set profile image
                    profile_pic_url = influencers[username]['profile_pic_url']
                    image_path = self.download_profile_image(username, profile_pic_url)
                    influencers[username]['profile_pic_local'] = image_path
            
            # Process posts if we have merged data
            if self.merged_data is not None:
                print(f"Processing {len(self.merged_data)} posts")
                
                # Group data by username
                grouped_data = self.merged_data.groupby('username')
                print(f"Found {len(grouped_data)} influencer groups")
                
                # Process each influencer group
                for username, group in grouped_data:
                    print(f"Processing posts for: {username}")
                    
                    # Skip if this influencer doesn't exist in our dictionary (shouldn't happen typically)
                    if username not in influencers:
                        print(f"Warning: Found posts for {username} but no profile data")
                        continue
                    
                    influencer = influencers[username]
                    
                    # Track existing post IDs to avoid duplicates
                    existing_post_ids = set()
                    if 'posts' in influencer:
                        existing_post_ids = {post.get('id') for post in influencer['posts'] if 'id' in post}
                    
                    # Get additional influencer data from posts
                    # Add user data if it's missing from profile
                    if 'full_name' not in influencer or not influencer['full_name']:
                        influencer['full_name'] = group['ownerFullName'].iloc[0] if not pd.isna(group['ownerFullName'].iloc[0]) else username
                        
                    # Add country if not set yet
                    if 'country' not in influencer or influencer['country'] == 'Unknown':
                        influencer['country'] = self.countries.get(username, 'Unknown')
                    
                    # Process posts for this influencer
                    posts_list = []
                    post_dates = []
                    engagement_rates = []
                    likes_counts = []
                    comments_counts = []
                    hashtags = []
                    captions = []
                    mentions = []
                    all_captions_text = ""
                    
                    # Keep existing posts in the list
                    if 'posts' in influencer:
                        posts_list = influencer['posts']
                    
                    # Process each post for this influencer
                    for _, post in group.iterrows():
                        # Safely get post ID or generate a fallback ID
                        if 'id' in post:
                            post_id = post['id']
                        elif 'shortCode' in post:
                            post_id = f"sc_{post['shortCode']}"
                        else:
                            # Generate a unique ID using hash of post content
                            post_id = f"gen_{hash(str(post))}"
                        
                        # Skip if we already have this post
                        if post_id in existing_post_ids:
                            print(f"Skipping already processed post {post_id}")
                            continue
                        
                        # Process post
                        print(f"Processing post: {post_id}")
                        
                        # Get likes and comments
                        likes_count = post.get('likesCount', 0) if not pd.isna(post.get('likesCount')) else 0
                        comments_count = post.get('commentsCount', 0) if not pd.isna(post.get('commentsCount')) else 0
                        
                        # Create post object
                        post_obj = {
                            'id': post_id,
                            'shortcode': post.get('shortCode', ''),
                            'caption': post.get('caption', ''),
                            'likes_count': likes_count,
                            'comments_count': comments_count,
                            'timestamp': post.get('timestamp', ''),
                            'display_url': post.get('displayUrl', ''),
                            'is_video': post.get('isVideo', False),
                        }
                        
                        # Download post image if available
                        if not pd.isna(post.get('displayUrl')):
                            image_path = self.download_post_image(post_id, post['displayUrl'])
                            # Store the image path with consistent field name
                            post_obj['image_local'] = image_path
                        
                        # Add post metrics to running totals
                        if not pd.isna(post.get('timestamp')):
                            post_dates.append(post['timestamp'])
                            
                        # Add likes and comments to running totals
                        likes_counts.append(likes_count)
                        comments_counts.append(comments_count)
                        
                        # Calculate engagement rate for this post
                        if 'followers_count' in influencer and influencer['followers_count'] > 0:
                            engagement = ((likes_count + comments_count) / influencer['followers_count']) * 100
                            post_obj['engagement_rate'] = engagement
                            engagement_rates.append(engagement)
                            
                        # Extract caption for analysis
                        caption = post.get('caption', '')
                        if caption and not pd.isna(caption):
                            captions.append(caption)
                            all_captions_text += caption + "\n\n"  # Add to full captions text
                        
                        # Extract hashtags from post data or caption
                        post_hashtags = []
                        if 'hashtags' in post:
                            # Check if it's a numpy array and handle accordingly
                            if isinstance(post['hashtags'], np.ndarray):
                                if not pd.isna(post['hashtags']).all():  # Only process if not all values are NaN
                                    post_hashtags = post['hashtags'].tolist()
                            # If not an array, check if it's not NaN directly
                            elif isinstance(post['hashtags'], list):
                                post_hashtags = post['hashtags']
                            elif isinstance(post['hashtags'], str) and not pd.isna(post['hashtags']):
                                post_hashtags = post['hashtags'].split(',')
                            # If it's scalar, check for NaN
                            elif not pd.isna(post['hashtags']):
                                # Try to convert to string and split
                                try:
                                    post_hashtags = str(post['hashtags']).split(',')
                                except:
                                    pass
                        
                        # If no hashtags found in the field, extract from caption
                        if not post_hashtags and caption and not pd.isna(caption):
                            import re
                            post_hashtags = re.findall(r'#(\w+)', caption)
                        
                        # Clean and store hashtags
                        if post_hashtags:
                            post_obj['hashtags'] = post_hashtags
                            hashtags.extend(post_hashtags)
                        
                        # Extract mentions from post data or caption
                        post_mentions = []
                        if 'mentions' in post:
                            # Check if it's a numpy array and handle accordingly
                            if isinstance(post['mentions'], np.ndarray):
                                if not pd.isna(post['mentions']).all():  # Only process if not all values are NaN
                                    post_mentions = post['mentions'].tolist()
                            # If not an array, check if it's not NaN directly
                            elif isinstance(post['mentions'], list):
                                post_mentions = post['mentions']
                            elif isinstance(post['mentions'], str) and not pd.isna(post['mentions']):
                                post_mentions = post['mentions'].split(',')
                            # If it's scalar, check for NaN
                            elif not pd.isna(post['mentions']):
                                # Try to convert to string and split
                                try:
                                    post_mentions = str(post['mentions']).split(',')
                                except:
                                    pass
                        
                        # If no mentions found in the field, extract from caption
                        if not post_mentions and caption and not pd.isna(caption):
                            import re
                            post_mentions = re.findall(r'@(\w+)', caption)
                        
                        # Clean and store mentions
                        if post_mentions:
                            post_obj['mentions'] = post_mentions
                            mentions.extend(post_mentions)
                        
                        # Add post to the list
                        posts_list.append(post_obj)
                    
                    # Add posts list to influencer
                    influencer['posts'] = posts_list
                    
                    # Calculate and add aggregate metrics
                    # Total engagement metrics
                    influencer['likes_total'] = sum(likes_counts) if likes_counts else 0
                    influencer['comments_total'] = sum(comments_counts) if comments_counts else 0
                    influencer['total_engagement'] = influencer['likes_total'] + influencer['comments_total']
                    
                    # Average engagement metrics
                    influencer['avg_likes'] = np.mean(likes_counts) if likes_counts else 0
                    influencer['avg_comments'] = np.mean(comments_counts) if comments_counts else 0
                    
                    # Engagement rates
                    if influencer.get('followers_count', 0) > 0 and len(posts_list) > 0:
                        # Overall engagement rate
                        influencer['engagement_rate'] = (influencer['total_engagement'] / (influencer['followers_count'] * len(posts_list))) * 100
                        
                        # Average post engagement rate
                        influencer['avg_engagement_rate'] = np.mean(engagement_rates) if engagement_rates else 0
                        influencer['max_engagement_rate'] = max(engagement_rates) if engagement_rates else 0
                    else:
                        influencer['engagement_rate'] = 0
                        influencer['avg_engagement_rate'] = 0
                        influencer['max_engagement_rate'] = 0
                    
                    # Top hashtags (most frequent first)
                    if hashtags:
                        hashtag_counter = Counter(hashtags)
                        influencer['top_hashtags'] = [{'tag': tag, 'count': count} for tag, count in hashtag_counter.most_common(10)]
                    else:
                        influencer['top_hashtags'] = []
                    
                    # Top mentions (most frequent first)
                    if mentions:
                        mention_counter = Counter(mentions)
                        influencer['top_mentions'] = [{'username': username, 'count': count} for username, count in mention_counter.most_common(10)]
                    else:
                        influencer['top_mentions'] = []
                    
                    # Store all captions for LLM analysis
                    influencer['all_captions'] = all_captions_text
                    
                    # Generate time-based engagement metrics if we have dates
                    if post_dates and (likes_counts or comments_counts):
                        try:
                            # Convert timestamps to datetime objects
                            date_objs = [pd.to_datetime(date) for date in post_dates if not pd.isna(date)]
                            
                            if date_objs:
                                # Create a DataFrame for time-based analysis
                                engagement_df = pd.DataFrame({
                                    'date': date_objs,
                                    'likes': likes_counts[:len(date_objs)],  # Align with valid dates
                                    'comments': comments_counts[:len(date_objs)]  # Align with valid dates
                                })
                                
                                # Sort by date
                                engagement_df = engagement_df.sort_values('date')
                                
                                # Add total engagement column
                                engagement_df['engagement'] = engagement_df['likes'] + engagement_df['comments']
                                
                                # Add engagement rate if we have follower count
                                if influencer.get('followers_count', 0) > 0:
                                    engagement_df['engagement_rate'] = (engagement_df['engagement'] / influencer['followers_count']) * 100
                                
                                # Weekly engagement aggregation
                                weekly = engagement_df.groupby(pd.Grouper(key='date', freq='W')).agg({
                                    'likes': 'sum',
                                    'comments': 'sum',
                                    'engagement': 'sum'
                                }).reset_index()
                                
                                if not weekly.empty and influencer.get('followers_count', 0) > 0:
                                    weekly['engagement_rate'] = (weekly['engagement'] / influencer['followers_count']) * 100
                                
                                # Monthly engagement aggregation
                                monthly = engagement_df.groupby(pd.Grouper(key='date', freq='M')).agg({
                                    'likes': 'sum',
                                    'comments': 'sum',
                                    'engagement': 'sum'
                                }).reset_index()
                                
                                if not monthly.empty and influencer.get('followers_count', 0) > 0:
                                    monthly['engagement_rate'] = (monthly['engagement'] / influencer['followers_count']) * 100
                                
                                # Quarterly engagement aggregation
                                quarterly = engagement_df.groupby(pd.Grouper(key='date', freq='Q')).agg({
                                    'likes': 'sum',
                                    'comments': 'sum',
                                    'engagement': 'sum'
                                }).reset_index()
                                
                                if not quarterly.empty and influencer.get('followers_count', 0) > 0:
                                    quarterly['engagement_rate'] = (quarterly['engagement'] / influencer['followers_count']) * 100
                                
                                # Convert to serializable format
                                influencer['engagement_weekly'] = [
                                    {
                                        'date': row['date'].strftime('%Y-%m-%d'),
                                        'likes': int(row['likes']),
                                        'comments': int(row['comments']),
                                        'engagement': int(row['engagement']),
                                        'engagement_rate': float(row.get('engagement_rate', 0))
                                    } for _, row in weekly.iterrows()
                                ]
                                
                                influencer['engagement_monthly'] = [
                                    {
                                        'date': row['date'].strftime('%Y-%m'),
                                        'likes': int(row['likes']),
                                        'comments': int(row['comments']),
                                        'engagement': int(row['engagement']),
                                        'engagement_rate': float(row.get('engagement_rate', 0))
                                    } for _, row in monthly.iterrows()
                                ]
                                
                                influencer['engagement_quarterly'] = [
                                    {
                                        'date': row['date'].strftime('%Y-Q%q'),
                                        'likes': int(row['likes']),
                                        'comments': int(row['comments']),
                                        'engagement': int(row['engagement']),
                                        'engagement_rate': float(row.get('engagement_rate', 0))
                                    } for _, row in quarterly.iterrows()
                                ]
                        except Exception as e:
                            print(f"Error generating time-based metrics for {username}: {e}")
                            traceback.print_exc()
            
            self.influencers_data = influencers
            print(f"Processed {len(influencers)} influencers successfully")

            # Save the processed data
            self._save_persistent_data()

            return influencers
        
        except Exception as e:
            print(f"Error in process_influencer_data: {str(e)}")
            traceback.print_exc()
            raise Exception(f"Error processing data: {str(e)}")
    
    def analyze_with_llm(self, openai_api_key):
        """Analyze influencer content using OpenAI LLM"""
        print("\n========== STARTING LLM ANALYSIS ==========")
        
        # Try importing OpenAI and setting up client with proper method
        api_available = False
        
        try:
            import openai
            openai.api_key = openai_api_key
            api_available = True
            
            # Check OpenAI API version to use correct API call format
            import pkg_resources
            openai_version = pkg_resources.get_distribution("openai").version
            using_new_api = openai_version.startswith('1.')
            print(f"✓ Successfully configured OpenAI API (version {openai_version})")
        except Exception as e:
            print(f"✗ Error importing OpenAI: {str(e)}")
            traceback.print_exc()
            api_available = False
        
        for username, influencer in self.influencers_data.items():
            print(f"\n----- Analyzing content for {username} -----")
            
            # Get all relevant content for analysis
            biography = influencer.get('biography', '')
            business_category = influencer.get('business_category', '')
            
            # Get captions text
            captions_text = influencer.get('all_captions', '')
            if not captions_text and 'posts' in influencer:
                # Build captions from posts if all_captions not set
                captions_text = "\n\n".join([post.get('caption', '') for post in influencer['posts'] 
                                          if post.get('caption') and not pd.isna(post.get('caption'))])
            
            # Get hashtags
            hashtags = []
            if 'top_hashtags' in influencer and influencer['top_hashtags']:
                hashtags = [item['tag'] for item in influencer['top_hashtags']]
            else:
                # Extract from posts if not already aggregated
                for post in influencer.get('posts', []):
                    if 'hashtags' in post and isinstance(post['hashtags'], list):
                        hashtags.extend(post['hashtags'])
            
            # Get mentions
            mentions = []
            if 'top_mentions' in influencer and influencer['top_mentions']:
                mentions = [item['username'] for item in influencer['top_mentions']]
            else:
                # Extract from posts if not already aggregated
                for post in influencer.get('posts', []):
                    if 'mentions' in post and isinstance(post['mentions'], list):
                        mentions.extend(post['mentions'])
            
            # Remove duplicates
            hashtags = list(set(hashtags))
            mentions = list(set(mentions))
            
            # Skip if we have no meaningful content to analyze
            if not biography and not captions_text and not hashtags:
                print(f"✗ No content found for {username}, skipping LLM analysis")
                # Initialize with empty values
                influencer['main_interests'] = []
                influencer['related_interests'] = []
                influencer['key_topics'] = []
                influencer['affiliated_brands'] = []
                influencer['content_sentiment'] = {
                    'overall': 'Neutral',
                    'description': 'Insufficient data for sentiment analysis'
                }
                continue
            
            if api_available:
                try:
                    print(f"→ Constructing prompt for {username}")
                    
                    # Prepare the prompt with all available information
                    prompt = f"""
                    I need an in-depth analysis of an Instagram influencer with the following data:
                    
                    USERNAME: {username}
                    
                    BIOGRAPHY: {biography}
                    
                    BUSINESS CATEGORY: {business_category}
                    
                    HASHTAGS USED: {', '.join(hashtags[:30]) if hashtags else 'No hashtags available'}
                    
                    ACCOUNTS MENTIONED: {', '.join(mentions[:20]) if mentions else 'No mentions available'}
                    
                    SAMPLE POST CAPTIONS:
                    {captions_text[:1000] + '...' if len(captions_text) > 1000 else captions_text}
                    
                    Based on this information, please provide:
                    
                    1. Main interests/topics of this influencer (3-5 items)
                    2. Related interests/topics that are secondary but still relevant (3-5 items)
                    3. Key topics frequently discussed in their content (3-5 items)
                    4. Identify any brands or companies they appear to be affiliated with from the mentions and captions
                    5. A brief sentiment analysis of their content (positive, negative, neutral, aspirational, educational, etc.)
                    
                    Format your response as JSON with these keys:
                    ```json
                    {{
                        "main_interests": ["interest1", "interest2", ...],
                        "related_interests": ["interest1", "interest2", ...],
                        "key_topics": ["topic1", "topic2", ...],
                        "affiliated_brands": ["brand1", "brand2", ...],
                        "content_sentiment": {{
                            "overall": "Positive/Negative/Neutral/etc.",
                            "description": "Brief 1-2 sentence description of content style and tone"
                        }}
                    }}
                    ```
                    """
                    
                    print(f"→ Sending request to OpenAI for {username}")
                    print(f"  Input content summary: Biography ({len(biography)} chars), " +
                          f"Hashtags ({len(hashtags)}), Mentions ({len(mentions)}), " +
                          f"Captions ({len(captions_text)} chars)")
                    
                    # Use the appropriate API call format based on OpenAI version
                    if using_new_api:
                        # New API format (v1.x)
                        response = openai.chat.completions.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a social media analyst specializing in influencer marketing. Provide detailed analysis of Instagram content."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=800
                        )
                        
                        # Extract content
                        response_content = response.choices[0].message.content if response.choices else "No content"
                    else:
                        # Legacy API format (v0.x)
                        response = openai.ChatCompletion.create(
                            model="gpt-3.5-turbo",
                            messages=[
                                {"role": "system", "content": "You are a social media analyst specializing in influencer marketing. Provide detailed analysis of Instagram content."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=800
                        )
                        
                        # Extract content
                        response_content = response['choices'][0]['message']['content'] if response['choices'] else "No content"
                    
                    truncated_content = response_content[:1000] + "..." if len(response_content) > 1000 else response_content
                    print(f"← Received response from OpenAI for {username}")
                    print(f"  Response length: {len(response_content)} characters")
                    print(f"  Response preview: {truncated_content[:200]}...")
                    
                    # Check if the response contains the expected content
                    if (using_new_api and 'choices' in response and response.choices) or \
                       (not using_new_api and 'choices' in response and response['choices']):
                        # Extract JSON content from within the backticks
                        content = response_content
                        # Try to find JSON within backticks first
                        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content, re.DOTALL)
                        
                        if json_match:
                            json_content = json_match.group(1)
                        else:
                            # If no backticks found, try to parse the whole content
                            json_content = content
                        
                        try:
                            result = json.loads(json_content)
                            print(f"✓ Successfully parsed JSON response for {username}")
                            
                            # Apply the result to the influencer data
                            influencer['main_interests'] = result.get('main_interests', [])
                            influencer['related_interests'] = result.get('related_interests', [])
                            influencer['key_topics'] = result.get('key_topics', [])
                            influencer['affiliated_brands'] = result.get('affiliated_brands', [])
                            
                            # Add content sentiment analysis
                            if 'content_sentiment' in result and isinstance(result['content_sentiment'], dict):
                                influencer['content_sentiment'] = result['content_sentiment']
                            else:
                                influencer['content_sentiment'] = {
                                    'overall': 'Neutral',
                                    'description': 'Content appears to be neutral in tone.'
                                }
                            
                            # Log the analysis results
                            print(f"  Main interests: {influencer['main_interests']}")
                            print(f"  Related interests: {influencer['related_interests']}")
                            print(f"  Key topics: {influencer['key_topics']}")
                            print(f"  Affiliated brands: {influencer['affiliated_brands']}")
                            print(f"  Content sentiment: {influencer['content_sentiment']['overall']}")
                            
                        except json.JSONDecodeError as e:
                            print(f"✗ Failed to parse JSON for {username}: {str(e)}")
                            print(f"  Raw content: {json_content}")
                            self._set_mock_analysis(influencer, captions_text, hashtags, mentions)
                    else:
                        print(f"✗ Unexpected response format for {username}")
                        self._set_mock_analysis(influencer, captions_text, hashtags, mentions)
                
                except Exception as e:
                    print(f"✗ Error analyzing content for {username} with OpenAI: {str(e)}")
                    traceback.print_exc()
                    self._set_mock_analysis(influencer, captions_text, hashtags, mentions)
            else:
                print(f"→ Using simple analysis for {username} (OpenAI API not available)")
                self._set_mock_analysis(influencer, captions_text, hashtags, mentions)
        
        print("\n========== LLM ANALYSIS COMPLETE ==========\n")
        return self.influencers_data
    
    def _set_mock_analysis(self, influencer, text, hashtags=None, mentions=None):
        """Set mock analysis data when OpenAI API is unavailable"""
        # Simple analysis based on basic keyword frequency
        text_lower = text.lower() if text else ""
        hashtags = hashtags or []
        mentions = mentions or []
        
        # Default interests
        influencer['main_interests'] = ["Social Media", "Photography"]
        influencer['related_interests'] = ["Travel", "Fashion"]
        influencer['key_topics'] = ["Lifestyle", "Content Creation"]
        influencer['affiliated_brands'] = []
        influencer['content_sentiment'] = {
            'overall': 'Neutral',
            'description': 'Basic analysis indicates a balanced content style.'
        }
        
        # Basic keyword detection for interests and topics
        keywords = {
            "Travel": ["travel", "trip", "vacation", "destination", "wanderlust", "explore"],
            "Food": ["food", "recipe", "cooking", "eat", "restaurant", "meal", "delicious"],
            "Fashion": ["fashion", "style", "outfit", "clothing", "wear", "dress"],
            "Fitness": ["workout", "fitness", "exercise", "gym", "training", "health"],
            "Beauty": ["makeup", "beauty", "skincare", "cosmetics", "hair", "skin"],
            "Lifestyle": ["lifestyle", "life", "daily", "routine", "living"],
            "Technology": ["tech", "technology", "digital", "gadget", "device"],
            "Art": ["art", "artist", "creative", "design", "paint", "draw"],
            "Music": ["music", "song", "artist", "concert", "festival"],
            "Family": ["family", "kid", "child", "parent", "baby", "mom", "dad"]
        }
        
        # Check text content against keywords
        detected_interests = []
        for category, terms in keywords.items():
            for term in terms:
                if term in text_lower:
                    detected_interests.append(category)
                    break
        
        # Check hashtags against keywords
        for tag in hashtags:
            tag_lower = tag.lower()
            for category, terms in keywords.items():
                category_lower = category.lower()
                if tag_lower == category_lower or any(term in tag_lower for term in terms):
                    detected_interests.append(category)
                    break
        
        # Get unique interests
        detected_interests = list(set(detected_interests))
        
        # Set detected interests if we found any
        if detected_interests:
            # Main interests are the first 3-5
            influencer['main_interests'] = detected_interests[:min(5, len(detected_interests))]
            
            # Related interests are the rest, up to 5 more
            if len(detected_interests) > 5:
                influencer['related_interests'] = detected_interests[5:min(10, len(detected_interests))]
            
            # Key topics are a mix
            influencer['key_topics'] = detected_interests[:min(5, len(detected_interests))]
        
        # Try to detect brand mentions
        common_brands = [
            "nike", "adidas", "puma", "reebok", "underarmour", "newbalance",
            "apple", "samsung", "huawei", "sony", "microsoft", "google",
            "coca", "cola", "pepsi", "starbucks", "mcdonalds", "wendys",
            "amazon", "walmart", "target", "ikea", "hm", "zara",
            "sephora", "ulta", "maccosmetics", "fenty", "dove", "loreal"
        ]
        
        # Check for brand mentions
        detected_brands = []
        
        # Check in mentions
        for mention in mentions:
            mention_lower = mention.lower()
            if any(brand in mention_lower for brand in common_brands):
                detected_brands.append(mention)
        
        # Check in text
        for brand in common_brands:
            if brand in text_lower:
                # Capitalize brand names
                detected_brands.append(brand.title())
        
        if detected_brands:
            influencer['affiliated_brands'] = list(set(detected_brands))[:10]
        
        # Determine sentiment based on keywords
        positive_words = ["love", "great", "amazing", "beautiful", "happy", "best", "perfect", "awesome"]
        negative_words = ["bad", "hate", "awful", "terrible", "worst", "sad", "disappointed"]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count * 2:
            influencer['content_sentiment'] = {
                'overall': 'Very Positive',
                'description': 'Content has an overwhelmingly positive and uplifting tone.'
            }
        elif positive_count > negative_count:
            influencer['content_sentiment'] = {
                'overall': 'Positive',
                'description': 'Content generally has a positive tone.'
            }
        elif negative_count > positive_count * 2:
            influencer['content_sentiment'] = {
                'overall': 'Very Negative',
                'description': 'Content has a predominantly negative tone.'
            }
        elif negative_count > positive_count:
            influencer['content_sentiment'] = {
                'overall': 'Somewhat Negative',
                'description': 'Content has a slightly negative tone.'
            }
        else:
            influencer['content_sentiment'] = {
                'overall': 'Neutral',
                'description': 'Content appears to be balanced or neutral in tone.'
            }
    
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

    def save_to_history_db(self, time_filter=None, max_posts=None):
        """Save the analysis results to the database for history tracking"""
        from app.models.history import History, AnalysisImage
        from run import db

        if not self.user_id or not self.influencers_data:
            print("Cannot save to history: missing user_id or influencers_data")
            return None

        # Create a history record for each influencer analyzed
        history_records = []
        
        for username, data in self.influencers_data.items():
            try:
                # Create history record
                history = History(
                    user_id=self.user_id,
                    profile_username=username,
                    profile_name=data.get('full_name', ''),
                    profile_url=f"https://instagram.com/{username}/",
                    profile_follower_count=data.get('follower_count', 0),
                    profile_post_count=data.get('post_count', 0),
                    analysis_results=data,
                    max_posts=max_posts,
                    time_filter=time_filter,
                    analysis_complete=True
                )
                
                # Add to database
                db.session.add(history)
                db.session.flush()  # This assigns an ID to history without committing
                
                # Add profile image if available
                profile_pic_path = data.get('profile_pic_local')
                if profile_pic_path:
                    profile_image = AnalysisImage(
                        history_id=history.id,
                        image_type='profile',
                        image_url=data.get('profile_pic_url', ''),
                        image_path=profile_pic_path
                    )
                    db.session.add(profile_image)
                
                # Add post images if available
                if 'posts' in data:
                    for post in data['posts']:
                        post_pic_path = post.get('image_local')
                        if post_pic_path:
                            # Ensure post ID exists
                            post_id = post.get('id', str(hash(str(post))))
                            
                            # Get likes and comments, ensuring we use the right key names
                            likes = post.get('likes_count') or post.get('likes', 0)
                            comments = post.get('comments_count') or post.get('comments', 0)
                            
                            post_image = AnalysisImage(
                                history_id=history.id,
                                image_type='post',
                                image_url=post.get('display_url', ''),
                                image_path=post_pic_path,
                                image_metadata={
                                    'post_id': post_id,
                                    'shortcode': post.get('shortcode', ''),
                                    'likes': likes,
                                    'comments': comments
                                }
                            )
                            db.session.add(post_image)
                
                # Add to the list of records
                history_records.append(history)
                
            except Exception as e:
                print(f"Error saving {username} to history: {str(e)}")
                traceback.print_exc()  # This will help with debugging
                continue
        
        # Commit all records
        try:
            db.session.commit()
            print(f"Saved {len(history_records)} influencers to history database")
            return history_records
        except Exception as e:
            db.session.rollback()
            print(f"Error committing history records: {str(e)}")
            traceback.print_exc()  # Add stack trace for better debugging
            return None
    
    def load_analysis_from_history(self, history_id):
        """Load analysis data from a history record"""
        from app.models.history import History
        
        if not self.user_id:
            print("Cannot load from history: missing user_id")
            return False
            
        # Find the history record
        history = History.query.filter_by(id=history_id, user_id=self.user_id).first()
        if not history:
            print(f"History record {history_id} not found for user {self.user_id}")
            return False
            
        try:
            # Load the analysis data
            username = history.profile_username
            self.influencers_data = {username: history.analysis_results}
            
            # Set country if available
            if history.analysis_results.get('country'):
                self.countries[username] = history.analysis_results['country']
                
            print(f"Loaded analysis for {username} from history record {history_id}")
            return True
            
        except Exception as e:
            print(f"Error loading analysis from history: {str(e)}")
            return False 