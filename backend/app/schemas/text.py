"""
Text schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.text import DocumentType


class TextBase(BaseModel):
    """Base schema for Text"""
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    language_id: Optional[UUID] = None  # Language of the content
    document_id: Optional[UUID] = None  # Parent document
    is_primary: bool = False
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class TextCreate(TextBase):
    """Schema for creating a new text"""
    pass


class TextUpdate(BaseModel):
    """Schema for updating a text"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    document_type: Optional[DocumentType] = None
    language_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    is_primary: Optional[bool] = None
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class TextInDB(TextBase):
    """Schema for text as stored in database"""
    id: UUID
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Text(TextInDB):
    """Complete text schema"""
    pass


class TextListItem(BaseModel):
    """Simplified schema for text lists"""
    id: UUID
    title: str
    content: str = Field(..., max_length=200)  # Truncated content for lists
    document_type: DocumentType
    language_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    is_primary: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TextFilter(BaseModel):
    """Schema for filtering and searching texts"""
    document_type: Optional[DocumentType] = None
    language_id: Optional[UUID] = None
    document_id: Optional[UUID] = None
    is_primary: Optional[bool] = None
    search_term: Optional[str] = None  # Search in content or title
    created_by_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class TextStatistics(BaseModel):
    """Statistics about texts in the database"""
    total_texts: int
    texts_by_type: dict[str, int]
    texts_by_language: dict[str, int]
    texts_with_linked_words: int
    primary_texts: int

