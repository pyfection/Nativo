"""Add status to texts for the suggester tier

Non-editors can now suggest documents/translations; those Texts land as
`pending_review` and only show up publicly once approved. Existing rows
(and editor-created texts) stay `published` via the server default.

Revision ID: a97f88589491
Revises: 1ba71552d2ac
Create Date: 2026-07-11 14:49:31.279292

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a97f88589491'
down_revision: Union[str, None] = '1ba71552d2ac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    text_status = postgresql.ENUM(
        "pending_review", "published", "archived", name="textstatus"
    )
    text_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "texts",
        sa.Column(
            "status",
            sa.Enum(
                "pending_review", "published", "archived",
                name="textstatus", create_type=False,
            ),
            nullable=False,
            server_default="published",
        ),
    )
    op.create_index(op.f("ix_texts_status"), "texts", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_texts_status"), table_name="texts")
    op.drop_column("texts", "status")
    op.execute("DROP TYPE IF EXISTS textstatus")
