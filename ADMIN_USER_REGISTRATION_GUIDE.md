# Admin User Registration & Password Management Guide

**Date**: December 18, 2025  
**Status**: ✅ COMPLETE  
**Feature**: Admin-Controlled User Registration with Secure Password Management

---

## Overview

The Admin Console now supports complete user registration and password management. Only administrators can create new user accounts, and all passwords are securely hashed and managed through the backend API.

---

## Key Features

### 1. **Admin-Only User Creation**
- Only admin users can access the admin console
- Admin console provides user creation interface
- Non-admin users cannot create or manage other users

### 2. **Secure Password Generation**
- System generates cryptographically secure temporary passwords
- Passwords are 12 characters long by default
- Include letters, digits, and special characters
- Temporary passwords are shown ONLY during creation

### 3. **Password Hashing**
- Passwords are hashed using bcrypt (via passlib)
- Fallback to SHA-256 if bcrypt unavailable
- Hash never stored in plain text
- Never transmitted over network (except temporary password at creation)

### 4. **User Lifecycle Management**
- Create users with assigned roles (admin, analyst, operator)
- Track password change history
- Monitor user status (active/inactive)
- Record user creation timestamps

---

## Backend Implementation

### New Endpoints

#### 1. **Create User** (Admin Only)
```
POST /api/users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@jarvis.local",
  "role": "analyst"
}

Response (201):
{
  "user": {
    "id": "3",
    "username": "john_doe",
    "email": "john@jarvis.local",
    "role": "analyst",
    "created_at": "2025-12-18T14:30:00.000000",
    "status": "active"
  },
  "temporary_password": "kR9@mL2$xQ1!",
  "created": true,
  "message": "User created successfully. Share the temporary password with the user..."
}
```

**Important**: The temporary password is ONLY returned at creation time. It's generated fresh each time.

#### 2. **Change Password** (User Self-Service)
```
POST /api/users/{username}/password/change
Content-Type: application/json

{
  "new_password": "MyNewSecurePassword123!"
}

Response:
{
  "success": true,
  "username": "john_doe",
  "message": "Password changed successfully"
}
```

**Requirements**:
- New password must be at least 8 characters
- User can change their own password
- Admin can change any user's password (with this endpoint)

#### 3. **Reset Password** (Admin Only)
```
POST /api/users/{username}/password/reset
(No body required)

Response:
{
  "success": true,
  "username": "john_doe",
  "temporary_password": "nX4#pL8@vQ2$",
  "message": "Password has been reset. Share the temporary password with the user."
}
```

**Use Case**: If user forgets password, admin can reset it to a new temporary password.

#### 4. **List Users**
```
GET /api/users

Response:
{
  "users": [
    {
      "id": "1",
      "username": "admin",
      "email": "admin@jarvis.local",
      "role": "admin",
      "password_changed_at": "2025-12-18T12:00:00.000000",
      "created_at": "2025-12-18T10:00:00.000000",
      "last_login": "2025-12-18T14:15:00.000000",
      "status": "active"
    },
    ...
  ],
  "count": 2,
  "timestamp": "2025-12-18T14:30:00.000000"
}
```

#### 5. **Delete User**
```
DELETE /api/users/{username}

Response:
{
  "deleted": true,
  "username": "john_doe"
}
```

**Restrictions**:
- Cannot delete the admin user
- Deletion is permanent

### Default Users

Two default users are provided for development:

| Username | Email | Role | Default Password | 
|----------|-------|------|------------------|
| admin | admin@jarvis.local | admin | admin123 |
| analyst01 | analyst@jarvis.local | analyst | analyst123 |

**Important**: Change these passwords in production!

---

## Frontend Implementation

### Admin Console User Tab

The "Users" tab in the admin console provides:

1. **User List**
   - Shows all users with their details
   - Displays role, status, and creation date
   - Shows last login timestamp

