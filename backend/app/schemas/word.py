from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

from app.models.word import (
    PartOfSpeech,
    GrammaticalGender,
    Plurality,
    Register,
    DifficultyLevel,
    WordStatus
)


# Base schema with common fields
class WordBase(BaseModel):
    """Base schema for Word with common fields"""
    word: str = Field(..., min_length=1, max_length=255, description="The word in the target language")
    language_id: int = Field(..., gt=0, description="ID of the language")
    romanization: Optional[str] = Field(None, max_length=255, description="Romanized/transliterated version")
    ipa_pronunciation: Optional[str] = Field(None, max_length=255, description="IPA pronunciation")
    
    # Linguistic Information
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[str] = Field(None, max_length=50)
    verb_aspect: Optional[str] = Field(None, max_length=50)
    animacy: Optional[str] = Field(None, max_length=50)
    
    # Meaning & Context
    definition: str = Field(..., min_length=1, description="Primary definition")
    literal_translation: Optional[str] = None
    context_notes: Optional[str] = None
    usage_examples: Optional[str] = None  # JSON string of examples
    synonyms: Optional[str] = None  # JSON string of synonyms
    antonyms: Optional[str] = None  # JSON string of antonyms
    related_words: Optional[str] = None  # JSON string of related word IDs
    
    # Audio & Media
    audio_id: Optional[int] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    
    # Etymology & Cultural Context
    etymology: Optional[str] = None
    cultural_significance: Optional[str] = None
    register: Optional[Register] = Register.NEUTRAL
    regional_variant: Optional[str] = Field(None, max_length=255)
    
    # Learning & Classification
    difficulty_level: Optional[DifficultyLevel] = None
    frequency_rank: Optional[int] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None  # JSON string of tags
    is_endangered_specific: bool = False
    
    # Metadata
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


# Schema for creating a new word
class WordCreate(WordBase):
    """Schema for creating a new word entry"""
    pass


# Schema for updating a word
class WordUpdate(BaseModel):
    """Schema for updating an existing word entry (all fields optional)"""
    word: Optional[str] = Field(None, min_length=1, max_length=255)
    language_id: Optional[int] = Field(None, gt=0)
    romanization: Optional[str] = Field(None, max_length=255)
    ipa_pronunciation: Optional[str] = Field(None, max_length=255)
    
    # Linguistic Information
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[str] = Field(None, max_length=50)
    verb_aspect: Optional[str] = Field(None, max_length=50)
    animacy: Optional[str] = Field(None, max_length=50)
    
    # Meaning & Context
    definition: Optional[str] = Field(None, min_length=1)
    literal_translation: Optional[str] = None
    context_notes: Optional[str] = None
    usage_examples: Optional[str] = None
    synonyms: Optional[str] = None
    antonyms: Optional[str] = None
    related_words: Optional[str] = None
    
    # Audio & Media
    audio_id: Optional[int] = Field(None, gt=0)
    image_url: Optional[str] = Field(None, max_length=500)
    
    # Etymology & Cultural Context
    etymology: Optional[str] = None
    cultural_significance: Optional[str] = None
    register: Optional[Register] = None
    regional_variant: Optional[str] = Field(None, max_length=255)
    
    # Learning & Classification
    difficulty_level: Optional[DifficultyLevel] = None
    frequency_rank: Optional[int] = Field(None, gt=0)
    category: Optional[str] = Field(None, max_length=100)
    tags: Optional[str] = None
    is_endangered_specific: Optional[bool] = None
    
    # Metadata
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    status: Optional[WordStatus] = None


# Schema for reading a word (includes database fields)
class WordInDB(WordBase):
    """Schema for word as stored in database"""
    id: int
    created_by_id: int
    verified_by_id: Optional[int] = None
    is_verified: bool
    status: WordStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for API responses
class Word(WordInDB):
    """Complete word schema for API responses"""
    pass


# Schema for list responses
class WordListItem(BaseModel):
    """Simplified schema for word lists"""
    id: int
    word: str
    romanization: Optional[str] = None
    language_id: int
    part_of_speech: Optional[PartOfSpeech] = None
    definition: str
    difficulty_level: Optional[DifficultyLevel] = None
    is_verified: bool
    status: WordStatus
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema for search/filter parameters
class WordFilter(BaseModel):
    """Schema for filtering and searching words"""
    language_id: Optional[int] = None
    part_of_speech: Optional[PartOfSpeech] = None
    difficulty_level: Optional[DifficultyLevel] = None
    category: Optional[str] = None
    register: Optional[Register] = None
    status: Optional[WordStatus] = None
    is_verified: Optional[bool] = None
    is_endangered_specific: Optional[bool] = None
    search_term: Optional[str] = None  # Search in word, romanization, definition
    created_by_id: Optional[int] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# Schema for word statistics
class WordStatistics(BaseModel):
    """Statistics about words in the database"""
    total_words: int
    verified_words: int
    words_by_language: dict[int, int]
    words_by_status: dict[str, int]
    words_by_difficulty: dict[str, int]
    words_by_part_of_speech: dict[str, int]

