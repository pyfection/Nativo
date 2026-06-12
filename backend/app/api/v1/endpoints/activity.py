"""
Recent activity feed for a language.

Aggregates events from a few sources (new words, new texts, new joins) into
a single chronological feed.
"""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.limiter import limiter
from app.models.text import Text
from app.models.user import User
from app.models.user_language import UserLanguage
from app.models.word import Lexeme

router = APIRouter()


ActivityType = Literal["word_added", "text_added", "contributor_joined"]


class ActivityItem(BaseModel):
    type: ActivityType
    timestamp: str
    actor: str | None  # username
    summary: str  # short, ready-to-render line


@router.get("/", response_model=list[ActivityItem])
@limiter.limit("30/minute")
def get_activity(
    request: Request,
    language_id: UUID = Query(..., description="Restrict feed to this language"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> list[ActivityItem]:
    """
    Return up to `limit` most recent activity events for the given language.

    Sources:
    - Word created in this language.
    - Text created in this language.
    - UserLanguage created for this language ("contributor joined").
    """
    # Pull a small over-fetch from each source then merge + sort.
    over = max(limit * 2, 20)

    recent_words = (
        db.query(Lexeme)
        .filter(Lexeme.language_id == language_id)
        .order_by(Lexeme.created_at.desc())
        .limit(over)
        .all()
    )
    recent_texts = (
        db.query(Text)
        .filter(Text.language_id == language_id)
        .order_by(Text.created_at.desc())
        .limit(over)
        .all()
    )
    recent_joins = (
        db.query(UserLanguage)
        .filter(UserLanguage.language_id == language_id)
        .order_by(UserLanguage.created_at.desc())
        .limit(over)
        .all()
    )

    # Hydrate user lookups in bulk so we don't N+1.
    user_ids: set[UUID] = set()
    user_ids.update(w.created_by_id for w in recent_words if w.created_by_id)
    user_ids.update(t.created_by_id for t in recent_texts if t.created_by_id)
    user_ids.update(j.user_id for j in recent_joins)
    users_by_id: dict[UUID, User] = {}
    if user_ids:
        users_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(user_ids)).all()}

    def actor_name(user_id: UUID | None) -> str | None:
        if not user_id:
            return None
        u = users_by_id.get(user_id)
        return u.username if u else None

    items: list[ActivityItem] = []
    for w in recent_words:
        actor = actor_name(w.created_by_id)
        items.append(
            ActivityItem(
                type="word_added",
                timestamp=w.created_at.isoformat(),
                actor=actor,
                summary=f'Word added: "{w.lemma}"',
            )
        )
    for t in recent_texts:
        actor = actor_name(t.created_by_id)
        items.append(
            ActivityItem(
                type="text_added",
                timestamp=t.created_at.isoformat(),
                actor=actor,
                summary=f'Document added: "{t.title}"',
            )
        )
    for j in recent_joins:
        actor = actor_name(j.user_id)
        items.append(
            ActivityItem(
                type="contributor_joined",
                timestamp=j.created_at.isoformat(),
                actor=actor,
                summary=f"{actor or 'A contributor'} joined ({j.proficiency_level.value})",
            )
        )

    items.sort(key=lambda i: i.timestamp, reverse=True)
    return items[:limit]
