#!/usr/bin/env python3
"""
Simple Database Initialization Script
"""

from app import create_app, db

def init_database():
    """Initialize the database with all tables"""
    print("🚀 Initializing database...")
    
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Show database info
        print(f"✅ Database file: {app.config['SQLALCHEMY_DATABASE_URI']}")
        print(f"✅ Upload folder: {app.config['UPLOAD_FOLDER']}")

if __name__ == '__main__':
    init_database() 