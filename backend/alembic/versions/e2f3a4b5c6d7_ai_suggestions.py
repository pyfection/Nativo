"""AI suggestions cache

Revision ID: e2f3a4b5c6d7
Revises: d1e2f3a4b5c6
Create Date: 2026-10-08 12:00:00.000000

- `ai_suggestions`: one stored AI answer (meaning, part of speech, spelling)
  per Quick Contribute word card, so each unknown word costs one call.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "e2f3a4b5c6d7"
down_revision: str | None = "d1e2f3a4b5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("key", sa.String(length=255), nullable=False),
        sa.Column(
            "gloss_language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "language_id", "kind", "key", "gloss_language_id", name="uq_ai_suggestions_card"
        ),
    )
    op.create_index("ix_ai_suggestions_language_id", "ai_suggestions", ["language_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_suggestions_language_id", table_name="ai_suggestions")
    op.drop_table("ai_suggestions")
