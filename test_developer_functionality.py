#!/usr/bin/env python3
"""
Test script for developer functionality
"""
from app import create_app, db
from app.models import User

def test_developer_functionality():
    """Test developer role functionality"""
    app = create_app()
    
    with app.app_context():
        print("Testing Developer Functionality")
        print("=" * 40)
        
        # Test 1: Check user roles
        users = User.query.all()
        for user in users:
            print(f"\nUser: {user.email}")
            print(f"  - Role: {user.role}")
            print(f"  - Has Admin Access: {user.has_admin_access}")
            print(f"  - Has Developer Access: {user.has_developer_access}")
            print(f"  - Can Manage Users: {user.can_manage_users()}")
            print(f"  - Can Manage Admins: {user.can_manage_admins()}")
        
        # Test 2: Create test users with different roles
        print("\n" + "=" * 40)
        print("Creating test users...")
        
        # Clean up any existing test users first
        for email in ['testdev@example.com', 'testadmin@example.com', 'testuser@example.com']:
            existing = User.query.filter_by(email=email).first()
            if existing:
                db.session.delete(existing)
        
        # Create developer user
        dev_user = User(email='testdev@example.com', is_developer=True, is_admin=True, is_active=True)
        dev_user.set_password('password123')
        db.session.add(dev_user)
        
        # Create admin user  
        admin_user = User(email='testadmin@example.com', is_admin=True, is_active=True)
        admin_user.set_password('password123')
        db.session.add(admin_user)
        
        # Create regular user
        regular_user = User(email='testuser@example.com', is_active=True)
        regular_user.set_password('password123')
        db.session.add(regular_user)
        
        db.session.commit()
        
        # Verify the test users
        print("\nTest users created:")
        test_users = [dev_user, admin_user, regular_user]
        for user in test_users:
            print(f"  - {user.email}: {user.role}")
        
        print("\n✅ All tests completed successfully!")
        
        # Clean up test users
        for user in test_users:
            db.session.delete(user)
        db.session.commit()
        print("✅ Test users cleaned up.")

if __name__ == "__main__":
    test_developer_functionality() 