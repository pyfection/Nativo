"""Keep accents in spelling_variants.normalized

Revision ID: b7c8d9e0f1a2
Revises: c3d4e5f6a7b8
Create Date: 2026-10-03 00:00:00.000000

`fold_for_match` no longer strips accents (they are contrastive in the Bavarian
standard: ia ≠ iá), so recompute the stored match key for existing variants.
The fold is inlined so this migration doesn't change if the app code does.
"""

import unicodedata
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c8d9e0f1a2"
down_revision: str | None = "c3d4e5f6a7b8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _keep_accents(value: str) -> str:
    return unicodedata.normalize("NFC", (value or "").casefold())


def _strip_accents(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value or "")
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn").casefold()


def _recompute(fold) -> None:
    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, variant FROM spelling_variants")).fetchall()
    for row_id, variant in rows:
        conn.execute(
            sa.text("UPDATE spelling_variants SET normalized = :n WHERE id = :id"),
            {"n": fold(variant), "id": row_id},
        )


def upgrade() -> None:
    _recompute(_keep_accents)


def downgrade() -> None:
    _recompute(_strip_accents)
