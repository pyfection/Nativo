from sqlalchemy import Column, String, DateTime, Table, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


# Association table for many-to-many relationship between Word and Tag
word_tags = Table(
    'word_tags',
    Base.metadata,
    Column('word_id', UUID(as_uuid=True), ForeignKey('words.id'), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow, nullable=False)
)


class Tag(Base):
    """Tags for categorizing words (e.g., 'nature', 'family', 'ceremonial')"""
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    words = relationship("Word", secondary=word_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name='{self.name}')>"

