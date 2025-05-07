import os
import sys
import subprocess
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Check if we need to fix auth.py before importing the app
auth_py_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'routes', 'auth.py')
if os.path.exists(auth_py_path):
    with open(auth_py_path, 'r') as f:
        content = f.read()
        if 'from run import db' in content:
            print("CRITICAL: Fixing circular import in auth.py before app import")
            with open(auth_py_path, 'w') as f:
                # Replace the problematic import
                fixed_content = content.replace('from run import db', 'from app import db')
                f.write(fixed_content)
            print("auth.py fixed successfully")

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app function
from app import create_app

# Create the application instance
application = create_app()

# For running with Gunicorn, this is what will be imported
app = application

if __name__ == "__main__":
    # Run the app if this script is executed directly (not recommended for production)
    application.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8001))) 