import os
import json
import time
import tempfile
from apify_client import ApifyClient

class ApifyWrapper:
    """A wrapper for the Apify Client to scrape Instagram data"""
    
    def __init__(self, api_token=None):
        """Initialize the Apify client with an API token"""
        self.api_token = api_token or os.getenv('APIFY_API_TOKEN')
        if not self.api_token:
            raise ValueError("Apify API token is not set. Please set the APIFY_API_TOKEN environment variable.")
        self.client = ApifyClient(self.api_token)
    
    def scrape_instagram_profiles(self, urls):
        """
        Scrape Instagram profiles using Apify's Instagram Profile Scraper
        
        Args:
            urls (list): List of Instagram profile URLs
        
        Returns:
            str: Path to the saved JSON file with profile data
        """
        # Extract usernames from URLs
        usernames = []
        for url in urls:
            # Get the username from the URL (handle formats like instagram.com/username/ or instagram.com/username?hl=en)
            username = url.split('instagram.com/')[1].split('/')[0].split('?')[0]
            usernames.append(username)
        
        print(f"Scraping profiles for usernames: {usernames}")
        
        # Prepare the Actor input
        run_input = {"usernames": usernames}
        
        # Run the Actor and wait for it to finish
        run = self.client.actor("dSCLg0C3YEZ83HzYX").call(run_input=run_input)
        
        # Create a temporary file to store the profile data
        fd, profile_file_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Fetch and save Actor results 
        with open(profile_file_path, 'w', encoding='utf-8') as f:
            profiles = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(profiles)} profiles to {profile_file_path}")
        return profile_file_path
    
    def scrape_instagram_posts(self, urls, max_posts=50, posts_newer_than=None):
        """
        Scrape Instagram posts using Apify's Instagram Post Scraper
        
        Args:
            urls (list): List of Instagram profile URLs
            max_posts (int): Maximum number of posts to fetch per profile
            posts_newer_than (str): Only fetch posts newer than specified timeframe (e.g., "1 month")
        
        Returns:
            str: Path to the saved JSON file with posts data
        """
        # Prepare the Actor input
        run_input = {
            "directUrls": urls,
            "resultsType": "posts",
            "resultsLimit": int(max_posts),
            "searchType": "user",
            "searchLimit": 1,
            "addParentData": False
        }
        
        # Add time filter if specified
        if posts_newer_than:
            run_input["onlyPostsNewerThan"] = posts_newer_than
        
        print(f"Scraping posts for URLs: {urls}, max_posts: {max_posts}, newer_than: {posts_newer_than}")
        
        # Run the Actor and wait for it to finish
        run = self.client.actor("shu8hvrXbJbY3Eb9W").call(run_input=run_input)
        
        # Create a temporary file to store the posts data
        fd, posts_file_path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        
        # Fetch and save Actor results
        with open(posts_file_path, 'w', encoding='utf-8') as f:
            posts = list(self.client.dataset(run["defaultDatasetId"]).iterate_items())
            json.dump(posts, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(posts)} posts to {posts_file_path}")
        return posts_file_path 