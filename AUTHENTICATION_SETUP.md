# Authentication System Setup Guide

## Overview
ITU Intern now includes a comprehensive authentication system with role-based access control:

- **Regular Users**: Can sign up only if their email is in the allowed users list
- **Admins**: Have all regular user access plus admin dashboard and user management

## Setup Instructions

### 1. Install Dependencies
```bash
pip install Flask-Login==0.6.3 email-validator==2.2.0
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run Database Migration
```bash
flask db upgrade
```

### 3. Create First Admin User
```bash
python create_admin.py admin@example.com
# You'll be prompted to enter a password securely
```

Or with password inline (less secure):
```bash
python create_admin.py admin@example.com your_password_here
```

### 4. Start Application
```bash
python run.py
```

The application will be available at: http://localhost:8000

## User Management

### Admin Dashboard
- Access at `/admin` (admin users only)
- View statistics: total users, allowed users, unused invites, total meetings
- Recent users and meetings activity

### User Management
- Access at `/admin/users` (admin users only)
- Add single users or bulk add multiple users
- Manage existing users (toggle admin status, activate/deactivate, delete)
- View allowed users list and remove pending invitations

### User Registration Flow
1. Admin adds user email to allowed list
2. User visits `/signup` and registers with allowed email
3. User can now log in and access the application
4. Admin sees the email marked as "used" in the allowed users list

## Quick Start (Demo Credentials)

### Admin Login
- **Email**: admin@example.com
- **Password**: adminpass123

### Test User Registration
- **Email**: user@example.com (already in allowed list)
- Create your own password during signup

## Features

### Authentication
- **Login/Logout**: Secure session management with Flask-Login
- **Password Security**: Werkzeug password hashing
- **Remember Me**: Optional persistent login
- **Email Validation**: Only allowed emails can register

### Authorization
- **Role-based Access**: Regular users vs Admins
- **Route Protection**: All main routes require login
- **Admin Protection**: Admin routes require admin role
- **Self-protection**: Admins cannot demote themselves if they're the only admin

### User Interface
- **Responsive Design**: Clean Bootstrap-based UI
- **Navbar Updates**: Shows user info and admin menu for admins
- **User Dropdown**: Easy access to logout
- **Form Validation**: Client and server-side validation

## Configuration

### Environment Variables
```bash
# Required for secure sessions
SECRET_KEY=your-secret-key-here-change-in-production

# Optional: First admin email for reference
ADMIN_EMAIL=admin@example.com
```

### Security Features
- CSRF protection on all forms
- Secure password hashing
- Session management
- Input validation and sanitization

## Usage Examples

### Adding Users as Admin
1. Log in as admin
2. Go to Admin → Manage Users
3. Use "Add Single User" or "Bulk Add Users"
4. Share signup link with users

### Managing Existing Users
1. Go to Admin → Manage Users
2. Use dropdown menu to select user and action
3. Toggle admin status, activate/deactivate, or delete

### User Registration
1. Admin must first add your email to allowed list
2. Visit `/signup`
3. Enter your email and create password
4. Log in at `/login`

## Database Schema

### User Table
- `id`: Primary key
- `email`: Unique email address
- `password_hash`: Hashed password
- `is_admin`: Admin role flag
- `is_active`: Account status
- `created_at`: Registration timestamp
- `last_login`: Last login timestamp

### AllowedUser Table
- `id`: Primary key
- `email`: Allowed email address
- `added_by_admin_id`: Which admin added this email
- `added_at`: When email was added
- `is_used`: Whether user has registered

### Meeting Updates
- `created_by_user_id`: Link to user who created the meeting

## Troubleshooting

### Common Issues

#### Email Validation Error
If you see "Install 'email_validator' for email validation support":
```bash
pip install email-validator==2.2.0
```

#### Other Issues
1. **Can't access admin pages**: Make sure user has `is_admin=True`
2. **Can't register**: Email must be in allowed users list first
3. **Migration errors**: Run `flask db stamp head` if partially applied

### Reset Admin User
```bash
python create_admin.py existing@admin.com
# Will promote existing user to admin
```

### Check Database Status
```bash
flask db current  # Shows current migration
flask db history  # Shows migration history
```

### Verify Installation
```bash
# Test if authentication system is working
python -c "
import requests
r = requests.get('http://localhost:8000', allow_redirects=False)
print('✅ Working!' if r.status_code == 302 else '❌ Error')
"
``` 