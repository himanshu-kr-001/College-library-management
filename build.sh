#!/bin/bash

# Build script for Render deployment
echo "Starting build process..."

# Install dependencies
pip install -r requirements.txt

# Initialize database if it doesn't exist
python setup_database.py

echo "Build completed successfully!"
