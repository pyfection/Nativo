from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Document(Base):
    """
    Document model representing a collection of Texts (potentially in multiple languages).
    
    A Document groups together Text records that represent the same content
    in different languages (translations). For example, a story might have
    a Document with multiple Text records - one in the indigenous language,
    one in English, one in Spanish, etc.
    
    Words can link to Documents for definitions, etymology, and cultural significance
    where the meaning is the same across translations.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    texts = relationship("Text", back_populates="document", cascade="all, delete-orphan")
    created_by = relationship("User")
    # Note: words_with_definition, words_with_etymology, and words_with_cultural_significance
    # are created automatically via backrefs defined in the Word model
    
    def __repr__(self):
        return f"<Document(id={self.id}, texts_count={len(self.texts) if self.texts else 0})>"
