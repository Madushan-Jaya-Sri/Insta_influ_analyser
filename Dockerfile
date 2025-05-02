FROM python:3.10-slim

# Install Nginx and required packages
RUN apt-get update && apt-get install -y nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/app/static /app/app/uploads /app/app/data
RUN mkdir -p /app/app/static/css /app/app/static/js /app/app/static/images/profiles /app/app/static/images/posts
RUN mkdir -p /app/app/static/font-awesome/4.3.0/css /app/app/static/font-awesome/4.3.0/fonts
RUN chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || (cat /tmp/pip-log.txt && exit 1)

# Copy application code
COPY . .

# Make start script executable
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose port
EXPOSE 80

# Run start script
CMD ["/start.sh"] 