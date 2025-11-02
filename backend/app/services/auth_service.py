"""
Authentication service for JWT token management and user operations.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from fastapi import HTTPException, status

from app.config import settings
from app.models.user import User, UserRole


def create_access_token(user_id: UUID, role: UserRole) -> str:
    """
    Create a JWT access token for a user.
    
    Args:
        user_id: User's UUID
        role: User's role
        
    Returns:
        Encoded JWT token
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": str(user_id),
        "role": role.value,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def check_resource_owner(user: User, resource_owner_id: UUID) -> bool:
    """
    Check if a user owns a resource or is an admin.
    
    Args:
        user: Current user
        resource_owner_id: ID of the resource owner
        
    Returns:
        True if user owns the resource or is an admin
    """
    return user.id == resource_owner_id or user.role == UserRole.ADMIN


def require_resource_owner(user: User, resource_owner_id: UUID) -> None:
    """
    Require that a user owns a resource or is an admin.
    
    Args:
        user: Current user
        resource_owner_id: ID of the resource owner
        
    Raises:
        HTTPException: If user doesn't own the resource and is not an admin
    """
    if not check_resource_owner(user, resource_owner_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own resources"
        )

