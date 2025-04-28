#!/bin/bash

# Script to directly fix the issues on the EC2 instance
set -e

echo "=== DIRECT FIX SCRIPT ==="

# 1. Fix the static files issue
echo "Creating static directories..."
mkdir -p /home/ubuntu/Insta_influ_analyser/app/static/css
mkdir -p /home/ubuntu/Insta_influ_analyser/app/static/images/brand

# 2. Create style.css in the correct location
echo "Creating style.css..."
cat > /home/ubuntu/Insta_influ_analyser/app/static/css/style.css << 'EOF'
/* Global Styles */
body {
    font-family: 'Roboto', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f5f5f5;
    margin: 0;
    padding: 0;
}

.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 15px;
}

/* Navigation */
.navbar {
    background-color: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.navbar-brand img {
    height: 40px;
}

/* Forms */
.form-control {
    border: 1px solid #ddd;
    border-radius: 4px;
    padding: 10px;
    margin-bottom: 15px;
    width: 100%;
}

.btn-primary {
    background-color: #007bff;
    border: none;
    padding: 10px 20px;
    color: white;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s;
}

.btn-primary:hover {
    background-color: #0069d9;
}

/* Authentication Forms */
.auth-form {
    max-width: 500px;
    margin: 40px auto;
    padding: 30px;
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.auth-form h2 {
    margin-bottom: 20px;
    text-align: center;
}

/* Flash Messages */
.flash-messages {
    margin: 20px 0;
}

.alert {
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
}

.alert-success {
    background-color: #d4edda;
    color: #155724;
    border: 1px solid #c3e6cb;
}

.alert-danger {
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
}

/* Dashboard */
.dashboard-card {
    background-color: #fff;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    padding: 20px;
    margin-bottom: 20px;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .auth-form {
        margin: 20px auto;
        padding: 20px;
    }
}
EOF

# 3. Create a placeholder logo
echo "Creating logo file..."
mkdir -p /home/ubuntu/Insta_influ_analyser/app/static/images/brand
curl -s https://via.placeholder.com/200x50/FFFFFF/000000?text=Momentro -o /home/ubuntu/Insta_influ_analyser/app/static/images/brand/momentro-logo.png

# 4. Fix data directory
echo "Setting up data directory..."
mkdir -p /home/ubuntu/Insta_influ_analyser/app/data/sessions
echo "[]" > /home/ubuntu/Insta_influ_analyser/app/data/users.json

# 5. Set proper permissions
echo "Setting permissions..."
chmod -R 777 /home/ubuntu/Insta_influ_analyser/app/static
chmod -R 777 /home/ubuntu/Insta_influ_analyser/app/data
chmod -R 777 /home/ubuntu/Insta_influ_analyser/uploads
chmod -R 777 /home/ubuntu/Insta_influ_analyser/data
chmod -R 777 /home/ubuntu/Insta_influ_analyser/static

# 6. Update nginx.conf
echo "Updating nginx.conf..."
cat > /home/ubuntu/Insta_influ_analyser/nginx/nginx.conf << 'EOF'
server {
    listen 80;
    server_name 13.126.220.175;

    # Increase max body size for larger file uploads
    client_max_body_size 100M;

    # Serve static files directly
    location /static/ {
        alias /app/app/static/;
        expires 30d;
        add_header Cache-Control "public, max-age=2592000";
    }

    # Handle uploads directory if needed
    location /uploads/ {
        alias /app/uploads/;
        expires off;
        add_header Cache-Control "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0";
    }

    location / {
        proxy_pass http://app:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # For streaming responses (SSE or long-polling)
        proxy_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
    }
}
EOF

# 7. Update docker-compose.prod.yml
echo "Updating docker-compose.prod.yml..."
cat > /home/ubuntu/Insta_influ_analyser/docker-compose.prod.yml << 'EOF'
services:
  app:
    build: .
    restart: always
    container_name: flask_app
    expose:
      - "5000"  # Only expose to internal network, not to host
    volumes:
      - ./uploads:/app/uploads
      - ./data:/app/data
      - ./app/data:/app/app/data  # Add this mapping for user data
      - ./static:/app/static 
      - ./app/static:/app/app/static  # Add this mapping for app static files
    env_file:
      - .env
    environment:
      - FLASK_ENV=production
    networks:
      - app_network

  nginx:
    image: nginx:1.25-alpine
    restart: always
    container_name: nginx
    ports:
      - "80:80"  # Map port 80 to host
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf
      - ./uploads:/app/uploads
      - ./static:/app/static
      - ./app/static:/app/app/static  # Add this mapping for app static files
    depends_on:
      - app
    networks:
      - app_network

networks:
  app_network:
    driver: bridge
EOF

# 8. Restart the containers
echo "Restarting containers..."
cd /home/ubuntu/Insta_influ_analyser
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# 9. Copy files into the container
echo "Waiting for containers to start..."
sleep 10
echo "Copying files into the container..."
docker cp /home/ubuntu/Insta_influ_analyser/app/static/css/style.css flask_app:/app/app/static/css/
docker cp /home/ubuntu/Insta_influ_analyser/app/static/images/brand/momentro-logo.png flask_app:/app/app/static/images/brand/

# 10. Fix permissions inside the container
echo "Fixing permissions inside the container..."
docker exec flask_app mkdir -p /app/app/data/sessions /app/app/static/css /app/app/static/images/brand
docker exec flask_app chmod -R 777 /app/app/data /app/app/static

echo "=== Fix completed ==="
echo "Please test your application now at http://13.126.220.175" 