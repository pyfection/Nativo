"""
Authentication service for JWT token management and user operations.
"""
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from jose import JWTError, jwt
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User, UserRole
from app.models.user_language import UserLanguage

# One-time account-flow tokens (password reset, email verification). Signed
# and timestamped with itsdangerous — stateless, so no token table.
PASSWORD_RESET_MAX_AGE = 60 * 60  # 1 hour
EMAIL_VERIFY_MAX_AGE = 60 * 60 * 24 * 3  # 3 days


def _serializer(salt: str) -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SECRET_KEY, salt=salt)


def make_password_reset_token(user: User) -> str:
    """Reset token bound to the CURRENT password hash: changing the password
    (by reset or otherwise) invalidates every outstanding token."""
    return _serializer("password-reset").dumps(
        {"uid": str(user.id), "pw": user.hashed_password[-12:]}
    )


def verify_password_reset_token(db: Session, token: str) -> User | None:
    try:
        payload = _serializer("password-reset").loads(
            token, max_age=PASSWORD_RESET_MAX_AGE
        )
        user_id = UUID(payload["uid"])
    except (BadSignature, SignatureExpired, KeyError, ValueError):
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    if user.hashed_password[-12:] != payload.get("pw"):
        return None  # password changed since the token was issued
    return user


def make_email_verify_token(user: User) -> str:
    """Verification token bound to the address it was sent to."""
    return _serializer("email-verify").dumps(
        {"uid": str(user.id), "email": user.email}
    )


def verify_email_token(db: Session, token: str) -> User | None:
    try:
        payload = _serializer("email-verify").loads(token, max_age=EMAIL_VERIFY_MAX_AGE)
        user_id = UUID(payload["uid"])
    except (BadSignature, SignatureExpired, KeyError, ValueError):
        return None
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        return None
    if user.email != payload.get("email"):
        return None  # address changed since the token was issued
    return user


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

    # Platform admins / superusers can edit any language
    if user.is_superuser or user.role == UserRole.ADMIN:
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

    # Platform admins / superusers can verify any language
    if user.is_superuser or user.role == UserRole.ADMIN:
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

# ---------------------------------------------------------------------------
# Suggester tier: trust-based auto-promotion
# ---------------------------------------------------------------------------

# After this many of a user's suggestions have been approved (published by a
# reviewer) in a language, they are trusted with direct edit rights there.
AUTO_PROMOTE_AFTER_APPROVALS = 5


def maybe_promote_suggester(db: Session, user_id: UUID, language_id: UUID) -> bool:
    """
    Grant `can_edit` once a suggester has enough approved suggestions.

    Called after a reviewer publishes a suggested lexeme. Only promotes users
    who have joined the language (a UserLanguage row exists) — the membership
    row is where the permission lives. Returns True if a promotion happened.
    """
    from app.models.word import Lexeme, LexemeStatus  # avoid module cycle at import time

    if can_user_edit_language(db, user_id, language_id):
        return False

    # The caller (verify endpoint) has just set the lexeme to PUBLISHED in
    # the session; the app session is autoflush=False, so flush explicitly or
    # the count below misses the approval that triggered this call.
    db.flush()

    approved = (
        db.query(Lexeme)
        .filter(
            Lexeme.created_by_id == user_id,
            Lexeme.language_id == language_id,
            Lexeme.status == LexemeStatus.PUBLISHED,
            Lexeme.verified_by_id.isnot(None),
            Lexeme.verified_by_id != user_id,
        )
        .count()
    )
    if approved < AUTO_PROMOTE_AFTER_APPROVALS:
        return False

    user_language = db.query(UserLanguage).filter(
        and_(
            UserLanguage.user_id == user_id,
            UserLanguage.language_id == language_id,
        )
    ).first()
    if user_language is None:
        return False
    user_language.can_edit = True
    return True
