#!/usr/bin/env python3
"""
Create Admin User Script for ITU Intern

This script creates the first admin user for the application.
Run this after setting up the database with flask db upgrade.

Usage:
    python create_admin.py <admin_email> [password]
    
If password is not provided, you'll be prompted to enter it securely.
"""

import sys
import os
import getpass
from app import create_app, db
from app.models import User, AllowedUser

def create_admin_user(email, password=None):
    """Create an admin user"""
    app = create_app()
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email.lower()).first()
        if existing_user:
            print(f"User {email} already exists!")
            if existing_user.is_admin:
                print("User is already an admin.")
            else:
                existing_user.is_admin = True
                db.session.commit()
                print("User has been promoted to admin.")
            return
        
        # Get password if not provided
        if not password:
            password = getpass.getpass("Enter password for admin user: ")
            password_confirm = getpass.getpass("Confirm password: ")
            
            if password != password_confirm:
                print("Passwords don't match!")
                return False
        
        # Create allowed user entry if it doesn't exist
        allowed_user = AllowedUser.query.filter_by(email=email.lower()).first()
        if not allowed_user:
            allowed_user = AllowedUser(email=email.lower(), is_used=True)
            db.session.add(allowed_user)
        else:
            allowed_user.is_used = True
        
        # Create admin user
        admin_user = User(
            email=email.lower(),
            is_admin=True,
            is_active=True
        )
        admin_user.set_password(password)
        
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Admin user created successfully!")
        print(f"Email: {email}")
        print(f"Admin: Yes")
        print("\nYou can now log in with these credentials.")
        return True

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_admin.py <admin_email> [password]")
        print("Example: python create_admin.py admin@example.com")
        sys.exit(1)
    
    email = sys.argv[1]
    password = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Basic email validation
    if '@' not in email or '.' not in email.split('@')[1]:
        print("Please provide a valid email address")
        sys.exit(1)
    
    try:
        success = create_admin_user(email, password)
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error creating admin user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 