"""
Document schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.document import DocumentType


class DocumentBase(BaseModel):
    """Base schema for Document"""
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    language_id: Optional[UUID] = None  # Language of the content
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    pass


class DocumentUpdate(BaseModel):
    """Schema for updating a document"""
    content: Optional[str] = Field(None, min_length=1)
    document_type: Optional[DocumentType] = None
    language_id: Optional[UUID] = None
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


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


class DocumentListItem(BaseModel):
    """Simplified schema for document lists"""
    id: UUID
    content: str = Field(..., max_length=200)  # Truncated content for lists
    document_type: DocumentType
    language_id: Optional[UUID] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DocumentFilter(BaseModel):
    """Schema for filtering and searching documents"""
    document_type: Optional[DocumentType] = None
    language_id: Optional[UUID] = None
    search_term: Optional[str] = None  # Search in content
    created_by_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class DocumentStatistics(BaseModel):
    """Statistics about documents in the database"""
    total_documents: int
    documents_by_type: dict[str, int]
    documents_by_language: dict[str, int]
    documents_with_linked_words: int

