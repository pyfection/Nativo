"""
Document schemas for API request/response validation.

Documents now group together Text records in multiple languages.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.schemas.text import Text, TextListItem


class DocumentBase(BaseModel):
    """Base schema for Document (minimal fields)"""
    pass


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    pass


class DocumentInDB(DocumentBase):
    """Schema for document as stored in database"""
    id: UUID
    created_by_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Document(DocumentInDB):
    """Complete document schema"""
    pass


class DocumentWithTexts(DocumentInDB):
    """Document schema with all associated texts"""
    texts: List[Text] = []
    
    model_config = ConfigDict(from_attributes=True)


class DocumentListItem(BaseModel):
    """Simplified schema for document lists
    
    Shows the primary text's title and a preview.
    For the documents view, we'll show the text in the selected language.
    """
    id: UUID
    title: str  # From primary or selected language text
    content_preview: str = Field(..., max_length=200)  # Truncated content
    source: Optional[str] = None  # Source of the displayed text
    language_id: Optional[UUID] = None  # Language of the displayed text
    created_at: datetime
    text_count: int = 0  # Number of translations
    
    model_config = ConfigDict(from_attributes=True)


class DocumentFilter(BaseModel):
    """Schema for filtering and searching documents"""
    language_id: Optional[UUID] = None  # Filter by texts in this language
    search_term: Optional[str] = None  # Search in text titles/content
    created_by_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class DocumentStatistics(BaseModel):
    """Statistics about documents in the database"""
    total_documents: int
    documents_with_multiple_languages: int
    total_texts: int
    texts_by_language: dict[str, int]

