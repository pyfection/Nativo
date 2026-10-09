"""
AiSuggestion — a stored AI answer for a Quick Contribute card.

Every user who gets the card for the same unknown word sees the same
suggestion, so it is made once per (language, word, meaning language) and
kept here. Nothing in it is dictionary content: a person still checks and
submits the card, and their answer goes through the normal review flow.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class AiSuggestion(Base):
    __tablename__ = "ai_suggestions"
    __table_args__ = (
        UniqueConstraint(
            "language_id", "kind", "key", "gloss_language_id", name="uq_ai_suggestions_card"
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind = Column(String(50), nullable=False)  # "word"
    key = Column(String(255), nullable=False)  # the word, fold_for_match'ed
    gloss_language_id = Column(
        UUID(as_uuid=True), ForeignKey("languages.id", ondelete="CASCADE"), nullable=True
    )
    payload = Column(JSON, nullable=False)
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=_now, nullable=False)

    def __repr__(self) -> str:
        return f"<AiSuggestion(kind='{self.kind}', key='{self.key}')>"
