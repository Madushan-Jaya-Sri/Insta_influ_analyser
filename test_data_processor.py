import os
import json
import numpy as np
import pandas as pd
from app.models.data_processor import DataProcessor

# Create a simple test case
print("Creating test data...")

# Create a simple sample data frame with an array in the 'mentions' field
test_profile = {
    'username': 'test_user',
    'fullName': 'Test User',
    'biography': 'This is a test user',
    'followersCount': 1000,
    'followsCount': 500,
    'postsCount': 10
}

test_post = {
    'id': 'test_post_1',
    'shortCode': 'test123',
    'caption': 'Test post with @mention and #hashtag',
    'likesCount': 100,
    'commentsCount': 20,
    'ownerUsername': 'test_user',
    'timestamp': '2025-05-01T12:00:00',
    'mentions': ['user1', 'user2'],  # Use list instead of numpy array
    'hashtags': ['tag1', 'tag2'],    # Use list instead of numpy array
    'displayUrl': 'https://example.com/image.jpg'
}

# Save test data to temporary files
def save_test_data():
    os.makedirs('temp', exist_ok=True)
    
    with open('temp/test_profile.json', 'w') as f:
        json.dump([test_profile], f)
    
    with open('temp/test_posts.json', 'w') as f:
        json.dump([test_post], f)
    
    return 'temp/test_profile.json', 'temp/test_posts.json'

def run_test():
    profile_path, posts_path = save_test_data()
    
    # Create DataProcessor instance
    print("Initializing DataProcessor...")
    dp = DataProcessor(user_id=999)
    
    try:
        # Load test data
        print("Loading test profile data...")
        dp.load_profile_data(profile_path)
        
        print("Loading test posts data...")
        dp.load_posts_data(posts_path)
        
        print("Merging data...")
        dp.merge_data()
        
        print("Setting country...")
        dp.set_country('test_user', 'Test Country')
        
        print("Processing influencer data...")
        dp.process_influencer_data()
        
        print("TEST PASSED: Successfully processed data with array fields")
        return True
    except Exception as e:
        print(f"TEST FAILED: Error during processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_test()
    
    # Clean up temp files if test was successful
    if success:
        import shutil
        shutil.rmtree('temp', ignore_errors=True)
        print("Cleaned up test files")
    
    print("Test complete.") 