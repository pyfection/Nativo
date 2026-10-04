"""Add users.is_bot and lexemes.draft_confidence

Support for LLM-drafted word batches: bot accounts are never auto-promoted
to editor, and each drafted suggestion carries a confidence level so
reviewers can batch-approve the safe ones.

Revision ID: c3d4e5f6a7b8
Revises: b7c1d2e3f4a5
Create Date: 2026-09-29 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: str | None = "b7c1d2e3f4a5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_bot", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    op.add_column("lexemes", sa.Column("draft_confidence", sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column("lexemes", "draft_confidence")
    op.drop_column("users", "is_bot")
