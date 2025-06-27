# Navbar Role-Based Navigation System

## Overview

The ITU-T application features a robust role-based navigation system that dynamically adapts the navbar based on user privileges. This ensures that users only see navigation options they have permission to access, creating a clean and secure user experience.

## Role Hierarchy

The system implements a three-tier role hierarchy:

1. **Developer** (Highest Privilege)
   - Has all admin capabilities
   - Can manage user privileges and roles
   - Can create/delete admin and developer users
   - Access to advanced developer tools

2. **Admin** (Medium Privilege)
   - Can manage allowed user emails
   - Can activate/deactivate users
   - Can toggle basic admin status
   - Access to standard admin dashboard

3. **User** (Basic Privilege)
   - Can process meetings and view content
   - Basic application access only
   - No administrative capabilities

## Navbar Implementation

### Role-Based Display Logic

The navbar uses the following conditional logic:

```html
{% if current_user.has_developer_access %}
    <!-- Shows Developer dropdown with full access -->
{% elif current_user.has_admin_access and not current_user.has_developer_access %}
    <!-- Shows Admin dropdown with standard tools -->
{% endif %}
<!-- Regular users see no admin dropdown -->
```

### Developer Navigation (Developers Only)

Developers see a "Developer" dropdown with green "Dev" badge containing:

**Developer Tools Section:**
- Dev Dashboard - Advanced system statistics and monitoring
- User Management (Full) - Complete user privilege control

**Admin Access Section:**
- Admin Dashboard - Standard admin dashboard
- Admin Users (Basic) - Basic user management interface

### Admin Navigation (Admins Only)

Admins see an "Admin" dropdown with blue "Admin" badge containing:

**Admin Tools Section:**
- Dashboard - Standard admin dashboard
- Manage Users - Basic user management

### Regular User Navigation

Regular users see only the standard navigation:
- Home
- All Meetings  
- About

No admin or developer dropdowns are displayed.

## User Model Properties

The role system is built on these User model properties:

```python
@property
def role(self):
    """Get user role as string"""
    if self.is_developer:
        return 'Developer'
    elif self.is_admin:
        return 'Admin'
    else:
        return 'User'

@property
def has_admin_access(self):
    """Check if user has admin access (admin or developer)"""
    return self.is_admin or self.is_developer

@property
def has_developer_access(self):
    """Check if user has developer access"""
    return self.is_developer
```

## Security Features

### Route Protection

All admin and developer routes are protected with decorators:

```python
@admin_required    # Allows both admins and developers
@developer_required  # Allows only developers
```

### Access Control Matrix

| Feature | User | Admin | Developer |
|---------|------|-------|-----------|
| Process Meetings | ✅ | ✅ | ✅ |
| View All Meetings | ✅ | ✅ | ✅ |
| Admin Dashboard | ❌ | ✅ | ✅ |
| Manage Users | ❌ | ✅ (Basic) | ✅ (Full) |
| Create Admins | ❌ | ❌ | ✅ |
| System Statistics | ❌ | ❌ | ✅ |

### Permission Safeguards

- Developers cannot remove their own developer status if they're the only developer
- Users cannot delete their own accounts through admin interfaces
- Role hierarchy prevents privilege escalation
- Automatic admin promotion when granting developer privileges

## Template Context

The navbar has access to these template variables:

```python
# From context processor
'user_role': current_user.role,
'is_developer_user': current_user.has_developer_access,
'is_admin_user': current_user.has_admin_access,
'is_regular_user': not current_user.has_admin_access

# From current_user object
current_user.role
current_user.has_admin_access
current_user.has_developer_access
```

## Visual Design

### Role Badges

- Developer: Green "Dev" badge
- Admin: Blue "Admin" badge
- Organized sections with icons and descriptive headers
- Consistent styling with application design system

### Badge Styling

```css
.navbar .nav-link .badge {
    font-size: 0.625rem;
    font-weight: var(--font-weight-semibold);
    padding: 0.25rem 0.4rem;
    border-radius: var(--radius-sm);
    text-transform: uppercase;
    letter-spacing: 0.025em;
}
```

## Implementation Details

### Conditional Rendering

The navbar uses precise conditional logic to ensure proper display:

1. **Developer Check**: `current_user.has_developer_access`
2. **Admin-Only Check**: `current_user.has_admin_access and not current_user.has_developer_access`
3. **Regular User**: No admin dropdown displayed

### Database Schema

```sql
-- User table fields for role management
is_admin BOOLEAN DEFAULT FALSE
is_developer BOOLEAN DEFAULT FALSE
is_active BOOLEAN DEFAULT TRUE
```

### Role Assignment Rules

- `is_developer=True` automatically implies admin access
- Developers should typically have `is_admin=True` for consistency
- Regular users have both flags set to `False`
- Inactive users maintain their roles but cannot access the system

## Testing

The system includes comprehensive role testing:

```python
# Test different user types
developer_user = User(is_developer=True, is_admin=True)
admin_user = User(is_admin=True, is_developer=False)  
regular_user = User(is_admin=False, is_developer=False)

# Verify navbar logic
assert developer_user.has_developer_access == True
assert admin_user.has_admin_access == True
assert regular_user.has_admin_access == False
```

## Best Practices

### Role Assignment

1. **New Developers**: Set both `is_developer=True` and `is_admin=True`
2. **New Admins**: Set `is_admin=True` and `is_developer=False`
3. **Regular Users**: Keep both flags as `False`

### Template Usage

1. Use `current_user.has_developer_access` for developer-only features
2. Use `current_user.has_admin_access` for admin/developer features
3. Always check authentication with `current_user.is_authenticated`

### Route Protection

1. Use `@developer_required` for developer-only routes
2. Use `@admin_required` for admin/developer routes
3. Use `@login_required` for all authenticated routes

## Migration and Updates

### Adding New Roles

To add new roles, extend the User model:

1. Add new boolean field (e.g., `is_moderator`)
2. Update role property logic
3. Add new access control properties
4. Update navbar conditional logic
5. Create new route decorators

### Backwards Compatibility

The system maintains backwards compatibility:
- Existing admin users retain all functionality
- New developer features are additive
- No breaking changes to existing admin workflows

## Troubleshooting

### Common Issues

1. **User sees wrong dropdown**: Check `is_admin` and `is_developer` flags
2. **Access denied errors**: Verify route decorators match user privileges
3. **Missing navigation**: Ensure user is authenticated and active

### Debugging

```python
# Check user roles in console
user = User.query.get(user_id)
print(f"Role: {user.role}")
print(f"Admin Access: {user.has_admin_access}")
print(f"Developer Access: {user.has_developer_access}")
```

## Summary

The navbar role-based navigation system provides:

- **Security**: Users only see what they can access
- **Clarity**: Clean, role-appropriate interface
- **Flexibility**: Easy to extend with new roles
- **Consistency**: Unified design across all user types
- **Robustness**: Comprehensive access control and validation

This implementation ensures a professional, secure, and user-friendly navigation experience that scales with the application's permission system. 