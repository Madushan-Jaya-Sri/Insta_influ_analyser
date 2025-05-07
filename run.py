"""
Development server entry point.
This file is used for local development only.
For production, use wsgi.py with Gunicorn.
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8001, debug=True)