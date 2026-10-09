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


class SourceContext(BaseModel):
    """Where a word was seen outside Nativo: an excerpt, its link and licence."""

    snippet_id: UUID
    snippet: str
    highlight_start: int
    highlight_end: int
    source_url: str
    source_title: str
    license: str | None = None


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


class ConfirmSpellingTask(_Task):
    """A word as an outside source writes it, for its standard spelling."""

    type: Literal["confirm_spelling"] = "confirm_spelling"
    token: str
    occurrences: int  # across all stored source snippets
    source: SourceContext


class TranslateWordTask(_Task):
    """A word in a language the user speaks with no translation yet."""

    type: Literal["translate_word"] = "translate_word"
    source_lexeme_id: UUID
    lemma: str
    source_language_id: UUID
    part_of_speech: PartOfSpeech | None = None
    # Its translations into other languages, to pin down the sense.
    translations: list[TranslationLink] = []


class TranslateTextTask(_Task):
    """A short text in a language the user speaks: an internal document
    (text_id) or an outside snippet (snippet_id)."""

    type: Literal["translate_text"] = "translate_text"
    source_language_id: UUID
    title: str
    content: str
    text_id: UUID | None = None
    document_id: UUID | None = None
    snippet_id: UUID | None = None
    source_url: str | None = None
    license: str | None = None


class ReviewAdditionTask(_Task):
    """Someone's suggested addition to an existing entry: a spelling variant
    or a translation link."""

    type: Literal["review_addition"] = "review_addition"
    proposal_id: UUID
    proposal_type: Literal["add_spelling_variant", "add_translation"]
    lexeme_id: UUID
    lemma: str
    variant: str | None = None  # add_spelling_variant: the outside spelling
    note: str | None = None  # e.g. where the spelling was seen
    other_lemma: str | None = None  # add_translation: the word it translates
    other_language_id: UUID | None = None
    # add_spelling_variant from a text card: accepting also corrects the
    # old spelling in the language's texts.
    fix_texts: bool = False
    creator_username: str | None = None


ContributeTask = Annotated[
    DefineWordTask
    | RecordAudioTask
    | ConfirmLinkTask
    | ReviewWordTask
    | VoteTask
    | ConfirmSpellingTask
    | TranslateWordTask
    | TranslateTextTask
    | ReviewAdditionTask,
    Field(discriminator="type"),
]


class DefineWordAnswer(BaseModel):
    """A new dictionary word from a define_word card."""

    # The word as seen in the text; kept as an extra form when the citation
    # form differs, so the linker can match it.
    token: str | None = Field(None, max_length=255)
    # The standard spelling of `token` when the text misspells it (e.g. an
    # outdated spelling). The text's spelling becomes a spelling variant and
    # is corrected in the language's texts (by an editor now, otherwise once
    # a reviewer accepts it).
    corrected: str | None = Field(None, max_length=255)
    lemma: str = Field(..., min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None
    # One or more meanings, comma-separated; each becomes a word in the
    # gloss language linked as a translation.
    gloss: str | None = Field(None, max_length=255)
    gloss_language_id: UUID | None = None


class DefineWordResult(BaseModel):
    lexeme_id: UUID
    status: LexemeStatus
    # published / suggested (new entry pending review) / proposed (a
    # spelling fix to an existing entry, waiting for a reviewer).
    outcome: Literal["published", "suggested", "proposed"] = "published"


class WordSuggestion(BaseModel):
    """An AI suggestion for a word card. A person checks it before anything
    is saved; empty fields mean the AI wasn't sure."""

    lemma: str | None = None
    part_of_speech: PartOfSpeech | None = None
    gloss: str | None = None
    # How the word should be written when the text breaks the writing
    # standard (e.g. an outdated spelling); None when it looks right.
    standard_spelling: str | None = None
    explanation: str | None = None


class SpellingAnswer(BaseModel):
    """The standard spelling of a word seen in an outside source."""

    token: str = Field(..., min_length=1, max_length=255)  # as the source writes it
    standard: str = Field(..., min_length=1, max_length=255)
    snippet_id: UUID | None = None
    # Only used when the standard spelling is a new word.
    part_of_speech: PartOfSpeech | None = None
    gloss: str | None = Field(None, max_length=255)
    gloss_language_id: UUID | None = None


class TranslateWordAnswer(BaseModel):
    source_lexeme_id: UUID
    lemma: str = Field(..., min_length=1, max_length=255)
    part_of_speech: PartOfSpeech | None = None


class TranslateTextAnswer(BaseModel):
    """A translation of an internal text or an outside snippet (one of the two)."""

    text_id: UUID | None = None
    snippet_id: UUID | None = None
    title: str | None = Field(None, max_length=500)  # defaults to the source's title
    content: str = Field(..., min_length=1)


Outcome = Literal["published", "suggested", "proposed"]


class ContributeResult(BaseModel):
    """What an answer did: published directly, suggested (a new entry pending
    review) or proposed (an addition to an existing entry, for a reviewer)."""

    outcome: Outcome
    lexeme_id: UUID | None = None
    document_id: UUID | None = None


class SourceTextCreate(BaseModel):
    """Text from an outside source, stored as sentence snippets."""

    source_url: str = Field(..., min_length=1, max_length=1000)
    source_title: str = Field(..., min_length=1, max_length=500)
    text: str = Field(..., min_length=1)
    license: str | None = Field(None, max_length=100)


class SourceTextResult(BaseModel):
    created: int
