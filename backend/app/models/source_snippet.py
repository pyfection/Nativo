"""
SourceSnippet — a sentence from an outside source (a Wikipedia article, a
web page), kept with a link back to it.

Quick Contribute deals cards from these: same-language snippets show how the
outside world spells words ("confirm the standard spelling"), and snippets
in languages a user speaks are offered for translation. Translating one
turns it into an internal Document (source text + translation) and sets
`document_id`, after which it is handled like any other document.

Only short excerpts are stored, always with their URL and licence, so the
card can credit and link the source.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(UTC)


class SourceSnippet(Base):
    __tablename__ = "source_snippets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    language_id = Column(
        UUID(as_uuid=True),
        ForeignKey("languages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content = Column(Text, nullable=False)
    source_url = Column(String(1000), nullable=False)
    source_title = Column(String(500), nullable=False)
    license = Column(String(100), nullable=True)  # e.g. "CC BY-SA 4.0"

    # Set once the snippet has been translated into an internal Document.
    document_id = Column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"), nullable=True
    )
    created_by_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at = Column(DateTime, default=_now, nullable=False)

    language = relationship("Language")
    document = relationship("Document")

    def __repr__(self) -> str:
        return f"<SourceSnippet(id={self.id}, source_url='{self.source_url}')>"
