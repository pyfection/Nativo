"""
Pydantic schemas for the lexicographic layer.

Two top-level entities: Lexeme (concept) and WordForm (surface form).
Location / Tag / Image schemas also live here for historical reasons.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.word import (
    Animacy,
    AntonymType,
    GrammaticalCase,
    GrammaticalGender,
    LexemeOrigin,
    LexemeRecommendation,
    LexemeStatus,
    PartOfSpeech,
    Plurality,
    Register,
    SynonymNuance,
    VerbAspect,
)

# Re-export for callers that imported the old WordStatus alias
WordStatus = LexemeStatus

# How sure the drafter of a suggestion is; reviewers batch-approve "high".
DraftConfidence = Literal["high", "medium", "low"]


# ============================================================================
# WordForm schemas
# ============================================================================


class WordFormBase(BaseModel):
    form: str = Field(..., min_length=1, max_length=255)
    romanization: str | None = Field(None, max_length=255)
    ipa_pronunciation: str | None = Field(None, max_length=255)
    is_lemma: bool = False
    plurality: Plurality | None = None
    grammatical_case: GrammaticalCase | None = None
    verb_aspect: VerbAspect | None = None
    notes: str | None = Field(None, max_length=500)


class WordFormCreate(WordFormBase):
    """Create a WordForm against an existing Lexeme."""

    lexeme_id: UUID
    confirmed_at_location_ids: list[UUID] | None = None


class WordFormCreateNested(WordFormBase):
    """Create a WordForm inline as part of a Lexeme create."""

    confirmed_at_location_ids: list[UUID] | None = None


class WordFormUpdate(BaseModel):
    form: str | None = Field(None, min_length=1, max_length=255)
    romanization: str | None = Field(None, max_length=255)
    ipa_pronunciation: str | None = Field(None, max_length=255)
    is_lemma: bool | None = None
    plurality: Plurality | None = None
    grammatical_case: GrammaticalCase | None = None
    verb_aspect: VerbAspect | None = None
    notes: str | None = Field(None, max_length=500)
    confirmed_at_location_ids: list[UUID] | None = None


class WordForm(WordFormBase):
    id: UUID
    lexeme_id: UUID
    rhyme_key: str | None = None
    near_rhyme_key: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# SpellingVariant schemas
# ============================================================================


class SpellingVariantBase(BaseModel):
    variant: str = Field(..., min_length=1, max_length=255)
    note: str | None = Field(None, max_length=500)


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
    note: str | None = None  # provenance of the matched variant


class SpellingResolution(BaseModel):
    """Resolve a single token to its standard spelling candidate(s)."""

    token: str
    normalized: str
    already_standard: bool
    candidates: list[SpellingCandidate]


class SpellingCorrection(BaseModel):
    """A span in a Text whose spelling has a known standard form."""

    start_char: int
    end_char: int
    original: str
    ambiguous: bool  # True when more than one standard form matches
    candidates: list[SpellingCandidate]


# ============================================================================
# Lexeme schemas
# ============================================================================


class LexemeBase(BaseModel):
    language_id: UUID
    lemma: str = Field(..., min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None
    gender: GrammaticalGender | None = None
    animacy: Animacy | None = None
    language_register: Register | None = Register.NEUTRAL
    origin: LexemeOrigin | None = None
    borrowed_from_language_id: UUID | None = None
    source: str | None = Field(None, max_length=500)
    notes: str | None = None


class LexemeCreate(LexemeBase):
    """
    Create a Lexeme.

    The required `lemma_form` payload becomes the canonical WordForm
    (is_lemma=True) for the new Lexeme. `additional_forms` lets a caller
    register inflected variants in the same request.
    """

    lemma_form: WordFormCreateNested
    additional_forms: list[WordFormCreateNested] | None = None
    tags: list[str] | None = None
    # Only kept when the entry lands as a suggestion (creator can't edit).
    draft_confidence: DraftConfidence | None = None


class LexemeUpdate(BaseModel):
    lemma: str | None = Field(None, min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None
    gender: GrammaticalGender | None = None
    animacy: Animacy | None = None
    language_register: Register | None = None
    origin: LexemeOrigin | None = None
    borrowed_from_language_id: UUID | None = None
    source: str | None = Field(None, max_length=500)
    notes: str | None = None
    status: LexemeStatus | None = None
    tags: list[str] | None = None


class Lexeme(LexemeBase):
    id: UUID
    created_by_id: UUID
    verified_by_id: UUID | None = None
    is_verified: bool
    status: LexemeStatus
    draft_confidence: DraftConfidence | None = None
    # Read-only here: changed only via an accepted ChangeProposal.
    recommendation: LexemeRecommendation = LexemeRecommendation.NEUTRAL
    recommendation_note: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LexemeListItem(BaseModel):
    id: UUID
    lemma: str
    language_id: UUID
    part_of_speech: PartOfSpeech | None = None
    origin: LexemeOrigin | None = None
    recommendation: LexemeRecommendation = LexemeRecommendation.NEUTRAL
    is_verified: bool
    status: LexemeStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LexemeSuggestion(BaseModel):
    """A pending suggestion in the review queue, with its author."""

    id: UUID
    language_id: UUID
    lemma: str
    part_of_speech: PartOfSpeech | None = None
    notes: str | None = None
    source: str | None = None
    draft_confidence: DraftConfidence | None = None
    status: LexemeStatus
    created_at: datetime
    creator_username: str | None = None
    forms: list[WordForm] = []
    translations: list["TranslationLink"] = []

    model_config = ConfigDict(from_attributes=True)


class LexemeRejection(BaseModel):
    """Payload for rejecting a suggestion."""

    reason: str | None = Field(None, max_length=500)


class FormCorrection(BaseModel):
    """A reviewer's fix to one form of a suggestion. `delete` drops it."""

    id: UUID
    form: str | None = Field(None, min_length=1, max_length=255)
    ipa_pronunciation: str | None = Field(None, max_length=255)
    notes: str | None = Field(None, max_length=500)
    delete: bool = False


