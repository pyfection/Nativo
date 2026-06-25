"""add spelling variants

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-06-25 00:00:00.000000

Adds `spelling_variants`: alternative, non-standard spellings that map back to
the WordForm whose `form` is the standard. Lets the platform resolve "how is
this properly written?" and suggest corrections across documents written in a
non-standardised orthography.

`normalized` is the case/diacritic-folded match key (single-equality lookup,
same idea as WordForm.rhyme_key). A variant is unique per (word_form, variant).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: str | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "spelling_variants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("word_form_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("variant", sa.String(length=255), nullable=False),
        sa.Column("normalized", sa.String(length=255), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["word_form_id"], ["word_forms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("word_form_id", "variant", name="uq_spelling_variants_form_variant"),
    )
    op.create_index(
        op.f("ix_spelling_variants_word_form_id"),
        "spelling_variants",
        ["word_form_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_spelling_variants_variant"), "spelling_variants", ["variant"], unique=False
    )
    op.create_index(
        op.f("ix_spelling_variants_normalized"), "spelling_variants", ["normalized"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_spelling_variants_normalized"), table_name="spelling_variants")
    op.drop_index(op.f("ix_spelling_variants_variant"), table_name="spelling_variants")
    op.drop_index(op.f("ix_spelling_variants_word_form_id"), table_name="spelling_variants")
    op.drop_table("spelling_variants")
