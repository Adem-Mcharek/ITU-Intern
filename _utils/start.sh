#!/bin/bash

echo "Starting ITU WebTV Processing System..."
echo

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run setup first: python -m venv venv"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if database exists
if [ ! -f "app.db" ] && [ ! -f "instance/app.db" ]; then
    echo "No database found. Initializing..."
    python init_db.py
fi

# Start the application
echo "Starting server..."
python run.py 