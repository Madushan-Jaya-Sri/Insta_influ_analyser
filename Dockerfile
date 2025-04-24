FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for matplotlib and wordcloud
# Also install debugging tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libffi-dev \
    libfreetype6-dev \
    curl \
    nano \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p app/uploads app/data app/static/images/brand app/static/images/profiles app/static/images/posts \
    && chmod -R 777 app/data app/uploads app/static/images

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--preload", "--log-level", "debug", "wsgi:app"] 