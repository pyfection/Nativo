"""
Model representing a link between a span of text content and a dictionary word.
"""
from __future__ import annotations

from datetime import datetime
import enum
import uuid

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class TextWordLinkStatus(str, enum.Enum):
    """
    Status of a link between a span in a text and a word.

    suggested:
        Auto-generated suggestion that needs human verification.
    confirmed:
        Verified/approved link between text span and word.
    rejected:
        Suggestion that was explicitly rejected by a user (prevents re-suggestion).
    """

    SUGGESTED = "suggested"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class TextWordLink(Base):
    """
    Persistent link between a span of characters in a text and a word entry.
    """

    __tablename__ = "text_word_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    text_id = Column(UUID(as_uuid=True), ForeignKey("texts.id"), nullable=False, index=True)
    word_id = Column(UUID(as_uuid=True), ForeignKey("words.id"), nullable=False, index=True)

    # Character offsets within Text.content (start inclusive, end exclusive)
    start_char = Column(Integer, nullable=False)
    end_char = Column(Integer, nullable=False)

    status = Column(
        SQLEnum(TextWordLinkStatus, name="textwordlinkstatus"),
        nullable=False,
        default=TextWordLinkStatus.SUGGESTED,
    )
    confidence = Column(Float, nullable=True)  # Optional for auto-suggestions
    notes = Column(String(500), nullable=True)

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    verified_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    verified_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("text_id", "start_char", "end_char", name="uq_text_word_links_unique_span"),
    )

    text = relationship("Text", back_populates="word_links")
    word = relationship("Word", back_populates="text_links")
    created_by = relationship("User", foreign_keys=[created_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])

    @property
    def word_text(self) -> str | None:
        return self.word.word if self.word else None

    @property
    def word_language_id(self):
        return self.word.language_id if self.word else None

    def __repr__(self) -> str:
        return (
            f"<TextWordLink(id={self.id}, text_id={self.text_id}, word_id={self.word_id}, "
            f"span=({self.start_char}, {self.end_char}), status={self.status})>"
        )


