"""add_managed_field_to_language

Revision ID: 33151565d1c2
Revises: c737f73cccf6
Create Date: 2025-11-03 00:07:39.558853

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '33151565d1c2'
down_revision: Union[str, None] = 'c737f73cccf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add managed column to languages table with default False
    # SQLite doesn't support ALTER COLUMN, so we add it with server_default
    op.add_column('languages', sa.Column('managed', sa.Boolean(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove managed column from languages table
    op.drop_column('languages', 'managed')

