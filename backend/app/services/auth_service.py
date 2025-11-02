"""
Authentication service for JWT token management and user operations.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.config import settings
from app.models.user import User, UserRole
from app.models.user_language import UserLanguage


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


def can_user_edit_language(db: Session, user_id: UUID, language_id: UUID) -> bool:
    """
    Check if a user has permission to edit content for a specific language.
    Admins always have permission.
    
    Args:
        db: Database session
        user_id: User's UUID
        language_id: Language's UUID
        
    Returns:
        True if user can edit content in this language
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Admins can edit any language
    if user.role == UserRole.ADMIN:
        return True
    
    # Check user-language relationship
    user_language = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id
        )
    ).first()
    
    return user_language is not None and user_language.can_edit


def can_user_verify_language(db: Session, user_id: UUID, language_id: UUID) -> bool:
    """
    Check if a user has permission to verify content for a specific language.
    Admins always have permission.
    
    Args:
        db: Database session
        user_id: User's UUID
        language_id: Language's UUID
        
    Returns:
        True if user can verify content in this language
    """
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    
    # Admins can verify any language
    if user.role == UserRole.ADMIN:
        return True
    
    # Check user-language relationship
    user_language = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id
        )
    ).first()
    
    return user_language is not None and user_language.can_verify


def require_language_edit_permission(db: Session, user: User, language_id: UUID) -> None:
    """
    Require that a user has permission to edit content for a language.
    
    Args:
        db: Database session
        user: Current user
        language_id: Language's UUID
        
    Raises:
        HTTPException: If user lacks permission
    """
    if not can_user_edit_language(db, user.id, language_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to edit content for this language"
        )


def require_language_verify_permission(db: Session, user: User, language_id: UUID) -> None:
    """
    Require that a user has permission to verify content for a language.
    
    Args:
        db: Database session
        user: Current user
        language_id: Language's UUID
        
    Raises:
        HTTPException: If user lacks permission
    """
    if not can_user_verify_language(db, user.id, language_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to verify content for this language"
        )

