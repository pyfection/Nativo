"""
Database model for tracking used password reset tokens.

This model stores tokens that have been used to reset passwords, allowing
us to prevent token reuse and clean up expired entries.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class PasswordResetToken(Base):
    """
    Model for tracking used password reset tokens.
    
    Stores tokens that have been used to reset passwords, along with
    their expiration timestamps for cleanup purposes.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Index for efficient cleanup queries
    __table_args__ = (
        Index('idx_token_expires_at', 'expires_at'),
    )
    
    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"
