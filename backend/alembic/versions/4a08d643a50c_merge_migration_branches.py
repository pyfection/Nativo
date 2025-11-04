"""merge_migration_branches

Revision ID: 4a08d643a50c
Revises: 9fe5b9ee2f11, d4e5f6g7h8i9
Create Date: 2025-11-04 18:31:26.346114

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a08d643a50c'
down_revision: Union[str, None] = ('9fe5b9ee2f11', 'd4e5f6g7h8i9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

