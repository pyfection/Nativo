from sqlalchemy import Column, String, Text as TextType, DateTime, ForeignKey, Boolean, Enum as SQLEnum
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


class Text(Base):
    """
    Text model for storing content in different languages.
    
    A Text contains the actual content and belongs to a Document.
    Multiple Texts can belong to the same Document (for translations).
    
    Can be:
    - Full texts (stories, historical records, books)
    - Small snippets (definitions, etymology, cultural notes)
    - Everything in between
    
    Words in the content can be linked to Word records via word_texts.
    """
    __tablename__ = "texts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    title = Column(String(500), nullable=False)
    content = Column(TextType, nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    
    # Language of the content itself
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=True, index=True)
    
    # Link to parent Document (nullable for migration purposes)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)
    
    # Flag to mark primary/original text
    is_primary = Column(Boolean, default=False, nullable=False)
    
    source = Column(String(500), nullable=True)  # Origin/citation
    notes = Column(TextType, nullable=True)  # Internal notes
    
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="texts")
    document = relationship("Document", back_populates="texts")
    created_by = relationship("User")
    # Words linked in this text's content
    linked_words = relationship("Word", secondary="word_texts", back_populates="texts", viewonly=True)
    
    def __repr__(self):
        return f"<Text(id={self.id}, title='{self.title}', type={self.document_type}, language_id={self.language_id})>"

