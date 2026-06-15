import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

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
    primary_color = Column(String(7), nullable=True)  # e.g., '#8B4513'
    secondary_color = Column(String(7), nullable=True)  # e.g., '#D2691E'
    accent_color = Column(String(7), nullable=True)  # e.g., '#CD853F'
    background_color = Column(String(7), nullable=True)  # e.g., '#FFF8DC'

    # The canonical writing-standard Document for this language. Nullable —
    # most languages won't have one yet. ON DELETE SET NULL so removing the
    # Document doesn't cascade-delete the Language; the FK just clears.
    writing_standard_document_id = Column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    lexemes = relationship("Lexeme", back_populates="language", cascade="all, delete-orphan")
    texts = relationship("Text", back_populates="language")
    user_proficiencies = relationship(
        "UserLanguage", back_populates="language", cascade="all, delete-orphan"
    )
    writing_standard_document = relationship(
        "Document",
        foreign_keys=[writing_standard_document_id],
    )

    def __repr__(self):
        return f"<Language(id={self.id}, name='{self.name}')>"
