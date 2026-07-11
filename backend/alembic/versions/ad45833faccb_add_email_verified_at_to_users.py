"""Add email_verified_at to users

Set when the user clicks the emailed verification link; null = unverified.

Revision ID: ad45833faccb
Revises: 00e251551ac9
Create Date: 2026-07-11 16:42:30.841369

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'ad45833faccb'
down_revision: Union[str, None] = '00e251551ac9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'email_verified_at')
