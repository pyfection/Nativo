"""Add text_id to audio for narrated texts

Narration recordings attach to a whole Text (word pronunciations keep
using word_form_audio). Deleting the text cascades to its narrations.

Revision ID: 00e251551ac9
Revises: a97f88589491
Create Date: 2026-07-11 15:24:06.473667

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '00e251551ac9'
down_revision: Union[str, None] = 'a97f88589491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audio', sa.Column('text_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_audio_text_id'), 'audio', ['text_id'], unique=False)
    op.create_foreign_key(
        'fk_audio_text_id_texts', 'audio', 'texts', ['text_id'], ['id'], ondelete='CASCADE'
    )


def downgrade() -> None:
    op.drop_constraint('fk_audio_text_id_texts', 'audio', type_='foreignkey')
    op.drop_index(op.f('ix_audio_text_id'), table_name='audio')
    op.drop_column('audio', 'text_id')
