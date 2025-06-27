# Developer Role System

## Overview

The ITU-T application now includes a comprehensive three-tier role system:

1. **Users** - Basic access to meetings and processing
2. **Admins** - Can manage allowed users and basic user operations
3. **Developers** - Full system access with advanced user privilege management

## Role Hierarchy

- **Developer** (highest privilege)
  - All admin capabilities
  - Can create/delete admin users
  - Can promote/demote users between all roles
  - Can manage developer privileges
  - Access to advanced developer dashboard

- **Admin** (medium privilege)
  - Can manage allowed user emails
  - Can activate/deactivate users
  - Can toggle admin status (limited)
  - Access to admin dashboard

- **User** (basic privilege)
  - Can process meetings
  - Can view own meetings
  - Basic application access

## New Features

### Developer Dashboard (`/dev`)
- Advanced system statistics
- User role distribution overview
- Enhanced activity monitoring
- Quick access to privilege management

### Developer User Management (`/dev/users`)
- **Create Admin/Developer Users**: Direct user creation with role assignment
- **Privilege Management**: 
  - Make/Remove Admin
  - Make/Remove Developer
  - Toggle Active Status
  - Delete Users
- **Enhanced User Overview**: Shows roles, activity, and meeting counts

### Navigation Updates
- Dynamic navigation based on user role
- Developers see "Developer" menu with admin access
- Admins see standard "Admin" menu
- Users see basic navigation
- User dropdown shows current role badge

## API Endpoints

### Developer Routes
- `GET /dev` - Developer dashboard
- `GET /dev/users` - Developer user management
- `POST /dev/users/manage` - Manage user privileges
- `POST /dev/users/create-admin` - Create admin/developer users

### Updated Admin Routes
- Admin routes now accessible by both admins and developers
- Enhanced permission checking

## Database Changes

### User Model Updates
- Added `is_developer` boolean field
- Added role helper properties and methods:
  - `role` - Returns "Developer", "Admin", or "User"
  - `has_admin_access` - True for admins and developers
  - `has_developer_access` - True for developers only
  - `can_manage_users()` - Permission to manage user privileges
  - `can_manage_admins()` - Permission to manage admin privileges

## Security Features

### Permission Safeguards
- Developers cannot remove their own developer status if they're the only developer
- Users cannot delete their own accounts through the admin interface
- Role hierarchy prevents privilege escalation attacks
- Automatic admin promotion when granting developer privileges

### Access Control
- Route decorators enforce role requirements
- Template-level permission checks
- Form validation based on user capabilities

## Setup Instructions

### 1. Database Migration
The migration has been applied automatically. The `is_developer` column has been added to the user table.

### 2. Create Developer User
Use the provided script to create or promote users:

```bash
python create_developer.py
```

### 3. Access Developer Features
1. Log in as a developer user
2. Navigate to the "Developer" dropdown in the navbar
3. Access:
   - Developer Dashboard for system overview
   - User Management for privilege control
   - Admin Dashboard and Users for standard admin functions

## Usage Examples

### Creating a New Admin
1. Go to `/dev/users`
2. Use "Create Admin/Developer User" form
3. Enter email, password, and select privileges
4. Admin users get standard admin access
5. Developer users get full system access

### Managing User Privileges
1. Go to `/dev/users`
2. Use "Manage User Privileges" form
3. Select user and action:
   - Make Admin/Remove Admin
   - Make Developer/Remove Developer
   - Toggle Active Status
   - Delete User

### Promoting Existing Users
1. Select user from dropdown
2. Choose "Make Admin" or "Make Developer"
3. User gains new privileges immediately
4. Developers automatically become admins

## Role Badge System

Users now see their role in the navbar dropdown:
- 🟢 Developer (green badge)
- 🔵 Admin (blue badge)  
- ⚫ User (gray badge)

## Testing

Run the test script to verify functionality:

```bash
python test_developer_functionality.py
```

This creates test users with different roles and verifies all permission methods work correctly.

## Migration Notes

- Existing users with `is_admin=True` were automatically promoted to developers during migration
- All admin functionality remains unchanged
- New developer features are additive
- Backward compatibility maintained for existing admin workflows 