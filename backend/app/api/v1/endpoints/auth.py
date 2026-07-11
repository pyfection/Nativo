"""
Authentication endpoints for user registration, login and account recovery.
"""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.database import get_db
from app.limiter import limiter
from app.models.user import User, UserRole
from app.models.user_language import UserLanguage
from app.schemas.user import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
    VerifyEmailRequest,
)
from app.services.auth_service import (
    create_access_token,
    make_email_verify_token,
    make_password_reset_token,
    verify_email_token,
    verify_password_reset_token,
)
from app.utils.email import send_email
from app.utils.security import hash_password, verify_password
from app.api.deps import get_current_active_user, require_admin

router = APIRouter()


def _send_verification_email(user: User) -> None:
    """Best-effort: account flows must not fail on a mail hiccup."""
    token = make_email_verify_token(user)
    link = f"{settings.FRONTEND_URL.rstrip('/')}/verify-email?token={token}"
    send_email(
        to=user.email,
        subject="Confirm your email address — Nativo",
        body=(
            f"Servus {user.username},\n\n"
            "Please confirm your email address so we can reach you about "
            "your account and contributions:\n\n"
            f"{link}\n\n"
            "The link is valid for 3 days. If you didn't create a Nativo "
            "account, you can ignore this email.\n"
        ),
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - PUBLIC role only for public registration
    - For other roles, use admin endpoint to create users
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Public registration only allows PUBLIC role
    if user_data.role != UserRole.PUBLIC:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Public registration only allows PUBLIC role. Contact admin to create accounts with other roles."
        )
    
    # Create new user
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=UserRole.PUBLIC  # Force PUBLIC for public registration
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    try:
        _send_verification_email(new_user)
    except Exception:
        pass  # registration succeeded; verification can be re-requested

    return new_user


@router.post("/users/create", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_as_admin(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a user with any role (admin only).
    
    Allows admins to create users with any role including NATIVE_SPEAKER, RESEARCHER, or ADMIN.
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user with specified role
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
        role=user_data.role
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login with email/username and password to receive JWT token.
    
    Returns access token on successful authentication.
    """
    # Try to find user by email or username
    user = db.query(User).filter(
        (User.email == form_data.username) | (User.username == form_data.username)
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    # Create access token
    access_token = create_access_token(user.id, user.role)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/forgot-password")
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Request a password-reset email.

    Always answers the same way, whether or not the address has an account —
    this endpoint must not be usable to probe which emails are registered.
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if user and user.is_active:
        token = make_password_reset_token(user)
        link = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={token}"
        try:
            send_email(
                to=user.email,
                subject="Reset your password — Nativo",
                body=(
                    f"Servus {user.username},\n\n"
                    "Someone (hopefully you) asked to reset the password for "
                    "this Nativo account. Set a new one here:\n\n"
                    f"{link}\n\n"
                    "The link is valid for 1 hour. If you didn't ask for "
                    "this, you can ignore this email — your password is "
                    "unchanged.\n"
                ),
            )
        except Exception:
            pass
    return {"message": "If that address has an account, a reset link is on its way."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """Set a new password using an emailed reset token."""
    user = verify_password_reset_token(db, payload.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired. Request a new one.",
        )
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated. You can sign in with it now."}


@router.post("/request-verification")
@limiter.limit("5/minute")
async def request_verification(
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """(Re-)send the email-verification link to the signed-in user."""
    if current_user.email_verified_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This email address is already verified.",
        )
    _send_verification_email(current_user)
    return {"message": "Verification email sent."}


@router.post("/verify-email", response_model=UserResponse)
async def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
):
    """Confirm an email address from the emailed token (no login required —
    the link may be opened in a fresh browser)."""
    user = verify_email_token(db, payload.token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired. Request a new one.",
        )
    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)
    return user


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information.
    """
    # Reload user with language_proficiencies and language relationships loaded
    user = db.query(User).options(
        joinedload(User.language_proficiencies).joinedload(UserLanguage.language)
    ).filter(User.id == current_user.id).first()
    
    return user


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """
    List all users (admin only).
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

