"""
Service for cleaning up expired password reset tokens from the database.

This service provides functionality to remove expired and used tokens
to keep the database clean and prevent unnecessary storage growth.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.password_reset_token import PasswordResetToken

logger = logging.getLogger(__name__)


class TokenCleanupService:
    """
    Service for managing cleanup of password reset tokens.
    
    Provides methods to remove expired tokens from the database,
    helping to maintain database performance and storage efficiency.
    """
    
    @classmethod
    def cleanup_expired_tokens(
        cls,
        db: Session,
        older_than_hours: Optional[int] = None
    ) -> int:
        """
        Remove expired password reset tokens from the database.
        
        Args:
            db: Database session
            older_than_hours: Optional. Only delete tokens older than this many hours.
                            If None, deletes all expired tokens (default).
        
        Returns:
            Number of tokens deleted
        """
        try:
            # Calculate cutoff time
            if older_than_hours is not None:
                cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
                # Delete tokens that are expired AND older than cutoff
                query = db.query(PasswordResetToken).filter(
                    and_(
                        PasswordResetToken.expires_at < datetime.utcnow(),
                        PasswordResetToken.created_at < cutoff_time
                    )
                )
            else:
                # Delete all expired tokens
                query = db.query(PasswordResetToken).filter(
                    PasswordResetToken.expires_at < datetime.utcnow()
                )
            
            # Count before deletion for logging
            count = query.count()
            
            if count > 0:
                # Delete expired tokens
                query.delete(synchronize_session=False)
                db.commit()
                
                logger.info(
                    f"Cleaned up {count} expired password reset tokens",
                    extra={"tokens_deleted": count}
                )
            else:
                logger.debug("No expired password reset tokens to clean up")
            
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(
                f"Error cleaning up expired tokens: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    @classmethod
    def cleanup_old_used_tokens(
        cls,
        db: Session,
        older_than_days: int = 7
    ) -> int:
        """
        Remove old used tokens from the database.
        
        Even if tokens haven't expired yet, we can clean up tokens
        that were used a long time ago (e.g., 7 days).
        
        Args:
            db: Database session
            older_than_days: Delete tokens used more than this many days ago (default: 7)
        
        Returns:
            Number of tokens deleted
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=older_than_days)
            
            query = db.query(PasswordResetToken).filter(
                PasswordResetToken.used_at < cutoff_time
            )
            
            count = query.count()
            
            if count > 0:
                query.delete(synchronize_session=False)
                db.commit()
                
                logger.info(
                    f"Cleaned up {count} old used password reset tokens (older than {older_than_days} days)",
                    extra={"tokens_deleted": count, "older_than_days": older_than_days}
                )
            else:
                logger.debug(f"No old used tokens to clean up (older than {older_than_days} days)")
            
            return count
            
        except Exception as e:
            db.rollback()
            logger.error(
                f"Error cleaning up old used tokens: {str(e)}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
    
    @classmethod
    def cleanup_all_expired_and_old(
        cls,
        db: Session,
        old_used_days: int = 7
    ) -> dict:
        """
        Perform comprehensive cleanup of expired and old tokens.
        
        Args:
            db: Database session
            old_used_days: Delete used tokens older than this many days (default: 7)
        
        Returns:
            Dictionary with cleanup statistics
        """
        expired_count = cls.cleanup_expired_tokens(db)
        old_used_count = cls.cleanup_old_used_tokens(db, older_than_days=old_used_days)
        
        return {
            "expired_tokens_deleted": expired_count,
            "old_used_tokens_deleted": old_used_count,
            "total_deleted": expired_count + old_used_count
        }


# Create a singleton instance
token_cleanup_service = TokenCleanupService()
