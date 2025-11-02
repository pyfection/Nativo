"""
Image model for visual references.
"""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Image(Base):
    """Images for visual references to words"""
    __tablename__ = "images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_path = Column(String(500), nullable=False)
    alt_text = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    
    uploaded_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    uploaded_by = relationship("User")
    
    def __repr__(self):
        return f"<Image(id={self.id}, file_path='{self.file_path}')>"

