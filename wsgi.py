import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

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