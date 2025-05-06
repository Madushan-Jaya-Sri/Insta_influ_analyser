#!/bin/bash
# This script tests the installation of wordcloud with build dependencies

echo "===== Testing wordcloud installation ====="

# Create a test environment
mkdir -p /tmp/wordcloud_test
cd /tmp/wordcloud_test

# Create a test Python script
cat > test_wordcloud.py << EOF
try:
    import wordcloud
    print("Successfully imported wordcloud version:", wordcloud.__version__)
    
    # Create a small wordcloud to test
    from wordcloud import WordCloud
    wc = WordCloud(width=400, height=200, max_words=50)
    text = "Python Flask wordcloud test installation success build deploy docker container"
    wordcloud_image = wc.generate(text)
    
    print("Successfully created wordcloud object and generated image")
    print("WORDCLOUD TEST: SUCCESS")
except Exception as e:
    print("Error importing or using wordcloud:", str(e))
    print("WORDCLOUD TEST: FAIL")
    exit(1)
EOF

# Create a Docker test file
cat > Dockerfile.test << EOF
FROM python:3.10-slim

# Install build dependencies
RUN apt-get update && apt-get install -y gcc build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy test script
COPY test_wordcloud.py /app/test_wordcloud.py

# Working directory
WORKDIR /app

# Install wordcloud
RUN pip install --upgrade pip && \
    pip install wordcloud==1.8.1

# Run the test
CMD ["python", "test_wordcloud.py"]
EOF

# Build and run the Docker image
echo "Building Docker test image..."
docker build -t wordcloud-test -f Dockerfile.test .

if [ $? -ne 0 ]; then
    echo "ERROR: Docker build failed"
    exit 1
fi

echo "Running wordcloud test..."
docker run --rm wordcloud-test

if [ $? -ne 0 ]; then
    echo "ERROR: Wordcloud test failed"
    exit 1
fi

echo "===== Wordcloud test completed successfully ====="
echo "Wordcloud can be built and used with the current Dockerfile configuration."
echo "The deployment should work correctly now."

# Clean up
cd - > /dev/null
rm -rf /tmp/wordcloud_test 