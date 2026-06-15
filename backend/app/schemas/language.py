"""
Language schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LanguageBase(BaseModel):
    """Base language schema"""

    name: str = Field(..., min_length=1, max_length=255)
    native_name: str | None = Field(None, max_length=255)
    iso_639_3: str | None = Field(
        None, min_length=3, max_length=3, description="ISO 639-3 language code"
    )
    description: str | None = None
    is_endangered: bool = True
    managed: bool = False

    # Theme colors for UI customization
    primary_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    secondary_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    accent_color: str | None = Field(None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )

    # Optional FK to the Document the admin has promoted as this language's
    # canonical writing-standard reference.
    writing_standard_document_id: UUID | None = None


class LanguageCreate(LanguageBase):
    """Schema for creating a new language"""

    pass


class LanguageUpdate(BaseModel):
    """Schema for updating a language"""

    name: str | None = Field(None, min_length=1, max_length=255)
    native_name: str | None = Field(None, max_length=255)
    iso_639_3: str | None = Field(None, min_length=3, max_length=3)
    description: str | None = None
    is_endangered: bool | None = None
    managed: bool | None = None

    # Theme colors
    primary_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    secondary_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    accent_color: str | None = Field(None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$")
    background_color: str | None = Field(
        None, min_length=7, max_length=7, pattern=r"^#[0-9A-Fa-f]{6}$"
    )
    writing_standard_document_id: UUID | None = None


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
    native_name: str | None = None
    iso_639_3: str | None = None
    is_endangered: bool
    managed: bool

    model_config = ConfigDict(from_attributes=True)