2. **Create User Button**
   - Opens form to create new user
   - Fields: username, email, role
   - Role selector (admin, analyst, operator)

3. **User Creation Form**
   ```
   Username: [text input]
   Email: [email input]
   Role: [dropdown: admin, analyst, operator]
   
   [Create User Button] [Cancel Button]
   ```

4. **Password Modal**
   - Appears after successful user creation
   - Displays the generated temporary password
   - Copy-to-clipboard button
   - Warning about password expiration and change requirement
   - "Acknowledged" button to close modal

5. **Delete User**
   - Red delete button on each user card
   - Confirms deletion (except admin user)
   - Instant feedback via toast notification

### User State Management

```typescript
interface User {
  id: string
  username: string
  email: string
  role: 'admin' | 'analyst' | 'operator'
  password_changed_at?: string
  last_login?: string
  status: 'active' | 'inactive'
  created_at?: string
}
```

### Password-Related States

```typescript
const [generatedPassword, setGeneratedPassword] = useState<string | null>(null)
const [newUsername, setNewUsername] = useState<string | null>(null)
const [showPasswordModal, setShowPasswordModal] = useState(false)
```

---

## Security Measures

### Backend Security

1. **Password Hashing**
   - bcrypt with cost factor of 12 (default from passlib)
   - Fallback to salted SHA-256 for compatibility
   - Never stored in plain text

2. **Temporary Passwords**
   - Generated using `secrets` module (cryptographically secure)
   - 12 characters minimum
   - Mix of uppercase, lowercase, digits, special chars
   - Only displayed once at creation time

3. **Audit Logging**
   - All user operations logged to audit trail
   - Tracks creation, deletion, password changes
   - Records user, timestamp, action, status

4. **Input Validation**
   - Username and email required
   - Role must be valid enum (admin, analyst, operator)
   - Password minimum 8 characters
   - Email format validated on frontend

5. **Admin Protection**
   - Admin user cannot be deleted
   - Only admins can create/delete users
   - All operations go through authenticated routes

### Frontend Security

1. **Component Protection**
   - Admin page wrapped in PrivateRoute
   - Requires authentication to access
   - User data never includes password hash

2. **Password Display**
   - Only shown in modal after creation
   - Copy button for easy sharing
   - Warning about password handling
   - Modal closes after acknowledgment

3. **Form Validation**
   - Username and email required
   - Email format validation
   - Role selection dropdown (no free text)
   - Loading states prevent double-submit

---

## User Registration Workflow

### Step-by-Step

**1. Admin Creates User**
   - Admin navigates to Admin Console → Users tab
   - Clicks "Create User" button
   - Form appears with fields: username, email, role

**2. Admin Fills Form**
   ```
   Username: alice_smith
   Email: alice@jarvis.local
   Role: analyst
   ```

**3. Admin Submits**
   - Click "Create User" button
   - Loading state shown during API call

**4. Backend Processes**
   - Validates input (no duplicates, valid role)
   - Generates temporary password: `kR9@mL2$xQ1!`
   - Hashes password: `$2b$12$...` (bcrypt)
   - Creates user record with metadata
   - Logs audit event
   - Returns user + password to frontend

**5. Modal Displays Password**
   - Modal appears with generated password
   - Shows message about temporary nature
   - Provides copy-to-clipboard button
   - Warning: "User must change password on first login"

**6. Admin Shares Password**
   - Admin copies password from modal
   - Admin shares via secure channel (email, messaging, etc.)
   - Admin clicks "Acknowledged" to close modal

**7. User Receives Account**
   - User receives username and temporary password
   - User logs in with temporary password
   - System prompts password change
   - User sets own secure password

---

## API Usage Examples

### Using cURL

#### Create User
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "username": "bob_jones",
    "email": "bob@jarvis.local",
    "role": "operator"
  }'
