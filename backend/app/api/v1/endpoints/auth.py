"""
Authentication endpoints for user registration and login.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.user_language import UserLanguage
from app.schemas.user import (
    UserCreate, 
    UserResponse, 
    UserLogin, 
    Token,
    PasswordResetRequest,
    PasswordReset,
    PasswordResetResponse
)
from app.config import settings
from app.services.auth_service import create_access_token
from app.services.email_service import email_service
from app.services.password_reset_service import password_reset_service
from app.utils.security import hash_password, verify_password
from app.api.deps import get_current_active_user, require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post(
    "/password-reset-request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="""
    Request a password reset token to be sent via email.
    
    This endpoint allows users to request a password reset by providing their email address.
    If the email exists in the system, a password reset token will be generated and sent
    to the user's email address. The token can then be used with the `/password-reset` endpoint
    to set a new password.
    
    **Security Note:** This endpoint always returns a success message, even if the email
    doesn't exist in the system, to prevent email enumeration attacks.
    
    **Example Request:**
    ```json
    {
        "email": "user@example.com"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "message": "Password reset email sent successfully"
    }
    ```
    """,
    operation_id="request_password_reset",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Password reset email sent successfully (or email doesn't exist)",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password reset email sent successfully"
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Response message indicating the result of the password reset operation",
                                "example": "Password reset email sent successfully"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        },
        422: {
            "description": "Validation error - invalid email format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "email"],
                                "msg": "value is not a valid email address",
                                "type": "value_error.email"
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def request_password_reset(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request a password reset token via email.
    
    Args:
        request: Password reset request containing the user's email address
        db: Database session
        
    Returns:
        PasswordResetResponse: Success message (always returns success for security)
        
    Raises:
        HTTPException: Never raises an error (always returns success to prevent email enumeration)
    """
    try:
        # Find user by email
        user = db.query(User).filter(User.email == request.email).first()
        
        # Always return success message to prevent email enumeration attacks
        # Only send email if user exists and is active
        if user and user.is_active:
            try:
                # Generate reset token
                reset_token = password_reset_service.generate_reset_token(user.id)
                
                # Build reset URL using frontend URL from settings
                reset_url = f"{settings.FRONTEND_URL}/password-reset?token={reset_token}"
                
                # Send email
                email_sent = await email_service.send_password_reset_email(
                    email=user.email,
                    reset_token=reset_token,
                    reset_url=reset_url
                )
                
                if email_sent:
                    logger.info(
                        f"Password reset email sent successfully to {user.email}",
                        extra={"user_id": str(user.id), "email": user.email}
                    )
                else:
                    # Email failed but don't expose this to user
                    logger.error(
                        f"Failed to send password reset email to {user.email}",
                        extra={"user_id": str(user.id), "email": user.email}
                    )
                    
            except Exception as e:
                # Log error but don't expose to user (security: prevent email enumeration)
                logger.error(
                    f"Error processing password reset request for {request.email}",
                    extra={"email": request.email, "error": str(e)},
                    exc_info=True
                )
        elif user and not user.is_active:
            # User exists but is inactive - log but don't expose
            logger.warning(
                f"Inactive user attempted password reset: {request.email}",
                extra={"email": request.email}
            )
        else:
            # User doesn't exist - log but don't expose (security)
            logger.info(
                f"Password reset requested for non-existent email: {request.email}",
                extra={"email": request.email}
            )
        
        # Always return success to prevent email enumeration
        return PasswordResetResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        # Catch any unexpected errors
        logger.error(
            f"Unexpected error in password reset request: {str(e)}",
            extra={"email": request.email, "error": str(e)},
            exc_info=True
        )
        # Still return success to prevent information leakage
        return PasswordResetResponse(
            message="If an account with that email exists, a password reset link has been sent."
        )


