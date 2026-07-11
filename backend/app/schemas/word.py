"""
Pydantic schemas for the lexicographic layer.

Two top-level entities: Lexeme (concept) and WordForm (surface form).
Location / Tag / Image schemas also live here for historical reasons.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.word import (
    Animacy,
    AntonymType,
    GrammaticalCase,
    GrammaticalGender,
    LexemeStatus,
    PartOfSpeech,
    Plurality,
    Register,
    SynonymNuance,
    VerbAspect,
    WordTextType,
)

# Re-export for callers that imported the old WordStatus alias
WordStatus = LexemeStatus


# ============================================================================
# WordForm schemas
# ============================================================================


class WordFormBase(BaseModel):
    form: str = Field(..., min_length=1, max_length=255)
    romanization: Optional[str] = Field(None, max_length=255)
    ipa_pronunciation: Optional[str] = Field(None, max_length=255)
    is_lemma: bool = False
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[GrammaticalCase] = None
    verb_aspect: Optional[VerbAspect] = None
    notes: Optional[str] = Field(None, max_length=500)


class WordFormCreate(WordFormBase):
    """Create a WordForm against an existing Lexeme."""
    lexeme_id: UUID
    confirmed_at_location_ids: Optional[List[UUID]] = None


class WordFormCreateNested(WordFormBase):
    """Create a WordForm inline as part of a Lexeme create."""
    confirmed_at_location_ids: Optional[List[UUID]] = None


class WordFormUpdate(BaseModel):
    form: Optional[str] = Field(None, min_length=1, max_length=255)
    romanization: Optional[str] = Field(None, max_length=255)
    ipa_pronunciation: Optional[str] = Field(None, max_length=255)
    is_lemma: Optional[bool] = None
    plurality: Optional[Plurality] = None
    grammatical_case: Optional[GrammaticalCase] = None
    verb_aspect: Optional[VerbAspect] = None
    notes: Optional[str] = Field(None, max_length=500)
    confirmed_at_location_ids: Optional[List[UUID]] = None


class WordForm(WordFormBase):
    id: UUID
    lexeme_id: UUID
    rhyme_key: Optional[str] = None
    near_rhyme_key: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SpellingVariant schemas
# ============================================================================


class SpellingVariantBase(BaseModel):
    variant: str = Field(..., min_length=1, max_length=255)
    note: Optional[str] = Field(None, max_length=500)


class SpellingVariantCreate(SpellingVariantBase):
    """Add a non-standard spelling that maps to an existing WordForm."""


class SpellingVariant(SpellingVariantBase):
    id: UUID
    word_form_id: UUID
    normalized: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpellingCandidate(BaseModel):
    """One standard form a non-standard spelling could resolve to."""

    word_form_id: UUID
    lexeme_id: UUID
    standard_form: str
    lemma: str
    note: Optional[str] = None  # provenance of the matched variant


class SpellingResolution(BaseModel):
    """Resolve a single token to its standard spelling candidate(s)."""

    token: str
    normalized: str
    already_standard: bool
    candidates: List[SpellingCandidate]


class SpellingCorrection(BaseModel):
    """A span in a Text whose spelling has a known standard form."""

    start_char: int
    end_char: int
    original: str
    ambiguous: bool  # True when more than one standard form matches
    candidates: List[SpellingCandidate]


# ============================================================================
# Lexeme schemas
# ============================================================================


class LexemeBase(BaseModel):
    language_id: UUID
    lemma: str = Field(..., min_length=1, max_length=255)
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    animacy: Optional[Animacy] = None
    language_register: Optional[Register] = Register.NEUTRAL
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class LexemeCreate(LexemeBase):
    """
    Create a Lexeme.

    The required `lemma_form` payload becomes the canonical WordForm
    (is_lemma=True) for the new Lexeme. `additional_forms` lets a caller
    register inflected variants in the same request.
    """
    lemma_form: WordFormCreateNested
    additional_forms: Optional[List[WordFormCreateNested]] = None
    tags: Optional[List[str]] = None


class LexemeUpdate(BaseModel):
    lemma: Optional[str] = Field(None, min_length=1, max_length=255)
    part_of_speech: Optional[PartOfSpeech] = None
    gender: Optional[GrammaticalGender] = None
    animacy: Optional[Animacy] = None
    language_register: Optional[Register] = None
    source: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None
    status: Optional[LexemeStatus] = None
    tags: Optional[List[str]] = None


class Lexeme(LexemeBase):
    id: UUID
    created_by_id: UUID
    verified_by_id: Optional[UUID] = None
    is_verified: bool
    status: LexemeStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LexemeListItem(BaseModel):
    id: UUID
    lemma: str
    language_id: UUID
    part_of_speech: Optional[PartOfSpeech] = None
    is_verified: bool
    status: LexemeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LexemeSuggestion(BaseModel):
    """A pending suggestion in the review queue, with its author."""

    id: UUID
    language_id: UUID
    lemma: str
    part_of_speech: Optional[PartOfSpeech] = None
    notes: Optional[str] = None
    status: LexemeStatus
    created_at: datetime
    creator_username: Optional[str] = None
    forms: List[WordForm] = []

    model_config = ConfigDict(from_attributes=True)


class LexemeRejection(BaseModel):
    """Payload for rejecting a suggestion."""

    reason: Optional[str] = Field(None, max_length=500)


class LexemeWithForms(Lexeme):
    forms: List[WordForm] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Relationship schemas
# ============================================================================


class SynonymCreate(BaseModel):
    other_lexeme_id: UUID
    nuance: Optional[SynonymNuance] = None
    notes: Optional[str] = Field(None, max_length=500)


class AntonymCreate(BaseModel):
    other_lexeme_id: UUID
    antonym_type: Optional[AntonymType] = None
    notes: Optional[str] = Field(None, max_length=500)


class RelatedLexemeCreate(BaseModel):
    related_lexeme_id: UUID
    relationship_type: Optional[str] = Field(None, max_length=100)


class TranslationCreate(BaseModel):
    other_lexeme_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class TranslationUpdate(BaseModel):
    notes: Optional[str] = Field(None, max_length=500)


class LexemeReference(BaseModel):
    """Compact lexeme reference used in relation responses."""
    id: UUID
    lemma: str
    language_id: UUID
    language_name: Optional[str] = None
    part_of_speech: Optional[PartOfSpeech] = None

    model_config = ConfigDict(from_attributes=True)


class SynonymLink(LexemeReference):
    nuance: Optional[SynonymNuance] = None
    notes: Optional[str] = None


class AntonymLink(LexemeReference):
    antonym_type: Optional[AntonymType] = None
    notes: Optional[str] = None


class TranslationLink(LexemeReference):
    notes: Optional[str] = None


# ============================================================================
# Rhyme search
# ============================================================================


class RhymeMatch(BaseModel):
    word_form_id: UUID
    lexeme_id: UUID
    form: str
    lemma: str
    ipa_pronunciation: Optional[str] = None
    language_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Filters
# ============================================================================


class LexemeFilter(BaseModel):
    language_id: Optional[UUID] = None
    part_of_speech: Optional[PartOfSpeech] = None
    status: Optional[LexemeStatus] = None
    is_verified: Optional[bool] = None
    search_term: Optional[str] = None
    created_by_id: Optional[UUID] = None
    tag_ids: Optional[List[UUID]] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# ============================================================================
# Statistics
# ============================================================================


class LexemeStatistics(BaseModel):
    total_lexemes: int
    verified_lexemes: int
    lexemes_by_language: dict[str, int]
    lexemes_by_status: dict[str, int]
    lexemes_by_part_of_speech: dict[str, int]
    lexemes_with_audio: int
    lexemes_with_images: int


# ============================================================================
# Location / Tag / Image (squatters, kept here for back-compat imports)
# ============================================================================


class LocationBase(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=500)


class LocationInDB(LocationBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Location(LocationInDB):
    pass


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class TagInDB(TagBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Tag(TagInDB):
    pass


class ImageBase(BaseModel):
    file_path: str = Field(..., max_length=500)
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = None


class ImageCreate(ImageBase):
    pass


class ImageUpdate(BaseModel):
    alt_text: Optional[str] = Field(None, max_length=500)
    caption: Optional[str] = None


class ImageInDB(ImageBase):
    id: UUID
    uploaded_by_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Image(ImageInDB):
    pass


# Re-exports under the old names so dependent modules don't break while we
# migrate them. Prefer the new names in new code.
Word = Lexeme
WordCreate = LexemeCreate
WordUpdate = LexemeUpdate
WordListItem = LexemeListItem
WordFilter = LexemeFilter
WordStatistics = LexemeStatistics