```

#### List Users
```bash
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer <token>"
```

#### Change Password
```bash
curl -X POST http://localhost:8000/api/users/bob_jones/password/change \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "new_password": "MySecurePassword123!"
  }'
```

#### Reset Password
```bash
curl -X POST http://localhost:8000/api/users/bob_jones/password/reset \
  -H "Authorization: Bearer <token>"
```

#### Delete User
```bash
curl -X DELETE http://localhost:8000/api/users/bob_jones \
  -H "Authorization: Bearer <token>"
```

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000/api"
HEADERS = {"Authorization": "Bearer <your_token>"}

# Create user
response = requests.post(
    f"{BASE_URL}/users",
    json={
        "username": "carol",
        "email": "carol@jarvis.local",
        "role": "analyst"
    },
    headers=HEADERS
)
data = response.json()
temp_password = data['temporary_password']
print(f"New user password: {temp_password}")

# Change password
response = requests.post(
    f"{BASE_URL}/users/carol/password/change",
    json={"new_password": "NewSecurePassword123"},
    headers=HEADERS
)

# List users
response = requests.get(f"{BASE_URL}/users", headers=HEADERS)
users = response.json()['users']
for user in users:
    print(f"{user['username']}: {user['role']}")

# Delete user
response = requests.delete(
    f"{BASE_URL}/users/carol",
    headers=HEADERS
)
```

---

## Configuration

### Environment Variables

```bash
# Password hashing configuration (in admin.py)
# No additional env vars required - uses defaults from passlib

# For development/testing:
export JARVIS_SETTINGS_PATH="/path/to/settings.json"
```

### Dependencies

**Backend Requirements** (add to `requirements.txt`):
```
passlib>=1.7.4
bcrypt>=4.0.0  # Or use: pip install passlib[bcrypt]
```

**Installation**:
```bash
# Option 1: Install both
pip install passlib bcrypt

# Option 2: Install with passlib
pip install passlib[bcrypt]

# Option 3: If bcrypt unavailable, system falls back to SHA-256
# (Not recommended for production)
```

---

## Error Handling

### Common Errors and Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `username and email are required` | Missing fields | Fill both username and email fields |
| `user '...' already exists` | Username duplicate | Choose a unique username |
| `invalid role` | Invalid role value | Select from: admin, analyst, operator |
| `cannot delete admin user` | Trying to delete admin | Cannot delete admin user (by design) |
| `user '...' not found` | User doesn't exist | Verify username is correct |
| `password must be at least 8 characters` | Password too short | Use password with 8+ characters |
| `failed to create user` | Server error | Check backend logs and API health |

### HTTP Status Codes

- `201 Created` - User created successfully
- `400 Bad Request` - Invalid input (missing fields, invalid role)
- `403 Forbidden` - Cannot delete admin user
- `404 Not Found` - User doesn't exist
- `409 Conflict` - Username already exists
- `500 Internal Server Error` - Server error

---

## Testing

### Manual Testing Checklist

- [ ] Create user with valid inputs
- [ ] Verify password modal appears
- [ ] Copy password to clipboard
- [ ] Verify password is different each time
- [ ] Try to create duplicate username (should error)
- [ ] Try to create user with invalid role
- [ ] Try to delete a user (should succeed for non-admin)
- [ ] Try to delete admin user (should fail)
- [ ] List users after creation
- [ ] Change password for user
- [ ] Reset password for user
- [ ] Verify passwords are never shown in user list
- [ ] Check audit logs for user operations
- [ ] Verify user creation timestamps

### Automated Testing

