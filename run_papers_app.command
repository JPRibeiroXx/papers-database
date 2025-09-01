#!/bin/bash

# Papers Desktop Database - Launcher Script
# This script can be double-clicked to start the Papers Database app

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to the script directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating it..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
if [ ! -f "venv/.deps_installed" ]; then
    echo "Installing dependencies..."
    pip install --upgrade pip
    cd papers-desktop-app
    pip install -r requirements.txt
    cd ..
    touch venv/.deps_installed
fi

# Change to app directory and run
cd papers-desktop-app

echo "Starting Papers Desktop Database..."
echo "Close this terminal window to quit the app."

# Run the application
python -m app.main

# Keep terminal open after app closes
echo ""
echo "App closed. Press any key to close this window..."
read -n 1
