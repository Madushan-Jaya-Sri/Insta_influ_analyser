# Instagram Influencer Analyzer

A web application for analyzing Instagram influencer profiles and engagement metrics, developed by Momentro.

## Features

- **URL Analysis**: Enter Instagram profile URLs for analysis
- **Data Upload**: Upload JSON data files from Instagram
- **Advanced Analytics**: Engagement metrics, audience insights, and content analysis
- **Beautiful Visualization**: Interactive charts and comprehensive dashboard
- **Image Management**: Efficient profile and post image handling

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap, JavaScript, Chart.js
- **Data Processing**: Pandas, NumPy
- **AI Integration**: OpenAI API
- **Instagram Data Collection**: Apify API
- **Containerization**: Docker
- **Deployment**: AWS EC2, NGINX
- **CI/CD**: GitHub Actions

## Local Development

### Prerequisites

- Python 3.9+
- Docker and Docker Compose (optional for containerized development)

### Setup Using Python

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the `.env.example` file and add your API keys.

4. Run the application:
   ```bash
   python app.py
   ```

### Setup Using Docker

1. Clone the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Insta_influ_analyser.git
   cd Insta_influ_analyser
   ```

2. Create a `.env` file based on the `.env.example` file and add your API keys.

3. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

4. Access the application at `http://localhost:8000`

## Production Deployment to AWS EC2

### Manual Deployment

1. Launch an EC2 instance (recommend t2.medium or higher with Ubuntu 22.04)

2. SSH into your instance:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. Run the setup script:
   ```bash
   curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/Insta_influ_analyser/main/scripts/setup_ec2.sh | bash
   ```

4. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Insta_influ_analyser.git ~/Insta_influ_analyser
   cd ~/Insta_influ_analyser
   ```

5. Create the `.env` file with your secrets:
   ```bash
   cp .env.example .env
   nano .env  # Edit with your API keys
   ```

6. Start the application:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### CI/CD Setup with GitHub Actions

1. Add the following secrets to your GitHub repository:
   - `SSH_PRIVATE_KEY`: Your EC2 SSH private key
   - `EC2_HOST`: Your EC2 instance IP or DNS

2. Push to the main branch to trigger automatic deployment.

## SSL Configuration

To enable HTTPS:

1. Uncomment the certbot service in `docker-compose.prod.yml`

2. Replace the placeholder in NGINX configuration with your domain name:
   ```bash
   nano nginx/nginx.conf
   # Change server_name _ to server_name your-domain.com
   ```

3. Run the initial certificate request:
   ```bash
   docker-compose run --rm certbot certonly --webroot --webroot-path=/var/www/certbot -d your-domain.com
   ```

4. Update nginx.conf to enable SSL (example provided in the repo)

5. Restart the services:
   ```bash
   docker-compose -f docker-compose.prod.yml down
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Contact

Developed by Momentro 