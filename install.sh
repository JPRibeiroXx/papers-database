#!/bin/bash

# Papers Database Installation Script
# This script sets up the Papers Database application

echo "🚀 Installing Papers Database..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating application directories..."
mkdir -p PDFs
mkdir -p logs

# Set permissions
echo "🔐 Setting permissions..."
chmod +x run_papers_app.command
chmod +x install.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📖 To get started:"
echo "   1. Activate the virtual environment: source venv/bin/activate"
echo "   2. Run the application: python -m app.main"
echo "   3. Or use the launcher scripts in the project directory"
echo ""
echo "📚 For more information, see README.md"
echo ""
echo "🔒 This software is licensed for personal use only."
echo "   See LICENSE file for details."