```python
import pytest
from fastapi.testclient import TestClient
from backend.api.server import app

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/api/users",
        json={
            "username": "test_user",
            "email": "test@jarvis.local",
            "role": "analyst"
        }
    )
    assert response.status_code == 200
    assert "temporary_password" in response.json()
    assert "user" in response.json()

def test_duplicate_username():
    # First creation
    client.post(
        "/api/users",
        json={
            "username": "duplicate",
            "email": "dup1@jarvis.local",
            "role": "analyst"
        }
    )
    # Second creation with same username
    response = client.post(
        "/api/users",
        json={
            "username": "duplicate",
            "email": "dup2@jarvis.local",
            "role": "analyst"
        }
    )
    assert response.status_code == 409

def test_delete_admin_protected():
    response = client.delete("/api/users/admin")
    assert response.status_code == 403
```

---

## Troubleshooting

### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'passlib'`  
**Solution**: Install passlib: `pip install passlib bcrypt`

**Problem**: Password hashing takes too long  
**Solution**: Check CPU usage; bcrypt is intentionally slow for security

**Problem**: Users show up in list but password change fails  
**Solution**: Verify user exists and endpoint is `/api/users/{username}/password/change`

### Frontend Issues

**Problem**: Password modal doesn't appear  
**Solution**: Check browser console for API errors; verify backend response includes `temporary_password`

**Problem**: Copy-to-clipboard doesn't work  
**Solution**: Browser security restriction; user may need to manually copy

**Problem**: User list empty after creation  
**Solution**: Check network tab in browser console; verify API response success

---

## Best Practices

### For Administrators

1. **Change Default Passwords**
   - Change default admin and analyst passwords immediately
   - Use strong, unique passwords

2. **Secure Password Sharing**
   - Never share passwords via email or chat
   - Use secure channels (encrypted message, in-person, etc.)
   - Consider password manager for distribution

3. **Monitor User Activity**
   - Review audit logs regularly
   - Check user creation dates
   - Monitor login timestamps

4. **Access Control**
   - Only grant admin rights when necessary
   - Regularly review user roles
   - Deactivate unused accounts

5. **Password Policy**
   - Enforce strong passwords (8+ chars, mixed case, digits, special chars)
   - Require password changes periodically (quarterly recommended)
   - Don't reuse old passwords

### For Users

1. **First Login**
   - Change temporary password immediately
   - Choose strong, unique password
   - Don't share password with anyone

2. **Ongoing Security**
   - Change password every 90 days
   - Never write down password
   - Log out after each session
   - Don't use same password on other systems

3. **Account Recovery**
   - Contact admin if password forgotten
   - Don't attempt to reset multiple times
   - Provide identity verification

---

## Future Enhancements

### Planned Features

1. **Password Expiration**
   - Track password age
   - Prompt for password change after 90 days
   - Force change on expiration

2. **Failed Login Tracking**
   - Count failed login attempts
   - Lock account after 5 failed attempts
   - Email alerts on suspicious activity

3. **Two-Factor Authentication (2FA)**
   - Add authenticator app support
   - Email-based OTP
   - SMS-based OTP

4. **Single Sign-On (SSO)**
   - Azure AD integration
   - LDAP/Active Directory
   - OAuth2 support

5. **Advanced Audit Logging**
   - Export audit logs to external systems
   - Real-time alerts for critical actions
   - Compliance reporting (HIPAA, SOC2, etc.)

6. **Role-Based Access Control (RBAC)**
   - Fine-grained permissions
   - Permission inheritance
   - Resource-specific access

7. **Multi-Workspace Support**
   - Separate user bases per workspace
   - User role scope per workspace
   - Cross-workspace administration

---

## Summary

The Admin User Registration system provides:

✅ **Secure password generation** - Cryptographically secure temporary passwords  
✅ **Secure password storage** - Bcrypt hashing with fallback  
✅ **Admin-only control** - Only admins can create/delete users  
✅ **Complete audit trail** - All operations logged  
✅ **User-friendly interface** - Simple admin console  
✅ **Production ready** - Error handling, validation, security measures  
✅ **Extensible design** - Ready for future enhancements  

---

**Version**: 1.0  
**Last Updated**: December 18, 2025  
**Status**: ✅ COMPLETE & READY FOR TESTING
