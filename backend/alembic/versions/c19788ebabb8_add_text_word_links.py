"""add text word links

Revision ID: c19788ebabb8
Revises: 4a08d643a50c
Create Date: 2025-11-09 14:20:59.023630

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c19788ebabb8'
down_revision: Union[str, None] = '4a08d643a50c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    textwordlinkstatus = sa.Enum(
        "suggested",
        "confirmed",
        "rejected",
        name="textwordlinkstatus",
    )
    textwordlinkstatus.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "text_word_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("text_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("word_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=False),
        sa.Column("end_char", sa.Integer(), nullable=False),
        sa.Column("status", textwordlinkstatus, nullable=False, server_default="suggested"),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("verified_by_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
            server_onupdate=sa.func.now(),
        ),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["text_id"], ["texts.id"]),
        sa.ForeignKeyConstraint(["verified_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["word_id"], ["words.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_text_word_links_text_id"), "text_word_links", ["text_id"], unique=False)
    op.create_index(op.f("ix_text_word_links_word_id"), "text_word_links", ["word_id"], unique=False)
    op.create_index(op.f("ix_text_word_links_start_end"), "text_word_links", ["start_char", "end_char"], unique=False)
    op.create_unique_constraint(
        "uq_text_word_links_unique_span",
        "text_word_links",
        ["text_id", "start_char", "end_char"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_text_word_links_unique_span", "text_word_links", type_="unique")
    op.drop_index(op.f("ix_text_word_links_start_end"), table_name="text_word_links")
    op.drop_index(op.f("ix_text_word_links_word_id"), table_name="text_word_links")
    op.drop_index(op.f("ix_text_word_links_text_id"), table_name="text_word_links")
    op.drop_table("text_word_links")

    textwordlinkstatus = sa.Enum(
        "suggested",
        "confirmed",
        "rejected",
        name="textwordlinkstatus",
    )
    textwordlinkstatus.drop(op.get_bind(), checkfirst=True)

