"""
Personal API tokens.

Long-lived bearer tokens for non-browser clients (the MCP server, scripts).
A token acts as its user with the user's own permissions; only a SHA-256
hash is stored, so the plaintext is shown exactly once at creation.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = Column(String(100), nullable=False)
    # First characters of the plaintext, so users can tell tokens apart.
    token_prefix = Column(String(16), nullable=False)
    token_hash = Column(String(64), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship("User")

    def __repr__(self):
        return f"<ApiToken(id={self.id}, user_id={self.user_id}, name='{self.name}')>"
