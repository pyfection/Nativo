"""
Audio schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class AudioBase(BaseModel):
    """Base audio schema"""
    file_path: str = Field(..., max_length=500)
    file_size: Optional[int] = Field(None, ge=0, description="File size in bytes")
    duration: Optional[int] = Field(None, ge=0, description="Duration in seconds")
    mime_type: Optional[str] = Field(None, max_length=100)


class AudioCreate(AudioBase):
    """Schema for creating a new audio record"""
    pass


class AudioUpdate(BaseModel):
    """Schema for updating an audio record"""
    file_path: Optional[str] = Field(None, max_length=500)
    file_size: Optional[int] = Field(None, ge=0)
    duration: Optional[int] = Field(None, ge=0)
    mime_type: Optional[str] = Field(None, max_length=100)


class AudioInDB(AudioBase):
    """Schema for audio as stored in database"""
    id: UUID
    uploaded_by_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Audio(AudioInDB):
    """Complete audio schema"""
    pass


class AudioListItem(BaseModel):
    """Simplified schema for audio lists"""
    id: UUID
    file_path: str
    duration: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

