"""Schemas for the guided learning path."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.learning import DifficultyRating


class LearningPathEntry(BaseModel):
    """One text on the learner's line through the corpus."""

    text_id: UUID
    document_id: UUID
    title: str
    total_lexemes: int
    new_lexeme_count: int
    known_pct: float
    state: Literal["completed", "recommended", "upcoming"]
    completed_at: datetime | None = None
    difficulty_rating: DifficultyRating | None = None


class TextCompletion(BaseModel):
    """Payload for finishing a text in the guided reader."""

    difficulty_rating: DifficultyRating
    # Lexemes the reader tapped during this session. Taps are also recorded
    # live via the click endpoint; this is the same set, used to exclude them
    # from the finished-without-tapping bonus.
    clicked_lexeme_ids: list[UUID] = []


class ReviewTranslation(BaseModel):
    """A translation shown on the back of a flashcard."""

    lemma: str
    language_id: UUID


class ReviewCard(BaseModel):
    """One shaky word in the practice deck."""

    lexeme_id: UUID
    lemma: str
    score: int
    ipa_pronunciation: str | None = None
    # The lemma WordForm, so the client can fetch attached audio lazily.
    lemma_form_id: UUID | None = None
    translations: list[ReviewTranslation] = []


class ReviewVerdict(BaseModel):
    """Flashcard self-assessment."""

    knew: bool


class PlacementRequest(BaseModel):
    """Self-assessed starting level for a language."""

    level: Literal["beginner", "intermediate", "advanced"]


class PlacementResult(BaseModel):
    seeded: int


class LexemeKnowledgeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    lexeme_id: UUID
    score: int


class TextProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text_id: UUID
    difficulty_rating: DifficultyRating
    completed_at: datetime
