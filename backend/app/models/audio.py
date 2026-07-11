from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Audio(Base):
    """Audio recordings for pronunciation and spoken content"""
    __tablename__ = "audio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    duration = Column(Integer, nullable=True)  # Duration in seconds
    mime_type = Column(String(100), nullable=True)

    # Narration: audio that reads a whole Text aloud attaches here (word
    # pronunciations attach via word_form_audio instead). Deleting the text
    # deletes its narrations with it.
    text_id = Column(
        UUID(as_uuid=True),
        ForeignKey("texts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    uploaded_by = relationship("User")
    text = relationship("Text")
    
    def __repr__(self):
        return f"<Audio(id={self.id}, file_path='{self.file_path}')>"

