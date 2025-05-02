FROM python:3.10-slim

# Install Nginx and required packages
RUN apt-get update && apt-get install -y nginx curl unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
RUN rm -f /etc/nginx/sites-enabled/default

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/app/static /app/app/uploads /app/app/data
RUN mkdir -p /app/app/static/css /app/app/static/js /app/app/static/images/profiles /app/app/static/images/posts /app/app/static/images/brand
RUN mkdir -p /app/app/static/font-awesome/4.3.0/css /app/app/static/font-awesome/4.3.0/fonts

# Download and install Font Awesome
RUN curl -L https://fontawesome.com/v4/assets/font-awesome-4.3.0.zip -o /tmp/font-awesome.zip \
    && unzip -q /tmp/font-awesome.zip -d /tmp \
    && cp -r /tmp/font-awesome-4.3.0/css/* /app/app/static/font-awesome/4.3.0/css/ \
    && cp -r /tmp/font-awesome-4.3.0/fonts/* /app/app/static/font-awesome/4.3.0/fonts/ \
    && rm -rf /tmp/font-awesome* || echo "Font Awesome download failed, continuing anyway"

# Create a basic style.css file
RUN echo "/* Basic styles */\nbody {\n  font-family: 'Arial', sans-serif;\n  line-height: 1.6;\n  margin: 0;\n  padding: 0;\n  color: #333;\n}\n.container {\n  width: 100%;\n  max-width: 1200px;\n  margin: 0 auto;\n  padding: 15px;\n}" > /app/app/static/css/style.css

# Create empty logo files (will be populated by start.sh)
RUN touch /app/app/static/images/brand/momentro-logo.png \
    && touch /app/app/static/images/brand/momentro_logo.png \
    && touch /app/app/static/favicon.ico

# Ensure directories have proper permissions
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