#!/usr/bin/env python
# Deployment Diagnostic Script for Instagram Influencer Analyzer
# Run this script in your production environment to diagnose issues

import os
import sys
import json
import traceback
from datetime import datetime
import importlib.util

def header(text):
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def check_python_version():
    header("Python Version Check")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    if sys.version_info < (3, 8):
        print("❌ WARNING: Python version is below 3.8, which may cause compatibility issues.")
    else:
        print("✅ Python version is 3.8 or higher.")

def check_environment_variables():
    header("Environment Variables Check")
    required_vars = [
        'FLASK_APP',
        'FLASK_ENV',
        'OPENAI_API_KEY',
        'SECRET_KEY',
        'DATABASE_URL'
    ]
    
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            masked_value = value[:3] + '******' + value[-3:] if len(value) > 10 else '******'
            print(f"✅ {var} is set ({masked_value})")
        else:
            print(f"❌ {var} is NOT set!")

def check_directory_permissions():
    header("Directory Permissions Check")
    # Get application root
    app_root = os.path.abspath(os.path.dirname(__file__))
    
    # Important directories to check
    dirs_to_check = [
        os.path.join(app_root, 'data'),
        os.path.join(app_root, 'app', 'static', 'images', 'profiles'),
        os.path.join(app_root, 'app', 'static', 'images', 'posts'),
        os.path.join(app_root, 'app', 'static', 'images', 'misc'),
        os.path.join(app_root, 'app', 'static', 'charts'),
    ]
    
    for directory in dirs_to_check:
        print(f"Checking {directory}:")
        
        if not os.path.exists(directory):
            print(f"  ❌ Directory doesn't exist")
            try:
                os.makedirs(directory, exist_ok=True)
                print(f"  ✅ Created directory")
            except Exception as e:
                print(f"  ❌ Failed to create directory: {str(e)}")
                continue
        
        # Check if writable
        try:
            test_file = os.path.join(directory, '.write_test')
            with open(test_file, 'w') as f:
                f.write('write test')
            os.remove(test_file)
            print(f"  ✅ Directory is writable")
        except Exception as e:
            print(f"  ❌ Directory is NOT writable: {str(e)}")

def check_dependencies():
    header("Dependency Check")
    required_packages = [
        'flask',
        'flask_login',
        'flask_sqlalchemy',
        'flask_wtf',
        'numpy',
        'pandas',
        'openai',
        'matplotlib',
        'pillow',
        'wordcloud',
        'requests'
    ]
    
    for package in required_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is None:
                print(f"❌ {package} is NOT installed")
                continue
                
            # Try to import and get version
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'unknown version')
            print(f"✅ {package} is installed ({version})")
        except Exception as e:
            print(f"❌ Error checking {package}: {str(e)}")

def check_database_connection():
    header("Database Connection Check")
    try:
        # Avoid importing at the top level to prevent issues
        from app import db
        from app.models.user import User
        
        # Test the connection by making a simple query
        user_count = User.query.count()
        print(f"✅ Database connection successful. Found {user_count} users.")
    except Exception as e:
        print(f"❌ Database connection error: {str(e)}")
        traceback.print_exc()

def create_test_user():
    header("Test User Creation")
    try:
        from app import db, create_app
        from app.models.user import User
        from werkzeug.security import generate_password_hash
        
        app = create_app()
        with app.app_context():
            # Check if test user already exists
            test_user = User.query.filter_by(email='test@example.com').first()
            
            if test_user:
                print(f"✅ Test user already exists (ID: {test_user.id})")
            else:
                # Create a test user
                new_user = User(
                    username='testuser',
                    email='test@example.com',
                    password_hash=generate_password_hash('password123')
                )
                db.session.add(new_user)
                db.session.commit()
                print(f"✅ Created test user with ID: {new_user.id}")
                print(f"   Email: test@example.com")
                print(f"   Password: password123")
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        traceback.print_exc()

def run_diagnostics():
    header("INSTAGRAM INFLUENCER ANALYZER - DEPLOYMENT DIAGNOSTICS")
    print(f"Time: {datetime.now().isoformat()}")
    print(f"Working directory: {os.getcwd()}")
    
    try:
        check_python_version()
        check_environment_variables()  
        check_directory_permissions()
        check_dependencies()
        
        print("\nWould you like to check the database connection? (y/n)")
        if input().lower() == 'y':
            check_database_connection()
            
            print("\nWould you like to create a test user? (y/n)")
            if input().lower() == 'y':
                create_test_user()
    except Exception as e:
        print(f"❌ Error during diagnostics: {str(e)}")
        traceback.print_exc()
    
    header("DIAGNOSTICS COMPLETE")
    print("If you're experiencing issues, check the errors above.")
    print("For more help, please check the documentation or create an issue on GitHub.")

if __name__ == "__main__":
    run_diagnostics() 