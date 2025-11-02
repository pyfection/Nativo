from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Document(Base):
    """Documents in endangered languages (texts, stories, historical records)"""
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=False, index=True)
    
    source = Column(String(500), nullable=True)  # Origin of the document
    notes = Column(Text, nullable=True)
    
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    language = relationship("Language", back_populates="documents")
    uploaded_by = relationship("User")
    word_associations = relationship("WordDocument", back_populates="document")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}')>"

