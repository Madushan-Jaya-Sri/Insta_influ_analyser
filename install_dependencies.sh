#!/bin/bash
# Script to install all required dependencies for Instagram Influencer Analyzer

echo "===== Installing dependencies for Instagram Influencer Analyzer ====="

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Linux OS detected"
    if [ -x "$(command -v apt-get)" ]; then
        echo "Debian/Ubuntu system detected, installing build dependencies..."
        sudo apt-get update
        sudo apt-get install -y build-essential python3-dev gcc
    elif [ -x "$(command -v yum)" ]; then
        echo "Red Hat/CentOS system detected, installing build dependencies..."
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y python3-devel
    else
        echo "WARNING: Could not determine Linux package manager. You may need to install build tools manually."
        echo "Required packages: gcc, python-dev, build-essential"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected"
    if [ -x "$(command -v brew)" ]; then
        echo "Homebrew found, installing build dependencies..."
        brew install gcc
    else
        echo "WARNING: Homebrew not found. Consider installing it to get build tools."
        echo "Visit https://brew.sh/ for installation instructions."
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Windows detected"
    echo "Consider installing Visual C++ Build Tools or using WSL for Linux compatibility."
    echo "Visit: https://visualstudio.microsoft.com/visual-cpp-build-tools/"
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "ERROR: pip is not installed. Please install Python and pip."
    exit 1
fi

# Create and activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Creating a virtual environment..."
    python -m venv venv
    
    # Activate the virtual environment based on OS
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
else
    echo "Using existing virtual environment: $VIRTUAL_ENV"
fi

# Uninstall potentially conflicting packages
echo "Uninstalling potentially conflicting packages..."
pip uninstall -y werkzeug flask flask-login

# Install key packages first
echo "Installing key packages..."
pip install Werkzeug==2.0.3
pip install Flask==2.0.1
pip install Flask-Login==0.5.0
pip install Flask-SQLAlchemy==2.5.1

# Try to install wordcloud-binary (pre-compiled) if building from source fails
echo "Installing remaining dependencies..."
pip install -r requirements.txt || (
    echo "Some dependencies failed to install. Trying alternative approach..."
    sed -i.bak 's/wordcloud==1.8.1/wordcloud-binary==1.8.1/g' requirements.txt
    pip install -r requirements.txt
)

echo "===== Dependency installation completed ====="
echo ""
echo "You can now run the application with:"
echo "python run.py" 