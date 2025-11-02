# Authentication and Authorization Guide

## Overview

The Nativo platform implements a role-based authentication system using JWT tokens. This guide explains how to use the authentication system.

## User Roles

Four user roles are available, each with different permissions:

1. **PUBLIC** (default) - Can view published content
2. **RESEARCHER** - Can create and edit documents
3. **NATIVE_SPEAKER** - Can create, verify words and pronunciation
4. **ADMIN** - Full system access

## API Endpoints

### Register a New User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "password": "securepassword123",
  "role": "public"  # Optional, defaults to "public"
}
```

**Note:** Only ADMIN users can create accounts with roles other than PUBLIC.

### Login

```bash
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepassword123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Get Current User Info

```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

### List All Users (Admin Only)

```bash
GET /api/v1/auth/users
Authorization: Bearer <access_token>
```

## Using Authentication in Code

### Protecting Endpoints

```python
from fastapi import APIRouter, Depends
from app.models.user import User
from app.api.deps import (
    get_current_active_user,
    require_admin,
    require_native_speaker,
    require_researcher,
    require_contributor,
    require_role
)
from app.models.user import UserRole

router = APIRouter()

# Require authentication (any role)
@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_active_user)
):
    return {"message": f"Hello {current_user.username}"}

# Require admin role
@router.delete("/resource/{id}")
async def delete_resource(
    id: int,
    current_user: User = Depends(require_admin)
):
    # Only admins can access this
    return {"message": "Deleted"}

# Require native speaker or admin
@router.post("/words/verify")
async def verify_word(
    current_user: User = Depends(require_native_speaker)
):
    # Native speakers and admins can verify
    return {"message": "Verified"}

# Require any contributor role
@router.post("/words")
async def create_word(
    current_user: User = Depends(require_contributor)
):
    # Researchers, Native Speakers, and Admins can create
    return {"message": "Created"}

# Custom role combination
@router.post("/special")
async def special_action(
    current_user: User = Depends(
        require_role(UserRole.ADMIN, UserRole.RESEARCHER)
    )
):
    # Only admins and researchers
    return {"message": "Special action"}
```

### Checking Resource Ownership

```python
from app.services.auth_service import require_resource_owner

@router.put("/words/{word_id}")
async def update_word(
    word_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db)
):
    word = db.query(Word).filter(Word.id == word_id).first()
    
    # Only allow if user owns the resource or is admin
    require_resource_owner(current_user, word.created_by_id)
    
    # Update the word
    return word
```

## Role Permissions Matrix

| Action | PUBLIC | RESEARCHER | NATIVE_SPEAKER | ADMIN |
|--------|--------|------------|----------------|-------|
| View published content | ✓ | ✓ | ✓ | ✓ |
| Create documents | - | ✓ | - | ✓ |
| Edit own documents | - | ✓ | - | ✓ |
| Create words | - | ✓ | ✓ | ✓ |
| Edit own words | - | ✓ | ✓ | ✓ |
| Verify words | - | - | ✓ | ✓ |
| Delete any content | - | - | - | ✓ |
| Manage users | - | - | - | ✓ |
| Edit others' content | - | - | - | ✓ |

## Security Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
SECRET_KEY=your-super-secret-key-min-32-chars-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
DATABASE_URL=sqlite:///./nativo.db
DEBUG=False
```

**Important:** Change the `SECRET_KEY` in production!

### Generate a Secure Secret Key

```python
import secrets
print(secrets.token_urlsafe(32))
```

## Example: Complete Authentication Flow

### 1. Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "researcher@example.com",
    "username": "researcher1",
    "password": "SecurePass123!"
  }'
```

### 2. Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=researcher@example.com&password=SecurePass123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
  "token_type": "bearer"
}
```

### 3. Access Protected Resource

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Create a Word (Protected)

```bash
curl -X POST http://localhost:8000/api/v1/words \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "word": "wəlapəmkanni",
    "language_id": "uuid-here",
    "romanization": "welapemkanni",
    "part_of_speech": "noun"
  }'
```

## Testing with FastAPI Docs

1. Start the server: `uv run uvicorn app.main:app --reload`
2. Open http://localhost:8000/docs
3. Click "Authorize" button (top right)
4. Login to get a token
5. Enter the token in the format: `Bearer <your_token>`
6. Test protected endpoints

## Error Responses

### 401 Unauthorized
Token is missing, invalid, or expired:
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
User lacks required permissions:
```json
{
  "detail": "Insufficient permissions. Required roles: ['admin']"
}
```

### 403 Forbidden (Ownership)
User doesn't own the resource:
```json
{
  "detail": "You can only modify your own resources"
}
```

## Best Practices

1. **Always use HTTPS in production** - JWT tokens should never be sent over plain HTTP
2. **Keep tokens secure** - Store in httpOnly cookies or secure storage, never in localStorage
3. **Set appropriate token expiry** - Balance security with user experience (default: 30 minutes)
4. **Validate on both frontend and backend** - Don't trust client-side validation alone
5. **Use strong passwords** - Enforce minimum 8 characters with complexity requirements
6. **Rotate secret keys** - Change SECRET_KEY periodically in production
7. **Log authentication attempts** - Monitor for suspicious activity

## Token Payload

The JWT token contains:
```json
{
  "sub": "user-uuid",
  "role": "researcher",
  "exp": 1234567890
}
```

- `sub`: User ID (UUID)
- `role`: User's role
- `exp`: Expiration timestamp

## Next Steps

- Implement token refresh endpoint
- Add password reset functionality
- Implement rate limiting
- Add OAuth/social login
- Set up email verification
- Add two-factor authentication (2FA)