class GlossCorrection(BaseModel):
    """The full set of glosses a suggestion should have in one language."""

    language_id: UUID
    lemmas: list[str]


class LexemeReviewCorrections(BaseModel):
    """
    Optional fixes applied atomically while approving a suggestion, so a
    nearly-right draft never has to be rejected and retyped.
    """

    lemma: str | None = Field(None, min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None
    gender: GrammaticalGender | None = None
    notes: str | None = None
    forms: list[FormCorrection] = []
    glosses: list[GlossCorrection] = []


class LexemeWithForms(Lexeme):
    forms: list[WordForm] = []

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Relationship schemas
# ============================================================================


class SynonymCreate(BaseModel):
    other_lexeme_id: UUID
    nuance: SynonymNuance | None = None
    notes: str | None = Field(None, max_length=500)


class AntonymCreate(BaseModel):
    other_lexeme_id: UUID
    antonym_type: AntonymType | None = None
    notes: str | None = Field(None, max_length=500)


class RelatedLexemeCreate(BaseModel):
    related_lexeme_id: UUID
    relationship_type: str | None = Field(None, max_length=100)


class TranslationCreate(BaseModel):
    other_lexeme_id: UUID
    notes: str | None = Field(None, max_length=500)


class TranslationUpdate(BaseModel):
    notes: str | None = Field(None, max_length=500)


class LexemeReference(BaseModel):
    """Compact lexeme reference used in relation responses."""

    id: UUID
    lemma: str
    language_id: UUID
    language_name: str | None = None
    part_of_speech: PartOfSpeech | None = None
    recommendation: LexemeRecommendation | None = None

    model_config = ConfigDict(from_attributes=True)


class SynonymLink(LexemeReference):
    nuance: SynonymNuance | None = None
    notes: str | None = None


class AntonymLink(LexemeReference):
    antonym_type: AntonymType | None = None
    notes: str | None = None


class TranslationLink(LexemeReference):
    notes: str | None = None


# ============================================================================
# Rhyme search
# ============================================================================


class RhymeMatch(BaseModel):
    word_form_id: UUID
    lexeme_id: UUID
    form: str
    lemma: str
    ipa_pronunciation: str | None = None
    language_id: UUID

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Filters
# ============================================================================


class LexemeFilter(BaseModel):
    language_id: UUID | None = None
    part_of_speech: PartOfSpeech | None = None
    status: LexemeStatus | None = None
    is_verified: bool | None = None
    search_term: str | None = None
    created_by_id: UUID | None = None
    tag_ids: list[UUID] | None = None
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
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=500)


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    name: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=500)


class LocationInDB(LocationBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Location(LocationInDB):
    pass


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class TagInDB(TagBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Tag(TagInDB):
    pass


class ImageBase(BaseModel):
    file_path: str = Field(..., max_length=500)
    alt_text: str | None = Field(None, max_length=500)
    caption: str | None = None


class ImageCreate(ImageBase):
    pass


class ImageUpdate(BaseModel):
    alt_text: str | None = Field(None, max_length=500)
    caption: str | None = None


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


LexemeSuggestion.model_rebuild()
