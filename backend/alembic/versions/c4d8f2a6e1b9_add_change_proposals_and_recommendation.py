"""Change proposals + votes, Lexeme.recommendation, Language threshold

Revision ID: c4d8f2a6e1b9
Revises: c3d4e5f6a7b8
Create Date: 2026-10-04 12:00:00.000000

Collective decisions on published content, starting with "mark this word
preferred / discouraged":

- `lexemes.recommendation` (preferred | neutral | discouraged, default
  neutral) + `lexemes.recommendation_note`. Written only when a proposal is
  accepted.
- `languages.proposal_approval_threshold` (default 2).
- `change_proposals` (generic: type + JSON payload) and `proposal_votes`
  (one vote per user per proposal).
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c4d8f2a6e1b9'
down_revision: str | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_ENUMS = {
    'lexemerecommendation': ('preferred', 'neutral', 'discouraged'),
    'proposaltype': ('set_recommendation',),
    'proposalstatus': ('open', 'accepted', 'rejected', 'withdrawn'),
    'votechoice': ('approve', 'reject'),
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in _ENUMS.items():
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    op.add_column(
        'lexemes',
        sa.Column(
            'recommendation',
            _enum('lexemerecommendation'),
            nullable=False,
            server_default='neutral',
        ),
    )
    op.add_column('lexemes', sa.Column('recommendation_note', sa.Text(), nullable=True))
    op.create_index('ix_lexemes_recommendation', 'lexemes', ['recommendation'])

    op.add_column(
        'languages',
        sa.Column(
            'proposal_approval_threshold', sa.Integer(), nullable=False, server_default='2'
        ),
    )

    op.create_table(
        'change_proposals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'language_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('languages.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'lexeme_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('lexemes.id', ondelete='CASCADE'),
            nullable=True,
        ),
        sa.Column('proposal_type', _enum('proposaltype'), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('status', _enum('proposalstatus'), nullable=False),
        sa.Column(
            'created_by_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_change_proposals_language_id', 'change_proposals', ['language_id'])
    op.create_index('ix_change_proposals_lexeme_id', 'change_proposals', ['lexeme_id'])
    op.create_index('ix_change_proposals_status', 'change_proposals', ['status'])

    op.create_table(
        'proposal_votes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            'proposal_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('change_proposals.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column(
            'user_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
        ),
        sa.Column('choice', _enum('votechoice'), nullable=False),
        sa.Column('comment', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('proposal_id', 'user_id', name='uq_proposal_vote_user'),
    )
    op.create_index('ix_proposal_votes_proposal_id', 'proposal_votes', ['proposal_id'])


def downgrade() -> None:
    op.drop_index('ix_proposal_votes_proposal_id', table_name='proposal_votes')
    op.drop_table('proposal_votes')
    op.drop_index('ix_change_proposals_status', table_name='change_proposals')
    op.drop_index('ix_change_proposals_lexeme_id', table_name='change_proposals')
    op.drop_index('ix_change_proposals_language_id', table_name='change_proposals')
    op.drop_table('change_proposals')
    op.drop_column('languages', 'proposal_approval_threshold')
    op.drop_index('ix_lexemes_recommendation', table_name='lexemes')
    op.drop_column('lexemes', 'recommendation_note')
    op.drop_column('lexemes', 'recommendation')
    bind = op.get_bind()
    for name in reversed(list(_ENUMS)):
        postgresql.ENUM(name=name).drop(bind, checkfirst=True)
