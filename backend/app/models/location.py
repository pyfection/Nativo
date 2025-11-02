from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from app.database import Base


class Location(Base):
    """
    Geographic location for tracking where words/pronunciations were confirmed.
    Useful for dialectal variations and regional language preservation.
    """
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Geographic coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Optional descriptive information
    name = Column(String(255), nullable=True)  # e.g., "Village of X", "Region Y"
    description = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<Location(id={self.id}, lat={self.latitude}, lon={self.longitude}, name='{self.name}')>"

