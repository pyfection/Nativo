"""Writing standard document + Text.format

Revision ID: f1a2b3c4d5e6
Revises: e9f1a2b3c4d5
Create Date: 2026-06-15 00:00:00.000000

Two related changes that together let a Language designate one Document as
its canonical writing-standard reference:

- Adds `Text.format` (plain | markdown) so structured Texts can render
  headings, lists and tables. Default `plain` so every existing row stays
  rendered the same way.
- Adds `Language.writing_standard_document_id` (nullable FK with ON DELETE
  SET NULL) so admins can promote any Document to be the language's
  official writing standard.
- Adds `writing_standard` value to the `documenttype` enum so the type
  picker on /documents/add can mark a Document as a writing standard.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f1a2b3c4d5e6"
down_revision: str | None = "e9f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---- Text.format ----
    text_format = postgresql.ENUM("plain", "markdown", name="textformat")
    text_format.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "texts",
        sa.Column(
            "format",
            sa.Enum("plain", "markdown", name="textformat", create_type=False),
            nullable=False,
            server_default="plain",
        ),
    )

    # ---- DocumentType.WRITING_STANDARD ----
    # Postgres won't let us add an enum value inside a transaction in older
    # versions; modern Postgres (we're on 17) handles it fine.
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'WRITING_STANDARD'")

    # ---- Language.writing_standard_document_id ----
    op.add_column(
        "languages",
        sa.Column(
            "writing_standard_document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("languages", "writing_standard_document_id")
    op.drop_column("texts", "format")
    op.execute("DROP TYPE IF EXISTS textformat")
    # We cannot easily remove a single enum value from documenttype, so we
    # leave WRITING_STANDARD in place on downgrade.
