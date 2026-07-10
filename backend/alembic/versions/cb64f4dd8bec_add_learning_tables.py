"""add learning tables

Per-user learning state for the guided reading path:
- user_lexeme_knowledge: implicit 0-4 familiarity score per lexeme
- user_text_progress: completed readings with a difficulty verdict

Hand-checked from autogenerate: unrelated schema drift the comparison also
surfaced (languages.managed nullability, stale ix_documents_* index names on
texts left over from the document->text rename) was deliberately dropped —
this migration only adds the two tables.

Revision ID: cb64f4dd8bec
Revises: a1b2c3d4e5f6
Create Date: 2026-07-10 23:43:30.748002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb64f4dd8bec'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'user_lexeme_knowledge',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('lexeme_id', sa.UUID(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['lexeme_id'], ['lexemes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'lexeme_id'),
    )
    op.create_table(
        'user_text_progress',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('text_id', sa.UUID(), nullable=False),
        sa.Column(
            'difficulty_rating',
            sa.Enum('easy', 'just_right', 'challenging', 'too_hard', name='difficultyrating'),
            nullable=False,
        ),
        sa.Column('completed_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['text_id'], ['texts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'text_id'),
    )


def downgrade() -> None:
    op.drop_table('user_text_progress')
    op.drop_table('user_lexeme_knowledge')
    sa.Enum(name='difficultyrating').drop(op.get_bind(), checkfirst=True)
