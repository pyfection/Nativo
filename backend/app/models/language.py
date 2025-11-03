from sqlalchemy import Column, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Language(Base):
    """Language model for endangered languages being preserved"""
    __tablename__ = "languages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True, index=True)
    native_name = Column(String(255), nullable=True)
    iso_639_3 = Column(String(3), nullable=True, unique=True, index=True)  # ISO 639-3 language code
    description = Column(Text, nullable=True)
    is_endangered = Column(Boolean, default=True)
    managed = Column(Boolean, default=False)  # True if language is managed by Nativo
    
    # Theme colors for UI customization
    primary_color = Column(String(7), nullable=True)      # e.g., '#8B4513'
    secondary_color = Column(String(7), nullable=True)    # e.g., '#D2691E'
    accent_color = Column(String(7), nullable=True)       # e.g., '#CD853F'
    background_color = Column(String(7), nullable=True)   # e.g., '#FFF8DC'
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    words = relationship("Word", back_populates="language")
    documents = relationship("Document", back_populates="language")
    user_proficiencies = relationship("UserLanguage", back_populates="language", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Language(id={self.id}, name='{self.name}')>"

