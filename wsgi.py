import sys
import os

# Add the current directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import create_app from main.py instead of app.py
from main import create_app

application = create_app()

if __name__ == "__main__":
    application.run() 