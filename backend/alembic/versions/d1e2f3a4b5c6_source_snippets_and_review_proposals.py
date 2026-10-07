"""Source snippets + reviewed proposal types

Revision ID: d1e2f3a4b5c6
Revises: b7c8d9e0f1a2
Create Date: 2026-10-08 00:00:00.000000

- `source_snippets`: sentences from outside sources (with URL + licence) that
  Quick Contribute turns into spelling-confirmation and translation cards.
- `proposaltype` gains `add_spelling_variant` and `add_translation`: a
  suggester's addition to an existing published entry, settled by one
  reviewer.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "d1e2f3a4b5c6"
down_revision: str | None = "b7c8d9e0f1a2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Postgres 12+ allows ADD VALUE inside the migration's transaction.
    op.execute("ALTER TYPE proposaltype ADD VALUE IF NOT EXISTS 'add_spelling_variant'")
    op.execute("ALTER TYPE proposaltype ADD VALUE IF NOT EXISTS 'add_translation'")

    op.create_table(
        "source_snippets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=False),
        sa.Column("source_title", sa.String(length=500), nullable=False),
        sa.Column("license", sa.String(length=100), nullable=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_source_snippets_language_id", "source_snippets", ["language_id"])


def downgrade() -> None:
    op.drop_index("ix_source_snippets_language_id", table_name="source_snippets")
    op.drop_table("source_snippets")
    # Postgres can't drop enum values; delete proposals that use them so the
    # remaining rows are valid for the older code.
    op.execute(
        "DELETE FROM change_proposals"
        " WHERE proposal_type IN ('add_spelling_variant', 'add_translation')"
    )
