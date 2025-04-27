"""
Debug script for the Flask application
This creates a simplified version of the app for testing
"""
import os
import sys
from flask import Flask, jsonify

# Add the parent directory to the path so we can import correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(parent_dir)

# First, try to import the create_app function
try:
    from run import create_app
    print("Successfully imported create_app from run.py")
except Exception as e:
    print(f"Error importing create_app: {e}")
    sys.exit(1)

# Create a simple test app
def create_test_app():
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return jsonify({
            'status': 'ok',
            'message': 'Debug app is running',
            'env': dict(os.environ)
        })
    
    return app

def main():
    print("Starting debug process")
    
    # Check if directories exist
    print("\nChecking directories:")
    for path in ['app/static', 'app/data', 'app/uploads', 'app/data/sessions']:
        full_path = os.path.join(parent_dir, path)
        exists = os.path.exists(full_path)
        print(f" - {path}: {'exists' if exists else 'MISSING'}")
        if not exists:
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"   Created directory: {path}")
            except Exception as e:
                print(f"   Failed to create: {e}")
    
    # Print environment variables
    print("\nEnvironment variables:")
    important_vars = ['FLASK_APP', 'FLASK_ENV', 'SECRET_KEY', 'OPENAI_API_KEY', 'APIFY_API_TOKEN']
    for var in important_vars:
        value = os.getenv(var)
        if var.endswith('KEY') or var.endswith('TOKEN') and value:
            value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
        print(f" - {var}: {value if value else 'NOT SET'}")
    
    # Try to create the real app
    print("\nAttempting to create the application:")
    try:
        app = create_app()
        print(" - App created successfully")
        print(" - App config:", app.config.keys())
        # Try to list a route
        try:
            routes = [f"{rule.endpoint} - {rule.rule}" for rule in app.url_map.iter_rules()]
            print(f" - Routes: {routes[:3]}... (total: {len(routes)})")
        except Exception as e:
            print(f" - Error listing routes: {e}")
    except Exception as e:
        print(f" - Error creating app: {e}")
        # If the real app fails, create a test app
        print("\nCreating test app instead:")
        try:
            app = create_test_app()
            print(" - Test app created successfully")
        except Exception as e:
            print(f" - Error creating test app: {e}")
            sys.exit(1)
    
    # Run the app
    print("\nStarting app in debug mode")
    app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    main() 