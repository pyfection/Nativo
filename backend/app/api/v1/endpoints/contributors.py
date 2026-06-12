"""
Contributors endpoint — list users with their contribution stats for a
specific language (or platform-wide).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.text import Text
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.word import Lexeme

router = APIRouter()


class ContributorItem(BaseModel):
    id: UUID
    username: str
    role: str
    proficiency_level: str | None  # null if user has no UserLanguage row for this language
    word_count: int
    text_count: int


@router.get("/", response_model=list[ContributorItem])
def list_contributors(
    language_id: UUID | None = Query(
        None, description="Optional — limit to users active in this language"
    ),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[ContributorItem]:
    """
    A user counts as a contributor for a language if any of:
      - has a UserLanguage row for that language
      - has created at least one Lexeme in that language
      - has created at least one Text in that language

    Without `language_id`, returns any user who has created at least one
    word or text platform-wide.

    Ordered by (word_count + text_count) descending.
    """
    if language_id is not None:
        ul_user_ids = (
            db.query(UserLanguage.user_id)
            .filter(UserLanguage.language_id == language_id)
            .distinct()
        )
        word_user_ids = (
            db.query(Lexeme.created_by_id).filter(Lexeme.language_id == language_id).distinct()
        )
        text_user_ids = (
            db.query(Text.created_by_id).filter(Text.language_id == language_id).distinct()
        )
        users_query = db.query(User).filter(
            User.id.in_(ul_user_ids) | User.id.in_(word_user_ids) | User.id.in_(text_user_ids)
        )
    else:
        word_user_ids = db.query(Lexeme.created_by_id).distinct()
        text_user_ids = db.query(Text.created_by_id).distinct()
        users_query = db.query(User).filter(User.id.in_(word_user_ids) | User.id.in_(text_user_ids))

    users = users_query.limit(limit * 2).all()  # over-fetch; sort below
    if not users:
        return []

    user_ids = [u.id for u in users]

    # Bulk word counts per user
    word_count_query = db.query(Lexeme.created_by_id, func.count(Lexeme.id)).filter(
        Lexeme.created_by_id.in_(user_ids)
    )
    if language_id is not None:
        word_count_query = word_count_query.filter(Lexeme.language_id == language_id)
    word_counts: dict[UUID, int] = dict(word_count_query.group_by(Lexeme.created_by_id).all())

    # Bulk text counts per user
    text_count_query = db.query(Text.created_by_id, func.count(Text.id)).filter(
        Text.created_by_id.in_(user_ids)
    )
    if language_id is not None:
        text_count_query = text_count_query.filter(Text.language_id == language_id)
    text_counts: dict[UUID, int] = dict(text_count_query.group_by(Text.created_by_id).all())

    # Proficiencies (only relevant when filtered by language)
    proficiency_by_user: dict[UUID, str] = {}
    if language_id is not None:
        proficiency_by_user = dict(
            db.query(UserLanguage.user_id, UserLanguage.proficiency_level)
            .filter(UserLanguage.language_id == language_id, UserLanguage.user_id.in_(user_ids))
            .all()
        )

    items: list[ContributorItem] = [
        ContributorItem(
            id=u.id,
            username=u.username,
            role=u.role.value if hasattr(u.role, "value") else str(u.role),
            proficiency_level=(
                proficiency_by_user[u.id].value
                if u.id in proficiency_by_user and hasattr(proficiency_by_user[u.id], "value")
                else (str(proficiency_by_user[u.id]) if u.id in proficiency_by_user else None)
            ),
            word_count=word_counts.get(u.id, 0),
            text_count=text_counts.get(u.id, 0),
        )
        for u in users
    ]
    items.sort(key=lambda c: (c.word_count + c.text_count, c.username), reverse=True)
    return items[:limit]
