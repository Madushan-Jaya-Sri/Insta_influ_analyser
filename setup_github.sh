#!/bin/bash

echo "Setting up GitHub repository for Instagram Influencer Analyzer"

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install git first."
    exit 1
fi

# Initialize git repository if not already initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
fi

# Create .gitignore
if [ ! -f ".gitignore" ]; then
    echo "Creating .gitignore file..."
    cat > .gitignore << 'EOL'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env

# Local files
app/uploads/*
app/data/*
app/static/images/posts/*
app/static/images/profiles/*
!app/uploads/.gitkeep
!app/data/.gitkeep
!app/static/images/posts/.gitkeep
!app/static/images/profiles/.gitkeep
!app/static/images/brand/.gitkeep

# IDE files
.idea/
.vscode/
*.swp
*.swo

# Logs
*.log
EOL
fi

# Create empty .gitkeep files to preserve directory structure
mkdir -p app/uploads app/data app/static/images/posts app/static/images/profiles app/static/images/brand
touch app/uploads/.gitkeep app/data/.gitkeep app/static/images/posts/.gitkeep app/static/images/profiles/.gitkeep app/static/images/brand/.gitkeep

# Make the deploy script executable
chmod +x deploy_ec2.sh

# Add all files
git add .

echo "All files have been added to git staging area."
echo ""
echo "Next steps:"
echo "1. Create a new GitHub repository at https://github.com/new"
echo "2. Run the following commands to push your code:"
echo "   git commit -m 'Initial commit'"
echo "   git branch -M main"
echo "   git remote add origin https://github.com/yourusername/Insta_influ_analyser.git"
echo "   git push -u origin main"
echo ""
echo "3. Add the required GitHub secrets for CI/CD:"
echo "   - AWS_SSH_KEY (the contents of your EC2 .pem file)"
echo "   - AWS_HOST (your EC2 instance hostname or IP, e.g., 65.0.181.3)"
echo "   - AWS_USERNAME (your EC2 username, e.g., ubuntu)"
echo "   - OPENAI_API_KEY"
echo "   - APIFY_API_TOKEN"
echo "   - SECRET_KEY" 