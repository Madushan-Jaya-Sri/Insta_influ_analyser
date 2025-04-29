FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies with verbose output
RUN pip install --no-cache-dir --verbose -r requirements.txt
RUN pip install --no-cache-dir --verbose gunicorn==21.2.0
# Explicitly install Flask-Session to ensure it's properly installed
RUN pip install --no-cache-dir --verbose Flask-Session==0.5.0

FROM python:3.11-slim

WORKDIR /app

# Install sqlite3
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/app/data/sessions /app/app/static/uploads \
    && chmod 755 /app/app/data/sessions /app/app/static/uploads

# Set environment variables for Flask
ENV FLASK_APP=run.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Create a non-root user and give ownership of app directory
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "run:app"] 