from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.models.word import (
    PartOfSpeech,
    GrammaticalGender,
    Plurality,
    GrammaticalCase,
    VerbAspect,
    Animacy,
    Register,
    WordStatus,
    WordDocumentType
)
from app.models.document import DocumentType


# ============================================================================
# Word Schemas
# ============================================================================

class WordBase(BaseModel):
    """Base schema for Word with common fields"""
    word: str = Field(..., min_length=1, max_length=255, description="The word in the target language")
    language_id: UUID = Field(..., description="ID of the language")
    romanization: Optional[str] = Field(None, max_length=255, description="Romanized/transliterated version")
    ipa_pronunciation: Optional[str] = Field(None, max_length=255, description="IPA pronunciation")
    
    # Linguistic Information (all enums)
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[GrammaticalCase] = None
    verb_aspect: Optional[VerbAspect] = None
    animacy: Optional[Animacy] = None
    
    # Cultural Context
    register: Optional[Register] = Register.NEUTRAL
    
    # Location
    confirmed_at_id: Optional[UUID] = None
    
    # Metadata
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class WordCreate(WordBase):
    """Schema for creating a new word entry"""
    pass


class WordUpdate(BaseModel):
    """Schema for updating an existing word entry (all fields optional)"""
    word: Optional[str] = Field(None, min_length=1, max_length=255)
    language_id: Optional[UUID] = None
    romanization: Optional[str] = Field(None, max_length=255)
    ipa_pronunciation: Optional[str] = Field(None, max_length=255)
    
    # Linguistic Information
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[GrammaticalCase] = None
    verb_aspect: Optional[VerbAspect] = None
    animacy: Optional[Animacy] = None
    
    # Cultural Context
    register: Optional[Register] = None
    
    # Location
    confirmed_at_id: Optional[UUID] = None
    
    # Metadata
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    status: Optional[WordStatus] = None


class WordInDB(WordBase):
    """Schema for word as stored in database"""
    id: UUID
    created_by_id: UUID
    verified_by_id: Optional[UUID] = None
    is_verified: bool
    status: WordStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Word(WordInDB):
    """Complete word schema for API responses"""
    pass


class WordListItem(BaseModel):
    """Simplified schema for word lists"""
    id: UUID
    word: str
    romanization: Optional[str] = None
    language_id: UUID
    part_of_speech: Optional[PartOfSpeech] = None
    is_verified: bool
    status: WordStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Document Schemas (unified for full texts and snippets)
# ============================================================================

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


# ============================================================================
# Location Schemas
# ============================================================================

class LocationBase(BaseModel):
    """Base schema for Location"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class LocationCreate(LocationBase):
    """Schema for creating a new location"""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating a location"""
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class LocationInDB(LocationBase):
    """Schema for location as stored in database"""
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Location(LocationInDB):
    """Complete location schema"""
    pass


# ============================================================================
# Tag Schemas
# ============================================================================

class TagBase(BaseModel):
    """Base schema for Tag"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TagCreate(TagBase):
    """Schema for creating a new tag"""
    pass


class TagUpdate(BaseModel):
    """Schema for updating a tag"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TagInDB(TagBase):
    """Schema for tag as stored in database"""
    id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Tag(TagInDB):
    """Complete tag schema"""
    pass


# ============================================================================
# Image Schemas
# ============================================================================

class ImageBase(BaseModel):
    """Base schema for Image"""
    file_path: str = Field(..., max_length=500)
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = None


class ImageCreate(ImageBase):
    """Schema for creating a new image"""
    pass


class ImageUpdate(BaseModel):
    """Schema for updating an image"""
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = None


class ImageInDB(ImageBase):
    """Schema for image as stored in database"""
    id: UUID
    uploaded_by_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class Image(ImageInDB):
    """Complete image schema"""
    pass


# ============================================================================
# Relationship Schemas
# ============================================================================

class WordRelationshipCreate(BaseModel):
    """Schema for creating word relationships (synonyms, antonyms, related)"""
    word_id: UUID
    related_word_id: UUID
    relationship_type: Optional[str] = Field(None, max_length=100)  # For related words


class WordDocumentAssociation(BaseModel):
    """Schema for linking a word to a document with a relationship type"""
    word_id: UUID
    document_id: UUID
    relationship_type: WordDocumentType


class WordWithRelations(Word):
    """Extended word schema with all relationships"""
    audio_files: List[UUID] = []
    images: List[UUID] = []
    tags: List[Tag] = []
    
    # Typed document relationships
    definitions: List[DocumentListItem] = []
    literal_translations: List[DocumentListItem] = []
    context_notes: List[DocumentListItem] = []
    usage_examples: List[DocumentListItem] = []
    etymologies: List[DocumentListItem] = []
    cultural_significance: List[DocumentListItem] = []
    
    # All documents (including stories where word is mentioned)
    documents: List[DocumentListItem] = []
    
    # Word relationships
    synonyms: List[WordListItem] = []
    antonyms: List[WordListItem] = []
    related_words: List[WordListItem] = []
    
    # Location
    confirmed_at: Optional[Location] = None
    
    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Filter & Search Schemas
# ============================================================================

class WordFilter(BaseModel):
    """Schema for filtering and searching words"""
    language_id: Optional[UUID] = None
    part_of_speech: Optional[PartOfSpeech] = None
    grammatical_case: Optional[GrammaticalCase] = None
    verb_aspect: Optional[VerbAspect] = None
    animacy: Optional[Animacy] = None
    register: Optional[Register] = None
    status: Optional[WordStatus] = None
    is_verified: Optional[bool] = None
    search_term: Optional[str] = None  # Search in word, romanization
    created_by_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = None  # Filter by tags
    location_id: Optional[UUID] = None  # Filter by confirmation location
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class DocumentFilter(BaseModel):
    """Schema for filtering and searching documents"""
    document_type: Optional[DocumentType] = None
    language_id: Optional[UUID] = None
    search_term: Optional[str] = None  # Search in content
    created_by_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# ============================================================================
# Statistics Schemas
# ============================================================================

class WordStatistics(BaseModel):
    """Statistics about words in the database"""
    total_words: int
    verified_words: int
    words_by_language: dict[str, int]  # language_id -> count
    words_by_status: dict[str, int]
    words_by_part_of_speech: dict[str, int]
    words_with_audio: int
    words_with_images: int
    words_with_location: int
    words_with_documents: int


class DocumentStatistics(BaseModel):
    """Statistics about documents in the database"""
    total_documents: int
    documents_by_type: dict[str, int]
    documents_by_language: dict[str, int]
    documents_with_linked_words: int
