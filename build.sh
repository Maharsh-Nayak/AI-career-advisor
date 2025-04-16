#!/usr/bin/env bash
# Exit on error
set -o errexit

# Print debug information
echo "Starting build process..."
echo "Python version:"
python --version

# Install Python dependencies
pip install -r requirements.txt

# Download spaCy models
echo "Downloading spaCy models..."
python -m spacy download en_core_web_sm

# Touch SQLite database file to ensure it exists
mkdir -p sqlite-data
touch sqlite-data/db.sqlite3
echo "Created SQLite database file"

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

echo "Build completed successfully" 