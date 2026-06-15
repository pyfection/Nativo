import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Text as TextType
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class DocumentType(str, enum.Enum):
    """Types of documents/texts"""

    # Full documents
    STORY = "story"
    HISTORICAL_RECORD = "historical_record"
    BOOK = "book"
    ARTICLE = "article"
    TRANSCRIPTION = "transcription"
    WRITING_STANDARD = "writing_standard"  # Orthography / writing-system reference

    # Text snippets
    DEFINITION = "definition"
    LITERAL_TRANSLATION = "literal_translation"
    CONTEXT_NOTE = "context_note"
    USAGE_EXAMPLE = "usage_example"
    ETYMOLOGY = "etymology"
    CULTURAL_SIGNIFICANCE = "cultural_significance"
    TRANSLATION = "translation"
    NOTE = "note"

    OTHER = "other"


class TextFormat(str, enum.Enum):
    """How a Text.content should be rendered to the user.

    `plain` is the default — paragraphs separated by line breaks, no inline
    formatting. `markdown` is used for structured Texts (notably writing
    standards) so headings, lists, and tables render properly.
    """

    PLAIN = "plain"
    MARKDOWN = "markdown"


class Text(Base):
    """
    Text model for storing content in different languages.

    A Text contains the actual content and belongs to a Document.
    Multiple Texts can belong to the same Document (for translations).

    Can be:
    - Full texts (stories, historical records, books)
    - Small snippets (definitions, etymology, cultural notes)
    - Everything in between

    Words in the content can be linked to Word records via word_texts.
    """

    __tablename__ = "texts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title = Column(String(500), nullable=False)
    content = Column(TextType, nullable=False)
    document_type = Column(SQLEnum(DocumentType), nullable=False, index=True)
    # How the content should be rendered. Most Texts are plain prose; writing
    # standards and any future structured Texts use markdown so headings,
    # lists and tables render properly. values_callable: send the lowercase
    # `.value` so it matches the Postgres enum labels created by Alembic
    # (same pattern as lexemestatus / textwordlinkstatus).
    format = Column(
        SQLEnum(
            TextFormat,
            name="textformat",
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=TextFormat.PLAIN,
        server_default=TextFormat.PLAIN.value,
    )

    # Language of the content itself
    language_id = Column(UUID(as_uuid=True), ForeignKey("languages.id"), nullable=True, index=True)

    # Link to parent Document (nullable for migration purposes)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=True, index=True)

    # Flag to mark primary/original text
    is_primary = Column(Boolean, default=False, nullable=False)

    source = Column(String(500), nullable=True)  # Origin/citation
    notes = Column(TextType, nullable=True)  # Internal notes

    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    language = relationship("Language", back_populates="texts")
    document = relationship("Document", back_populates="texts")
    created_by = relationship("User")
    # Lexemes whose definition / usage example / context note this Text fills.
    linked_lexemes = relationship(
        "Lexeme",
        secondary="lexeme_texts",
        back_populates="texts",
        viewonly=True,
    )
    word_links = relationship(
        "TextWordLink",
        back_populates="text",
        cascade="all, delete-orphan",
        primaryjoin="Text.id==TextWordLink.text_id",
        order_by="TextWordLink.start_char",
    )

    def __repr__(self):
        return f"<Text(id={self.id}, title='{self.title}', type={self.document_type}, language_id={self.language_id})>"
