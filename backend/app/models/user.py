from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


class UserRole(str, enum.Enum):
    """User roles for access control"""
    ADMIN = "admin"
    NATIVE_SPEAKER = "native_speaker"
    RESEARCHER = "researcher"
    PUBLIC = "public"


class User(Base):
    """User model for authentication and tracking contributions"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.PUBLIC, nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    words_created = relationship("Word", foreign_keys="Word.created_by_id", back_populates="created_by")
    words_verified = relationship("Word", foreign_keys="Word.verified_by_id", back_populates="verified_by")
    language_proficiencies = relationship("UserLanguage", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"

