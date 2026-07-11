"""
Audio listing + upload endpoints.

Audio recordings attach to WordForms (pronunciation varies per surface form,
not per dictionary headword). Listing is public; upload requires auth.
"""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audio import Audio
from app.models.user import User
from app.models.word import Lexeme, WordForm, word_form_audio
from app.services.auth_service import require_language_edit_permission
from app.utils.file_storage import StorageError, delete_blob, store_audio

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
        None,
        description=(
            "Optional filter — only audio linked to a form whose lexeme is in this language"
        ),
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
        db.query(word_form_audio.c.audio_id).filter(word_form_audio.c.audio_id.in_(audio_ids)).all()
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


class AudioResponse(BaseModel):
    """Shape returned by the upload endpoint."""

    id: UUID
    file_path: str
    file_size: int | None
    duration: int | None
    mime_type: str | None
    word_form_id: UUID | None


@router.post(
    "/upload",
    response_model=AudioResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_audio(
    file: UploadFile = File(..., description="Audio blob (webm/ogg/mp3/wav/flac/m4a)"),
    word_form_id: UUID | None = Form(
        None, description="If provided, the new audio is also linked to this WordForm."
    ),
    duration: int | None = Form(None, description="Optional recorded duration in whole seconds."),
    is_primary: bool = Form(False, description="Mark as the canonical recording for the form."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AudioResponse:
    """Accept a multipart upload, persist it, and optionally link to a WordForm.

    Either creates a standalone Audio row (no `word_form_id`) for later linking
    or — the common path — uploads + links in a single round-trip so the
    frontend can record-and-attach with one button.
    """
    raw = await file.read()
    try:
        url_path, size = store_audio(
            raw_bytes=raw,
            mime_type=file.content_type or "application/octet-stream",
            original_filename=file.filename,
        )
    except StorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audio = Audio(
        file_path=url_path,
        file_size=size,
        mime_type=file.content_type,
        duration=duration,
        uploaded_by_id=current_user.id,
    )
    db.add(audio)
    db.flush()  # so audio.id exists for the association row

    if word_form_id is not None:
        form = db.query(WordForm).filter(WordForm.id == word_form_id).first()
        if form is None:
            raise HTTPException(status_code=404, detail="WordForm not found")
        require_language_edit_permission(db, current_user, form.lexeme.language_id)
        db.execute(
            word_form_audio.insert().values(
                word_form_id=word_form_id,
                audio_id=audio.id,
                is_primary=is_primary,
                created_at=datetime.now(UTC),
            )
        )

    db.commit()
    db.refresh(audio)
    return AudioResponse(
        id=audio.id,
        file_path=audio.file_path,
        file_size=audio.file_size,
        duration=audio.duration,
        mime_type=audio.mime_type,
        word_form_id=word_form_id,
    )


@router.get("/by-form/{form_id}", response_model=list[AudioListItem])
def list_form_audio(
    form_id: UUID,
    db: Session = Depends(get_db),
) -> list[AudioListItem]:
    """List all audio recordings attached to a specific WordForm."""
    audios = (
        db.query(Audio)
        .join(word_form_audio, word_form_audio.c.audio_id == Audio.id)
        .filter(word_form_audio.c.word_form_id == form_id)
        .order_by(Audio.created_at.desc())
        .all()
    )
    if not audios:
        return []

    uploader_ids = {a.uploaded_by_id for a in audios}
    users_by_id: dict[UUID, User] = {
        u.id: u for u in db.query(User).filter(User.id.in_(uploader_ids)).all()
    }
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
            word_count=1,
        )
        for a in audios
    ]


@router.delete("/{audio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_audio(
    audio_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an audio recording (only the uploader or an admin can do this)."""
    audio = db.query(Audio).filter(Audio.id == audio_id).first()
    if audio is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    if audio.uploaded_by_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not allowed to delete this audio")
    # Drop association rows first (no cascade declared here).
    db.execute(word_form_audio.delete().where(word_form_audio.c.audio_id == audio_id))
    file_path = audio.file_path
    db.delete(audio)
    db.commit()
    # Blob cleanup after the row is gone; best-effort by design — an
    # already-missing file must not resurrect the DB row.
    delete_blob(file_path)
    return None
