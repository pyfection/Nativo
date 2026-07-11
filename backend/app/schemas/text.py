"""
Text schemas for API request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.text import DocumentType, TextFormat
from app.models.text_word_link import TextWordLinkStatus


class TextBase(BaseModel):
    """Base schema for Text"""

    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=1)
    document_type: DocumentType
    format: TextFormat = TextFormat.PLAIN
    language_id: UUID | None = None  # Language of the content
    document_id: UUID | None = None  # Parent document
    is_primary: bool = False
    source: str | None = Field(None, max_length=500)
    notes: str | None = None
    # Editor pin for the guided learning path (null = computed placement).
    learning_order: int | None = None


class TextCreate(TextBase):
    """Schema for creating a new text"""

    pass


class TextUpdate(BaseModel):
    """Schema for updating a text"""

    title: str | None = Field(None, min_length=1, max_length=500)
    content: str | None = Field(None, min_length=1)
    document_type: DocumentType | None = None
    format: TextFormat | None = None
    language_id: UUID | None = None
    document_id: UUID | None = None
    is_primary: bool | None = None
    source: str | None = Field(None, max_length=500)
    notes: str | None = None
    learning_order: int | None = None


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


class TextWordLinkBase(BaseModel):
    """Base schema for a word link within a text"""

    start_char: int = Field(..., ge=0, description="Start character offset (inclusive)")
    end_char: int = Field(..., gt=0, description="End character offset (exclusive)")
    notes: str | None = Field(None, max_length=500)


class TextWordLinkCreate(TextWordLinkBase):
    """Schema for creating a link to an existing word"""

    word_form_id: UUID
    status: TextWordLinkStatus = TextWordLinkStatus.CONFIRMED


class TextWordLinkUpdate(BaseModel):
    """Schema for updating link metadata or status"""

    status: TextWordLinkStatus | None = None
    notes: str | None = Field(None, max_length=500)
    word_form_id: UUID | None = None


class TextWordLink(BaseModel):
    """Complete schema for a link between text span and word"""

    id: UUID
    text_id: UUID
    word_form_id: UUID
    start_char: int
    end_char: int
    status: TextWordLinkStatus
    confidence: float | None = None
    notes: str | None = None
    created_by_id: UUID | None = None
    verified_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    verified_at: datetime | None = None
    # Form-level info (the actual surface form the link points at)
    word_text: str | None = None
    word_form_romanization: str | None = None
    word_form_ipa: str | None = None
    word_form_notes: str | None = None
    # Lexeme-level info (the dictionary entry the form belongs to)
    lexeme_id: UUID | None = None
    word_lemma: str | None = None
    word_part_of_speech: str | None = None
    word_notes: str | None = None
    word_language_id: UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class TextWithLinks(Text):
    """Text schema including link metadata"""

    word_links: list[TextWordLink] = []


class TextListItem(BaseModel):
    """Simplified schema for text lists"""

    id: UUID
    title: str
    content: str = Field(..., max_length=200)  # Truncated content for lists
    document_type: DocumentType
    language_id: UUID | None = None
    document_id: UUID | None = None
    is_primary: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TextFilter(BaseModel):
    """Schema for filtering and searching texts"""

    document_type: DocumentType | None = None
    language_id: UUID | None = None
    document_id: UUID | None = None
    is_primary: bool | None = None
    search_term: str | None = None  # Search in content or title
    created_by_id: UUID | None = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class TextStatistics(BaseModel):
    """Statistics about texts in the database"""

    total_texts: int
    texts_by_type: dict[str, int]
    texts_by_language: dict[str, int]
    texts_with_linked_words: int
    primary_texts: int
