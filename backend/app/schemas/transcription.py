"""
Schemas for speech/IPA → standard-spelling transcription.

The output is a *suggestion*: each token carries its candidates so a person can
pick or correct before anything is saved.
"""

from uuid import UUID

from pydantic import BaseModel, Field


class IpaTranscriptionRequest(BaseModel):
    language_id: UUID
    # Segmentation cost grows with input length; keep requests to a sentence or two.
    ipa: str = Field(..., min_length=1, max_length=300)


class TranscriptionCandidate(BaseModel):
    word_form_id: UUID
    lexeme_id: UUID
    form: str  # standard spelling
    lemma: str
    ipa_pronunciation: str
    distance: float  # weighted phonetic edit distance, 0 = exact


class TranscriptionToken(BaseModel):
    ipa: str  # the slice of the input this token covers (normalised segments)
    spelling: str  # best guess at the standard spelling
    known: bool  # False → spelled by fallback rules, not found in the lexicon
    ambiguous: bool  # True → near-tied candidates with different spellings
    confidence: float  # 0..1, rough
    candidates: list[TranscriptionCandidate]


class TranscriptionResult(BaseModel):
    ipa: str  # the full IPA that was transcribed (from the recogniser, for audio)
    text: str  # tokens' spellings joined with spaces
    tokens: list[TranscriptionToken]
    lexicon_size: int  # word forms with IPA available for matching
