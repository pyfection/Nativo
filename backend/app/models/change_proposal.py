"""
Change proposals — collective decisions on published content.

Some decisions shouldn't be made by one person, e.g. promoting a native word
(Párádaisa) over a loanword (Tomadn). Instead of setting such a field
directly, an editor opens a `ChangeProposal`; members of the language with
edit/verify rights vote on it, and it is applied only once it reaches the
language's `proposal_approval_threshold` with no objection.

The table is generic (type + JSON payload) so later edit/delete proposals
from the suggester tier can reuse it. Today the only type is
SET_RECOMMENDATION, which targets a Lexeme.
"""

import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class ProposalType(str, enum.Enum):
    SET_RECOMMENDATION = "set_recommendation"  # payload: {recommendation, note}


class ProposalStatus(str, enum.Enum):
    OPEN = "open"
    ACCEPTED = "accepted"  # threshold reached, change applied
    REJECTED = "rejected"  # threshold of objections reached
    WITHDRAWN = "withdrawn"  # pulled by its author


class VoteChoice(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"


def _values(e: type[enum.Enum]) -> list[str]:
    return [m.value for m in e]


class ChangeProposal(Base):
    __tablename__ = "change_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lexeme_id = Column(
        UUID(as_uuid=True),
        ForeignKey("lexemes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    proposal_type = Column(
        SQLEnum(ProposalType, name="proposaltype", values_callable=_values), nullable=False
    )
    payload = Column(JSON, nullable=False)
    rationale = Column(Text, nullable=True)
    status = Column(
        SQLEnum(ProposalStatus, name="proposalstatus", values_callable=_values),
        default=ProposalStatus.OPEN,
        nullable=False,
        index=True,
    )
    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    language = relationship("Language")
    lexeme = relationship("Lexeme")
    created_by = relationship("User")
    votes = relationship(
        "ProposalVote",
        back_populates="proposal",
        cascade="all, delete-orphan",
        order_by="ProposalVote.created_at",
    )


class ProposalVote(Base):
    __tablename__ = "proposal_votes"
    __table_args__ = (UniqueConstraint("proposal_id", "user_id", name="uq_proposal_vote_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proposal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("change_proposals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    choice = Column(SQLEnum(VoteChoice, name="votechoice", values_callable=_values), nullable=False)
    comment = Column(String(1000), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    proposal = relationship("ChangeProposal", back_populates="votes")
    user = relationship("User")
