"""Pydantic schemas for change proposals and votes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.change_proposal import ProposalStatus, ProposalType, VoteChoice
from app.models.word import LexemeOrigin, LexemeRecommendation


class RecommendationProposalCreate(BaseModel):
    """Propose marking a lexeme preferred / neutral / discouraged."""

    recommendation: LexemeRecommendation
    note: str | None = Field(None, max_length=1000)  # shown on the word once accepted
    rationale: str | None = Field(None, max_length=2000)  # the case made to voters


class VoteCreate(BaseModel):
    choice: VoteChoice
    comment: str | None = Field(None, max_length=1000)


class ProposalVote(BaseModel):
    user_id: UUID
    username: str | None = None
    choice: VoteChoice
    comment: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LexemeUsage(BaseModel):
    """How much real-world evidence backs a lexeme — shown next to a vote."""

    lexeme_id: UUID
    lemma: str
    origin: LexemeOrigin | None = None
    recommendation: LexemeRecommendation
    text_count: int  # distinct texts linking one of its forms (non-rejected links)
    audio_count: int  # recordings attached to its forms
    locations: list[str]  # where its forms were attested


class ChangeProposal(BaseModel):
    id: UUID
    language_id: UUID
    lexeme_id: UUID | None = None
    lexeme_lemma: str | None = None
    proposal_type: ProposalType
    payload: dict
    rationale: str | None = None
    status: ProposalStatus
    created_by_id: UUID | None = None
    created_by_username: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    approvals: int
    rejections: int
    threshold: int
    votes: list[ProposalVote] = []
    # The target lexeme first, then its same-language synonyms.
    usage: list[LexemeUsage] = []
