from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.database import Base


class DocumentType(str, enum.Enum):
    """Types of documents/texts"""
    # Full documents
    STORY = "story"
    HISTORICAL_RECORD = "historical_record"
    BOOK = "book"
    ARTICLE = "article"
    TRANSCRIPTION = "transcription"
    
    # Text snippets
    DEFINITION = "definition"
    LITERAL_TRANSLATION = "literal_translation"
    CONTEXT_NOTE = "context_note"
    USAGE_EXAMPLE = "usage_example"
    ETYMOLOGY = "etymology"
    CULTURAL_SIGNIFICANCE = "cultural_significance"
    TRANSLATION = "translation"
    NOTE = "note"
    
    OTHER = "other"


class Document(Base):
    """
    Unified model for all text content - from full documents to small snippets.
    
    Can be:
    - Full texts (stories, historical records, books)
    - Small snippets (definitions, etymology, cultural notes)
    - Everything in between
    
    Words in the content can be linked to Word records via word_documents.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    content = Column(Text, nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    
    # Language of the content itself (optional - e.g., English definition of indigenous word)
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=True, index=True)
    
    source = Column(String(500), nullable=True)  # Origin/citation
    notes = Column(Text, nullable=True)  # Internal notes
    
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="documents")
    created_by = relationship("User")
    # Words linked in this document's content
    linked_words = relationship("Word", secondary="word_documents", back_populates="documents", viewonly=True)
    
    def __repr__(self):
        return f"<Document(id={self.id}, type={self.document_type}, content='{self.content[:50]}...')>"
