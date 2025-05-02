#!/bin/bash
set -e

# Set up necessary directories
echo "Setting up application directories..."
mkdir -p /app/app/static /app/app/uploads /app/app/data
mkdir -p /app/app/static/css /app/app/static/js 
mkdir -p /app/app/static/images/profiles /app/app/static/images/posts /app/app/static/images/brand
chmod -R 777 /app/app/static /app/app/uploads /app/app/data

# Create missing CSS file
echo "Creating missing CSS file..."
cat > /app/app/static/css/style.css << 'EOF'
/* Basic styles */
body {
  font-family: 'Arial', sans-serif;
  line-height: 1.6;
  margin: 0;
  padding: 0;
  color: #333;
}
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 15px;
}
EOF

# Check if mounted logo files exist
if [ -f "/app/app/static/images/brand/momentro-logo.png" ]; then
    echo "Logo file momentro-logo.png exists in mounted volume"
    ls -l /app/app/static/images/brand/momentro-logo.png
else
    echo "Logo file does not exist in mounted volume - creating placeholder"
    # Create a simple colored placeholder logo file
    cat > /app/app/static/images/brand/momentro-logo.png << 'EOF'
iVBORw0KGgoAAAANSUhEUgAAAMgAAABkCAYAAADDhn8LAAABhGlDQ1BJQ0MgcHJvZmlsZQAAKJF9kT1Iw0AcxV9TpUUqgmYo4pChOlkQFXHUKhShQqgVWnUwufQLmjQkKS6OgmvBwY/FqoOLs64OroIg+AHi5uak6CIl/i8ptIjx4Lgf7+497t4BQqPCVLNrAlA1y0jFY2I2tyoGXtGHIAYQRUJipp7MLGbhOb7u4ePrXZRneZ/7cwwoeZMBPpF4jumGRbxBPLNp6Zz3iUOsJCnE58RjBl2Q+JHrsstvnIsOCzwzZGRS88QhYrHYwXIHs5KhEk8RRxRVo3wh67LCeYuzWqmx1j35C4N5bSXNdZrDiGMJCSQhQkYNZVRgIUqrRoqJFO3HPPzDjj9JLplcZTByLKAKFZLjB/+D392ahckJNykYA7pfbPtjBAjsAs26bX8f23bzBPA/A1d6219uAjOfpDe7WvQI6N8GLq7bmpIHuN0B+p50yZAcyU9TKBSA9zP6phwQugX6Vt3e2vs4fQAy1FXqBjg4BMaKlL3u8e5gZ2//nmn19wMkHXK45czAVAAAAAZiS0dEAP8A/wD/oL2nkwAAAAlwSFlzAAAuIwAALiMBeKU/dgAAAAd0SU1FB+YFAgcPKoqcwDUAAAAZdEVYdENvbW1lbnQAQ3JlYXRlZCB3aXRoIEdJTVBXgQ4XAAADhUlEQVR42u3csWpUQRzH8V9ys0QUozHZQqy1CLETrIJiYWOT0kIsBMEn0NbCp7ASLE1jo/gGoj6B2BkQiYmFtxcRQ+Lm5vrftsjOZhJuJDe7Ozv380GaK8na/GF/szPzczt2Y96JRmEbHMePyfbXZr+e/YKvm1hHDnHqWvtLp55rrfcDu+pjzm8+k3x+vp9GR/k8MfP86Tw+bwk2xJeWTfPbbNs229jUVyzfGPuxS8JW1Zhr/P3fG9qRYjNQ4Df1Gz4gQSBBgECCAIEEAQIJAgQSBAhylcdg5+yHXZl8FDtmHsS2mQf9Tm77yexUfp7k+0nym0lrUZvfbsrP9cvm6Y9n8f7D09zXt2qGGiTfud8tPY9dM/f7neABPHZ6Lzad3u1/7FLvYzw/uT3f6ZzMr+k+iiedu/nH3EiQ4Tv97nA8PnMp385ZhP0fFlCKoQZ5tPQitq++zcMVvfmbZBOBJqhBju1bjG3zy/m28OE4lW9rTpqbZRgkSBNtv7ArTuRhSkEyibXbLSRIk23rXcofrSokfVKDxBQjUQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAD+MRCqY2BgIFSL3TKAAIEEAQIJAgQSBAgkCBBIECCQIEAgQYBAgkw0tXa6DU2yAgECCQIEEgQIJAgQSBAgkCBAIEGAQIIAgQQBAgkCBBIECCQIEEiQiWZ4xMaBPQgAABXjDPpBcvfajXwUw9FvuvNv5Odf8eYsZkpwBn0ztY5qD0OC/Lw5+3VxOj5+Ger2u/H21EL/GvKDw3vjwu7FfLn2OT7sBiRIo4zuSj90+VJ8efUsPq8e6K/f8v2eeHb5QPy6fKD//tqn1Vh8dSs+dXaZiU1qkGb65+I9+/LFPE1KJyrLSmPfUm45aTzuPD3dEg8SbZAdPw5Vq14dv77/Zr7stNu53i93lGXdNGxTKJxqb49aUpUeIxgaKg/k5Wbh74cXZZpSlpJlZa5eU8s/KtHlqCW9t5Kaa6kzqVfPU9tY9kEyplA71c9TM1iVnbPqfTdaUl9f/TtsfAdpqK2XATR2C2+8BiRIr+F04qNBfDR6o0G8ww5/rV4GzRr7mVHPfwDN94mZ6M/Nl2etGvn52nnrDO7I69eP/I4y01ZnXWfq6FfKTuXGyHfIujPeD9fGs6p1tUrCzMT/7U9r+iI0Cw2tCQAAAABJRU5ErkJggg==
EOF
    base64 -d /app/app/static/images/brand/momentro-logo.png > /app/app/static/images/brand/momentro-logo.png.tmp
    mv /app/app/static/images/brand/momentro-logo.png.tmp /app/app/static/images/brand/momentro-logo.png
fi

# Create both logo filenames
cp -f /app/app/static/images/brand/momentro-logo.png /app/app/static/images/brand/momentro_logo.png
chmod 644 /app/app/static/images/brand/momentro-logo.png
chmod 644 /app/app/static/images/brand/momentro_logo.png

# Also copy to the root /static directory (for Nginx root directive)
mkdir -p /app/static/images/brand
cp -f /app/app/static/images/brand/momentro-logo.png /app/static/images/brand/
cp -f /app/app/static/images/brand/momentro_logo.png /app/static/images/brand/
chmod 644 /app/static/images/brand/momentro-logo.png
chmod 644 /app/static/images/brand/momentro_logo.png

# Create favicon
echo "Creating favicon..."
cp -f /app/app/static/images/brand/momentro-logo.png /app/app/static/favicon.ico
chmod 644 /app/app/static/favicon.ico

# Debug static files (check directory structure)
echo "Static files directory structure:"
find /app/app/static -type d | sort
find /app/static -type d | sort

# List created files
echo "Created static files:"
find /app/app/static -type f | sort
find /app/static -type f | sort

# Debug Font Awesome files
echo "Checking Font Awesome files:"
ls -la /app/app/static/font-awesome/4.3.0/css/ || echo "Font Awesome directory not found"

echo "Starting Nginx..."
nginx -t && nginx

echo "Starting Gunicorn..."
cd /app
gunicorn --bind 127.0.0.1:8000 --timeout 120 --workers 3 --log-level debug --access-logfile - --error-logfile - app:app

# Keep the container running if gunicorn fails
exec "$@"