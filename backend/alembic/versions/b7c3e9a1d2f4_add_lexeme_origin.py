"""Add Lexeme.origin + borrowed_from_language_id (loanwords)

Revision ID: b7c3e9a1d2f4
Revises: ad45833faccb
Create Date: 2026-10-04 00:00:00.000000

Words speakers actually use are recorded in their language even when
borrowed (e.g. German words for modern concepts in Bavarian). These columns
mark where a lexeme came from:

- `lexemes.origin` (native | loanword | calque | neologism), nullable =
  not yet classified.
- `lexemes.borrowed_from_language_id` (nullable FK, ON DELETE SET NULL).
- `loan_variant` value on `synonymnuance`, for linking a loanword to its
  native alternative.
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b7c3e9a1d2f4'
down_revision: str | None = 'ad45833faccb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    lexeme_origin = postgresql.ENUM(
        'native', 'loanword', 'calque', 'neologism', name='lexemeorigin'
    )
    lexeme_origin.create(op.get_bind(), checkfirst=True)
    op.add_column(
        'lexemes',
        sa.Column(
            'origin',
            postgresql.ENUM(name='lexemeorigin', create_type=False),
            nullable=True,
        ),
    )
    op.create_index('ix_lexemes_origin', 'lexemes', ['origin'])

    op.add_column(
        'lexemes',
        sa.Column(
            'borrowed_from_language_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                'languages.id',
                ondelete='SET NULL',
                name='fk_lexemes_borrowed_from_language_id_languages',
            ),
            nullable=True,
        ),
    )
    op.create_index(
        'ix_lexemes_borrowed_from_language_id', 'lexemes', ['borrowed_from_language_id']
    )

    op.execute("ALTER TYPE synonymnuance ADD VALUE IF NOT EXISTS 'loan_variant'")


def downgrade() -> None:
    # Postgres can't drop a single enum value; remap any loan_variant rows and
    # leave the label in place (harmless, and re-added idempotently above).
    op.execute(
        "UPDATE lexeme_synonyms SET nuance = 'other' WHERE nuance = 'loan_variant'"
    )
    op.drop_index('ix_lexemes_borrowed_from_language_id', table_name='lexemes')
    op.drop_column('lexemes', 'borrowed_from_language_id')
    op.drop_index('ix_lexemes_origin', table_name='lexemes')
    op.drop_column('lexemes', 'origin')
    postgresql.ENUM(name='lexemeorigin').drop(op.get_bind(), checkfirst=True)
