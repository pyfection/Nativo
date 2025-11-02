"""
User-Language proficiency relationship model.
"""
from sqlalchemy import Column, ForeignKey, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class ProficiencyLevel(str, enum.Enum):
    """Language proficiency levels"""
    NATIVE = "native"
    FLUENT = "fluent"
    INTERMEDIATE = "intermediate"
    BEGINNER = "beginner"


class UserLanguage(Base):
    """
    Association table for User-Language relationships with proficiency and permissions.
    
    Tracks which languages a user knows and their proficiency level.
    Also stores permissions for editing and verifying content in that language.
    Permissions default to False and must be granted by admins.
    """
    __tablename__ = "user_languages"

    # Composite primary key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), primary_key=True)
    
    # Proficiency information
    proficiency_level = Column(SQLEnum(ProficiencyLevel), nullable=False)
    
    # Permissions (default to False, set by admins)
    can_edit = Column(Boolean, default=False, nullable=False)
    can_verify = Column(Boolean, default=False, nullable=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="language_proficiencies")
    language = relationship("Language", back_populates="user_proficiencies")
    
    def __repr__(self):
        return f"<UserLanguage(user_id={self.user_id}, language_id={self.language_id}, proficiency={self.proficiency_level})>"

