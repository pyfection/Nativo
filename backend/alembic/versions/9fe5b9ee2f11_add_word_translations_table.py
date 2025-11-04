"""add_word_translations_table

Revision ID: 9fe5b9ee2f11
Revises: c737f73cccf6
Create Date: 2025-11-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fe5b9ee2f11'
down_revision: Union[str, None] = 'c737f73cccf6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create word_translations association table
    op.create_table('word_translations',
    sa.Column('word_id', sa.UUID(), nullable=False),
    sa.Column('translation_id', sa.UUID(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('created_by_id', sa.UUID(), nullable=True),
    sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['translation_id'], ['words.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('word_id', 'translation_id')
    )
    
    # Create index for reverse lookups
    op.create_index('ix_word_translations_translation_id', 'word_translations', ['translation_id'])


def downgrade() -> None:
    op.drop_index('ix_word_translations_translation_id', table_name='word_translations')
    op.drop_table('word_translations')

