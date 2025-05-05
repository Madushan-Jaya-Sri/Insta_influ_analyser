import os
import sys
import traceback
from datetime import datetime

# Check for Python version
if sys.version_info < (3, 8):
    print("WARNING: Python version below 3.8 detected. This application is designed for Python 3.8+")

# Configure environment before importing app
try:
    from dotenv import load_dotenv
    print("Loading environment variables from .env file...")
    load_dotenv()
except ImportError:
    print("python-dotenv not installed, relying on existing environment variables.")

# Ensure critical environment variables
for var in ['FLASK_APP', 'SECRET_KEY']:
    if not os.environ.get(var):
        if var == 'FLASK_APP':
            print(f"Setting default value for {var}")
            os.environ[var] = 'app'
        else:
            print(f"WARNING: {var} environment variable not set!")

# Create required directories
try:
    print("Checking and creating required directories...")
    
    # Get application root directory
    app_root = os.path.abspath(os.path.dirname(__file__))
    
    # Critical directories to ensure exist
    dirs_to_create = [
        os.path.join(app_root, 'data'),
        os.path.join(app_root, 'app', 'static', 'images', 'profiles'),
        os.path.join(app_root, 'app', 'static', 'images', 'posts'),
        os.path.join(app_root, 'app', 'static', 'images', 'misc'),
        os.path.join(app_root, 'app', 'static', 'charts'),
    ]
    
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"Created directory: {directory}")
except Exception as e:
    print(f"Error creating directories: {str(e)}")
    traceback.print_exc()

# Import the app
try:
    from app import create_app
    
    app = create_app()
    
    if __name__ == '__main__':
        print(f"\n==== Starting Instagram Influencer Analyzer ====")
        print(f"Time: {datetime.now().isoformat()}")
        print(f"Flask environment: {os.environ.get('FLASK_ENV', 'not set')}")
        print(f"Debug mode: {app.debug}")
        print(f"OpenAI API key configured: {'Yes' if os.environ.get('OPENAI_API_KEY') else 'No'}")
        
        # Get the port with a fallback to 8001
        port = int(os.environ.get('PORT', 8001))
        
        # Run the app
        app.run(host='0.0.0.0', port=port)
except Exception as e:
    print(f"Critical error during application startup: {str(e)}")
    traceback.print_exc()
    sys.exit(1)