import os
import json
import numpy as np
import pandas as pd
from app.models.data_processor import DataProcessor

# Create a test case specifically for numpy arrays
print("Creating test data with numpy arrays...")

# Create profile data
test_profile = {
    'username': 'test_array_user',
    'fullName': 'Test Array User',
    'biography': 'This is a test user for numpy arrays',
    'followersCount': 1000,
    'followsCount': 500,
    'postsCount': 10
}

# Create post with numpy arrays
test_post = {
    'id': 'test_post_array',
    'shortCode': 'test456',
    'caption': 'Test post with arrays for processing',
    'likesCount': 200,
    'commentsCount': 30,
    'ownerUsername': 'test_array_user',
    'timestamp': '2025-05-01T12:00:00',
    'displayUrl': 'https://example.com/image2.jpg'
}

def run_array_test():
    """Run a test with numpy arrays to ensure they're processed correctly"""
    try:
        print("\nRunning test with pandas and numpy arrays...")
        
        # Create DataProcessor instance
        dp = DataProcessor(user_id=888)
        
        # Create pandas DataFrames directly with numpy arrays
        profile_df = pd.DataFrame([test_profile])
        
        # Create post dataframe with array columns
        post_data = [test_post]
        posts_df = pd.DataFrame(post_data)
        
        # Add numpy array columns after creating the DataFrame
        posts_df['mentions'] = None  # Initialize to avoid errors
        posts_df['hashtags'] = None  # Initialize to avoid errors
        
        # Replace with numpy arrays
        posts_df.at[0, 'mentions'] = np.array(['user1', 'user2', 'user3'])
        posts_df.at[0, 'hashtags'] = np.array(['tag1', 'tag2', 'tag3'])
        
        # Set the dataframes directly on the DataProcessor instance
        dp.profile_data = profile_df
        dp.posts_data = posts_df
        
        print("Profile DataFrame structure:")
        print(profile_df.dtypes)
        print("\nPosts DataFrame structure:")
        print(posts_df.dtypes)
        print("\nConfirming mentions is a numpy array:", isinstance(posts_df.at[0, 'mentions'], np.ndarray))
        print("Confirming hashtags is a numpy array:", isinstance(posts_df.at[0, 'hashtags'], np.ndarray))
        
        # Merge the data
        print("\nMerging data...")
        dp.merge_data()
        
        # Set country
        print("Setting country...")
        dp.set_country('test_array_user', 'Test Array Country')
        
        # Process the data
        print("Processing data with numpy arrays...")
        dp.process_influencer_data()
        
        print("\nTEST PASSED: Successfully processed numpy array fields")
        return True
        
    except Exception as e:
        print(f"\nTEST FAILED: Error during array processing: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the array test
    success = run_array_test()
    print("\nArray test complete with result:", "SUCCESS" if success else "FAILURE") 