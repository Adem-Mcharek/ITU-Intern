#!/bin/bash

echo "ITU WebTV Processing System - First Time Setup"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed!"
    echo "Please install Python 3.8+ from https://python.org/downloads/"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON=python3
    PIP=pip3
else
    PYTHON=python
    PIP=pip
fi

echo "Python found:"
$PYTHON --version

# Create virtual environment
echo
echo "Creating virtual environment..."
$PYTHON -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo
echo "Installing dependencies (this may take several minutes)..."
pip install -r requirements.txt

# Initialize database
echo
echo "Initializing database..."
python init_db.py

# Create admin user
echo
echo "Creating admin user..."
python create_admin.py

echo
echo "Setup complete! You can now start the application with:"
echo "./start.sh"
echo
echo "Or manually with:"
echo "source venv/bin/activate"
echo "python run.py" 