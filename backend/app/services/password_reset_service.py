"""
Password reset token service for generating, validating, and managing reset tokens.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import UUID
from jose import JWTError, jwt, ExpiredSignatureError
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.utils.security import hash_token

logger = logging.getLogger(__name__)


class PasswordResetTokenError(Exception):
    """Base exception for password reset token errors"""
    pass


class InvalidTokenError(PasswordResetTokenError):
    """Raised when token is invalid or malformed"""
    pass


class ExpiredTokenError(PasswordResetTokenError):
    """Raised when token has expired"""
    pass


class PasswordResetService:
    """
    Service for managing password reset tokens.
    
    Uses JWT tokens with expiration for secure password reset functionality.
    """
    
    # Token expiration time (default: 1 hour)
    TOKEN_EXPIRE_MINUTES = 60
    
    @classmethod
    def generate_reset_token(cls, user_id: UUID) -> str:
        """
        Generate a password reset token for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Encoded JWT token for password reset
        """
        expire = datetime.utcnow() + timedelta(minutes=cls.TOKEN_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": str(user_id),
            "type": "password_reset",
            "exp": expire.timestamp(),
            "iat": datetime.utcnow().timestamp()
        }
        
        try:
            encoded_token = jwt.encode(
                to_encode,
                settings.SECRET_KEY,
                algorithm=settings.ALGORITHM
            )
            logger.info(
                f"Generated password reset token for user {user_id}",
                extra={"user_id": str(user_id)}
            )
            return encoded_token
        except Exception as e:
            logger.error(
                f"Failed to generate reset token for user {user_id}",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate reset token. Please try again."
            ) from e
    
    @classmethod
    def decode_reset_token(cls, token: str) -> Dict[str, any]:
        """
        Decode and validate a password reset token.
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload containing user_id
            
        Raises:
            InvalidTokenError: If token is invalid or malformed
            ExpiredTokenError: If token has expired
        """
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            
            # Verify token type
            if payload.get("type") != "password_reset":
                logger.warning(
                    "Invalid token type for password reset",
                    extra={"token_type": payload.get("type")}
                )
                raise InvalidTokenError("Invalid token type")
            
            # Verify user ID exists
            user_id_str = payload.get("sub")
            if not user_id_str:
                logger.warning("Token missing user ID")
                raise InvalidTokenError("Token missing user identification")
            
            return payload
            
        except ExpiredSignatureError:
            logger.info("Password reset token expired")
            raise ExpiredTokenError("Reset token has expired")
        except JWTError as e:
            logger.warning(
                f"Invalid password reset token: {str(e)}",
                extra={"error": str(e)}
            )
            raise InvalidTokenError("Invalid reset token") from e
        except Exception as e:
            logger.error(
                f"Unexpected error decoding reset token: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise InvalidTokenError("Invalid reset token") from e
    
    @classmethod
    def validate_token_and_get_user(
        cls,
        token: str,
        db: Session
    ) -> User:
        """
        Validate a reset token and return the associated user.
        
        Also checks if the token has already been used.
        
        Args:
            token: Password reset token
            db: Database session
            
        Returns:
            User associated with the token
            
        Raises:
            HTTPException: If token is invalid, expired, already used, or user not found
        """
        try:
            # Decode token
            payload = cls.decode_reset_token(token)
            user_id_str = payload.get("sub")
            exp_timestamp = payload.get("exp")
            
            if not user_id_str:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            # Convert to UUID
            try:
                user_id = UUID(user_id_str)
            except ValueError:
                logger.warning(f"Invalid user ID format in token: {user_id_str}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            # Check if token has already been used
            token_hash = hash_token(token)
            used_token = db.query(PasswordResetToken).filter(
                PasswordResetToken.token_hash == token_hash
            ).first()
            
            if used_token:
                logger.warning(
                    f"Attempted reuse of password reset token for user {user_id}",
                    extra={"user_id": str(user_id)}
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This reset token has already been used. Please request a new password reset."
                )
            
            # Find user
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                logger.warning(f"User not found for reset token: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Inactive user attempted password reset: {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Account is inactive. Please contact support."
                )
            
            return user
            
        except ExpiredTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new password reset."
            )
        except InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid reset token. Please check your email and try again."
            )
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Check if it's a database connection error
            error_str = str(e).lower()
            if 'connection' in error_str or 'database' in error_str or 'timeout' in error_str:
                logger.error(
                    f"Database connection error validating reset token: {str(e)}",
                    extra={"error": str(e)},
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Database service is temporarily unavailable. Please try again in a few moments."
                ) from e
            else:
                logger.error(
                    f"Unexpected error validating reset token: {str(e)}",
                    extra={"error": str(e)},
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred while processing your request. Please try again."
                ) from e
    
    @classmethod
    def mark_token_as_used(
        cls,
        token: str,
        user_id: UUID,
        db: Session
    ) -> None:
        """
        Mark a password reset token as used in the database.
        
        This prevents token reuse and allows cleanup of old tokens.
        
        Args:
            token: The password reset token that was used
            user_id: UUID of the user who used the token
            db: Database session
        """
        try:
            # Decode token to get expiration time
            payload = cls.decode_reset_token(token)
            exp_timestamp = payload.get("exp")
            
            # Convert expiration timestamp to datetime
            expires_at = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else datetime.utcnow()
            
            # Create token record
            token_hash = hash_token(token)
            used_token = PasswordResetToken(
                token_hash=token_hash,
                user_id=user_id,
                expires_at=expires_at,
                used_at=datetime.utcnow()
            )
            
            db.add(used_token)
            db.commit()
            
            logger.info(
                f"Marked password reset token as used for user {user_id}",
                extra={"user_id": str(user_id)}
            )
            
        except Exception as e:
            db.rollback()
            # Log error but don't fail the password reset if token tracking fails
            logger.error(
                f"Failed to mark token as used: {str(e)}",
                extra={"user_id": str(user_id), "error": str(e)},
                exc_info=True
            )


# Create a singleton instance
password_reset_service = PasswordResetService()
