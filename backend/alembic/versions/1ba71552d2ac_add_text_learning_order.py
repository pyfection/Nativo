"""add Text.learning_order

Editor pin for the guided learning path: pinned texts lead the sequence
(ascending) before the computed ordering; null means computed placement.

Hand-checked from autogenerate: unrelated drift (languages.managed
nullability, stale ix_documents_* index names on texts) was dropped —
this migration only adds the column.

Revision ID: 1ba71552d2ac
Revises: cb64f4dd8bec
Create Date: 2026-07-11 00:02:14.282830

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '1ba71552d2ac'
down_revision: str | None = 'cb64f4dd8bec'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('texts', sa.Column('learning_order', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('texts', 'learning_order')
