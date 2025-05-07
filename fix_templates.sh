#!/bin/bash

# Fix template slice issues script
echo "Fixing template slice issues in dashboard.html and influencer_detail.html"

# Create directory for backup
mkdir -p template_backups

# Dashboard template fixes
if [ -f "app/templates/dashboard.html" ]; then
    # Backup original
    cp app/templates/dashboard.html template_backups/dashboard.html.bak
    
    # Fix slice issues with main_interests and top_hashtags
    sed -i 's/{% for interest in influencer\.main_interests\[:3\] %}/{% for interest in (influencer.main_interests|list)[:3] %}/g' app/templates/dashboard.html
    sed -i 's/{% for hashtag_item in influencer\.top_hashtags\[:3\] %}/{% for hashtag_item in (influencer.top_hashtags|list)[:3] %}/g' app/templates/dashboard.html
    
    echo "✓ Fixed dashboard.html"
else
    echo "✗ dashboard.html not found"
fi

# Influencer detail template fixes
if [ -f "app/templates/influencer_detail.html" ]; then
    # Backup original
    cp app/templates/influencer_detail.html template_backups/influencer_detail.html.bak
    
    # Fix all unhashable object issues
    sed -i 's/{% for tag in post\.hashtags\[:5\] %}/{% for tag in (post.hashtags|list)[:5] %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for hashtag_item in influencer\.top_hashtags %}/{% for hashtag_item in (influencer.top_hashtags|list) %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for mention_item in influencer\.top_mentions %}/{% for mention_item in (influencer.top_mentions|list) %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for interest in influencer\.main_interests %}/{% for interest in (influencer.main_interests|list) %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for interest in influencer\.related_interests %}/{% for interest in (influencer.related_interests|list) %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for topic in influencer\.key_topics %}/{% for topic in (influencer.key_topics|list) %}/g' app/templates/influencer_detail.html
    sed -i 's/{% for brand in influencer\.affiliated_brands %}/{% for brand in (influencer.affiliated_brands|list) %}/g' app/templates/influencer_detail.html
    
    echo "✓ Fixed influencer_detail.html"
else
    echo "✗ influencer_detail.html not found"
fi

# Fix database.py
if [ -f "app/database.py" ]; then
    # Backup original
    cp app/database.py template_backups/database.py.bak
    
    # Add fix for database initialization
    sed -i '/if '"'"'user'"'"' not in tables:/a\            else:\n                app.logger.info("Tables already exist, skipping creation")' app/database.py
    
    # Add try-except improvement for handling existing tables
    sed -i '/except Exception as e:/a\            if "table user already exists" in str(e):\n                app.logger.info("Table '"'"'user'"'"' already exists, continuing normally")\n            else:' app/database.py
    
    echo "✓ Fixed app/database.py"
else
    echo "✗ app/database.py not found"
fi

# Fix fix_database.py
if [ -f "fix_database.py" ]; then
    # Backup original
    cp fix_database.py template_backups/fix_database.py.bak
    
    # Add try-except improvement for database fixes
    sed -i '/if '"'"'user'"'"' not in existing_tables:/a\            try:' fix_database.py
    sed -i '/logger\.info("User table already exists, no action needed")/a\            except Exception as e:\n                if "table user already exists" in str(e):\n                    logger.info("Table already exists error caught, this is normal and can be ignored")\n                    # Even if we get this error, we should still have the table\n                    logger.info("SUCCESS: User table exists")\n                else:\n                    logger.error(f"Error creating tables: {str(e)}")\n                    import traceback\n                    logger.error(traceback.format_exc())\n                    return False' fix_database.py
    
    echo "✓ Fixed fix_database.py"
else
    echo "✗ fix_database.py not found"
fi

echo "All fixes applied. Restarting containers..."

# Restart containers
docker-compose down || echo "Failed to down containers, may not be using docker-compose"
docker stop instagram-nginx instagram-app || echo "Failed to stop containers directly"
docker-compose up -d || (
    echo "Restarting containers directly..."
    docker start instagram-app
    docker start instagram-nginx
)

echo "Containers restarted! Check the logs for any remaining issues."
echo "You may want to run: docker logs instagram-app" 