"""
Audio listing endpoints.

Read-only listing so the Audio stats card and audio page work; upload and
streaming are still out of scope. Audio recordings attach to WordForms
(pronunciation varies per surface form).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.audio import Audio
from app.models.user import User
from app.models.word import Lexeme, WordForm, word_form_audio

router = APIRouter()


class AudioListItem(BaseModel):
    id: UUID
    file_path: str
    file_size: int | None
    duration: int | None
    mime_type: str | None
    uploaded_by_id: UUID
    uploader_username: str | None
    created_at: str
    word_count: int


@router.get("/", response_model=list[AudioListItem])
def list_audio(
    language_id: UUID | None = Query(
        None, description="Optional filter — only audio linked to a form whose lexeme is in this language"
    ),
    skip: int = 0,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[AudioListItem]:
    query = db.query(Audio).order_by(Audio.created_at.desc())

    if language_id is not None:
        query = (
            query.join(word_form_audio, word_form_audio.c.audio_id == Audio.id)
            .join(WordForm, WordForm.id == word_form_audio.c.word_form_id)
            .join(Lexeme, Lexeme.id == WordForm.lexeme_id)
            .filter(Lexeme.language_id == language_id)
            .distinct()
        )

    audios = query.offset(skip).limit(limit).all()
    if not audios:
        return []

    uploader_ids = {a.uploaded_by_id for a in audios}
    users_by_id: dict[UUID, User] = {
        u.id: u for u in db.query(User).filter(User.id.in_(uploader_ids)).all()
    }

    audio_ids = [a.id for a in audios]
    link_rows = (
        db.query(word_form_audio.c.audio_id)
        .filter(word_form_audio.c.audio_id.in_(audio_ids))
        .all()
    )
    word_counts: dict[UUID, int] = {}
    for (aid,) in link_rows:
        word_counts[aid] = word_counts.get(aid, 0) + 1

    return [
        AudioListItem(
            id=a.id,
            file_path=a.file_path,
            file_size=a.file_size,
            duration=a.duration,
            mime_type=a.mime_type,
            uploaded_by_id=a.uploaded_by_id,
            uploader_username=(
                users_by_id[a.uploaded_by_id].username if a.uploaded_by_id in users_by_id else None
            ),
            created_at=a.created_at.isoformat(),
            word_count=word_counts.get(a.id, 0),
        )
        for a in audios
    ]
