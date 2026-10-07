"""Pydantic schemas for Quick Contribute: the task deck and its answers."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.word import LexemeStatus, PartOfSpeech
from app.schemas.proposal import ChangeProposal
from app.schemas.word import TranslationLink


class TextContext(BaseModel):
    """Where a word was seen: a short excerpt with the word's offsets in it."""

    text_id: UUID
    document_id: UUID | None = None
    title: str
    snippet: str
    highlight_start: int
    highlight_end: int


class _Task(BaseModel):
    # Stable per-item id ("<type>:<id>"); the client sends skipped keys back
    # as `exclude` so a skipped card doesn't come straight back.
    key: str


class DefineWordTask(_Task):
    """A word used in texts that the dictionary doesn't know yet."""

    type: Literal["define_word"] = "define_word"
    token: str
    occurrences: int
    context: TextContext


class RecordAudioTask(_Task):
    """A published word nobody has recorded yet, most-used first."""

    type: Literal["record_audio"] = "record_audio"
    lexeme_id: UUID
    word_form_id: UUID
    form: str
    ipa_pronunciation: str | None = None
    translations: list[TranslationLink] = []
    uses: int  # confirmed links to the word in texts


class ConfirmLinkTask(_Task):
    """An auto-suggested link from a word in a text to a dictionary entry."""

    type: Literal["confirm_link"] = "confirm_link"
    link_id: UUID
    context: TextContext
    lexeme_id: UUID
    word_form_id: UUID
    form: str
    lemma: str
    confidence: float | None = None
    translations: list[TranslationLink] = []


class ReviewWordTask(_Task):
    """Someone else's word suggestion waiting for a verdict."""

    type: Literal["review_word"] = "review_word"
    lexeme_id: UUID
    lemma: str
    part_of_speech: PartOfSpeech | None = None
    ipa_pronunciation: str | None = None
    notes: str | None = None
    creator_username: str | None = None
    translations: list[TranslationLink] = []


class VoteTask(_Task):
    """An open proposal the user hasn't voted on yet."""

    type: Literal["vote"] = "vote"
    proposal: ChangeProposal


ContributeTask = Annotated[
    DefineWordTask | RecordAudioTask | ConfirmLinkTask | ReviewWordTask | VoteTask,
    Field(discriminator="type"),
]


class DefineWordAnswer(BaseModel):
    """A new dictionary word from a define_word card."""

    # The word as seen in the text; kept as an extra form when the citation
    # form differs, so the linker can match it.
    token: str | None = Field(None, max_length=255)
    lemma: str = Field(..., min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None
    gloss: str | None = Field(None, max_length=255)
    gloss_language_id: UUID | None = None


class DefineWordResult(BaseModel):
    lexeme_id: UUID
    status: LexemeStatus
