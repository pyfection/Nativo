"""
Language schemas for API request/response validation.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class LanguageBase(BaseModel):
    """Base language schema"""
    name: str = Field(..., min_length=1, max_length=255)
    native_name: Optional[str] = Field(None, max_length=255)
    iso_639_3: Optional[str] = Field(None, min_length=3, max_length=3, description="ISO 639-3 language code")
    description: Optional[str] = None
    is_endangered: bool = True
    managed: bool = False
    
    # Theme colors for UI customization
    primary_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')


class LanguageCreate(LanguageBase):
    """Schema for creating a new language"""
    pass


class LanguageUpdate(BaseModel):
    """Schema for updating a language"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    native_name: Optional[str] = Field(None, max_length=255)
    iso_639_3: Optional[str] = Field(None, min_length=3, max_length=3)
    description: Optional[str] = None
    is_endangered: Optional[bool] = None
    managed: Optional[bool] = None
    
    # Theme colors
    primary_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    secondary_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    accent_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')
    background_color: Optional[str] = Field(None, min_length=7, max_length=7, pattern=r'^#[0-9A-Fa-f]{6}$')


class LanguageInDB(LanguageBase):
    """Schema for language as stored in database"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Language(LanguageInDB):
    """Complete language schema"""
    pass


class LanguageListItem(BaseModel):
    """Simplified schema for language lists"""
    id: UUID
    name: str
    native_name: Optional[str] = None
    iso_639_3: Optional[str] = None
    is_endangered: bool
    managed: bool
    
    model_config = ConfigDict(from_attributes=True)