@router.post(
    "/password-reset",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="""
    Reset a user's password using a reset token received via email.
    
    This endpoint allows users to set a new password after they have received a password
    reset token via email. The token must be valid and not expired. After successful
    password reset, the token is invalidated and cannot be used again.
    
    **Security Requirements:**
    - The reset token must be valid and not expired
    - The new password must meet minimum security requirements (8+ characters)
    - The token is single-use and invalidated after successful reset
    
    **Example Request:**
    ```json
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiMTIzNDU2NzgtMTIzNC0xMjM0LTEyMzQtMTIzNDU2Nzg5MDEyIiwiZXhwIjoxNjAwMDAwMDAwfQ.example_signature",
        "new_password": "newSecurePassword123"
    }
    ```
    
    **Example Response:**
    ```json
    {
        "message": "Password has been reset successfully"
    }
    ```
    
    **Error Responses:**
    - `400 Bad Request`: Invalid or expired reset token
    - `400 Bad Request`: Password does not meet requirements
    """,
    operation_id="reset_password",
    tags=["Authentication"],
    responses={
        200: {
            "description": "Password reset successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Password has been reset successfully"
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Response message indicating successful password reset",
                                "example": "Password has been reset successfully"
                            }
                        },
                        "required": ["message"]
                    }
                }
            }
        },
        400: {
            "description": "Invalid or expired reset token, or password validation failed",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_token": {
                            "summary": "Invalid or expired token",
                            "value": {
                                "detail": "Invalid or expired reset token"
                            }
                        },
                        "expired_token": {
                            "summary": "Token has expired",
                            "value": {
                                "detail": "Reset token has expired"
                            }
                        },
                        "weak_password": {
                            "summary": "Password validation failed",
                            "value": {
                                "detail": "Password must be at least 8 characters long"
                            }
                        }
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "detail": {
                                "type": "string",
                                "description": "Error message describing what went wrong"
                            }
                        },
                        "required": ["detail"]
                    }
                }
            }
        },
        422: {
            "description": "Validation error - invalid request format",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["body", "new_password"],
                                "msg": "ensure this value has at least 8 characters",
                                "type": "value_error.any_str.min_length",
                                "ctx": {"limit_value": 8}
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def reset_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_db)
):
    """
    Reset a user's password using a reset token.
    
    Args:
        reset_data: Password reset data containing the token and new password
        db: Database session
        
    Returns:
        PasswordResetResponse: Success message
        
    Raises:
        HTTPException: If token is invalid, expired, or password validation fails
    """
    try:
        # Validate token and get user
        user = password_reset_service.validate_token_and_get_user(
            token=reset_data.token,
            db=db
        )
        
        # Validate password strength (already validated by schema, but double-check)
        if len(reset_data.new_password) < 8:
            logger.warning(
                f"Password reset attempted with weak password for user {user.id}",
                extra={"user_id": str(user.id)}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long"
            )
        
        # Update user's password
        try:
            # Hash the new password (with error handling)
            try:
                user.hashed_password = hash_password(reset_data.new_password)
            except ValueError as hash_error:
                logger.error(
                    f"Password hashing failed for user {user.id}",
                    extra={"user_id": str(user.id), "error": str(hash_error)},
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to process password. Please try again."
                ) from hash_error
            
            db.commit()
            db.refresh(user)
            
            # Mark token as used to prevent reuse
            try:
                password_reset_service.mark_token_as_used(
                    token=reset_data.token,
                    user_id=user.id,
                    db=db
                )
            except Exception as e:
                # Log error but don't fail the password reset if token tracking fails
                logger.warning(
                    f"Failed to mark token as used after password reset: {str(e)}",
                    extra={"user_id": str(user.id), "error": str(e)}
                )
            
            logger.info(
                f"Password reset successful for user {user.id}",
                extra={"user_id": str(user.id), "email": user.email}
            )
            
            return PasswordResetResponse(
                message="Password has been reset successfully. You can now log in with your new password."
            )
            
        except Exception as e:
            # Rollback database transaction
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(
                    f"Failed to rollback transaction: {str(rollback_error)}",
                    extra={"error": str(rollback_error)},
                    exc_info=True
                )
            
            # Check if it's a database connection error
            error_str = str(e).lower()
            if 'connection' in error_str or 'database' in error_str or 'timeout' in error_str:
                logger.error(
                    f"Database connection error during password reset for user {user.id}",
                    extra={"user_id": str(user.id), "error": str(e)},
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service is temporarily unavailable. Please try again in a few moments."
                ) from e
            else:
                logger.error(
                    f"Database error during password reset for user {user.id}",
                    extra={"user_id": str(user.id), "error": str(e)},
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while resetting your password. Please try again."
                ) from e
            
    except HTTPException:
        # Re-raise HTTP exceptions (these are already user-friendly)
        raise
    except Exception as e:
        # Catch any unexpected errors
        error_str = str(e).lower()
        if 'connection' in error_str or 'database' in error_str or 'timeout' in error_str:
            logger.error(
                f"Database connection error in password reset: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database service is temporarily unavailable. Please try again in a few moments."
            ) from e
        else:
            logger.error(
                f"Unexpected error in password reset: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred while processing your request. Please try again."
            ) from e


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

