#!/usr/bin/env python3
"""
Script to create or promote a developer user
"""
import sys
from app import create_app, db
from app.models import User

def create_developer():
    """Create or promote a developer user"""
    app = create_app()
    
    with app.app_context():
        print("Developer User Management")
        print("=" * 40)
        
        # Show existing users
        users = User.query.all()
        if users:
            print("\nExisting users:")
            for i, user in enumerate(users, 1):
                role = "Developer" if user.is_developer else ("Admin" if user.is_admin else "User")
                status = "Active" if user.is_active else "Inactive"
                print(f"{i}. {user.email} - {role} ({status})")
        else:
            print("\nNo existing users found.")
        
        print("\nOptions:")
        print("1. Promote existing user to developer")
        print("2. Create new developer user")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            if not users:
                print("No users available to promote.")
                return
            
            try:
                user_num = int(input(f"Enter user number (1-{len(users)}): "))
                if 1 <= user_num <= len(users):
                    user = users[user_num - 1]
                    user.is_developer = True
                    user.is_admin = True  # Developers are automatically admins
                    user.is_active = True
                    
                    db.session.commit()
                    print(f"\n✅ User {user.email} promoted to Developer successfully!")
                else:
                    print("Invalid user number.")
            except ValueError:
                print("Invalid input. Please enter a number.")
                
        elif choice == "2":
            email = input("Enter email address: ").strip().lower()
            
            # Check if user already exists
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                print(f"User {email} already exists.")
                return
            
            password = input("Enter password: ").strip()
            if len(password) < 6:
                print("Password must be at least 6 characters long.")
                return
            
            # Create new developer user
            user = User(
                email=email,
                is_developer=True,
                is_admin=True,  # Developers are automatically admins
                is_active=True
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f"\n✅ Developer user {email} created successfully!")
            
        elif choice == "3":
            print("Goodbye!")
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    create_developer() 