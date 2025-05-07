"""
WSGI entry point for the application.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

# Import the app factory function
from app import create_app

# Create the application instance
app = create_app()

# This is what will be imported by Gunicorn
application = app

if __name__ == "__main__":
    # Run the app if this script is executed directly (not recommended for production)
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8001))) 