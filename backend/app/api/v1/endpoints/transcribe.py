"""
Speech / IPA → standard spelling (suggest-only).

- POST /transcribe/ipa   — public; IPA in, standard spelling + candidates out.
- POST /transcribe/audio — authenticated; runs the phoneme recogniser first.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database import get_db
from app.limiter import limiter
from app.models.language import Language
from app.models.user import User
from app.schemas.transcription import IpaTranscriptionRequest, TranscriptionResult
from app.services import transcription_service
from app.utils.phoneme_recognizer import RecognizerUnavailableError

router = APIRouter()

MAX_AUDIO_BYTES = 10 * 1024 * 1024


def _require_language(db: Session, language_id: UUID) -> None:
    if not db.query(Language).filter(Language.id == language_id).first():
        raise HTTPException(status_code=404, detail="Language not found")


@router.post("/ipa", response_model=TranscriptionResult)
@limiter.limit("60/minute")
def transcribe_ipa(
    request: Request,
    data: IpaTranscriptionRequest,
    db: Session = Depends(get_db),
):
    _require_language(db, data.language_id)
    return transcription_service.transcribe_ipa(db, data.language_id, data.ipa)


# Sync `def` so FastAPI runs the (CPU-heavy) model in its threadpool.
@router.post("/audio", response_model=TranscriptionResult)
@limiter.limit("10/minute")
def transcribe_audio(
    request: Request,
    language_id: UUID = Form(...),
    file: UploadFile = File(..., description="Audio clip (webm/ogg/mp3/wav/m4a), max 15 s"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    _require_language(db, language_id)
    audio = file.file.read(MAX_AUDIO_BYTES + 1)
    if len(audio) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large (max 10 MB)")
    try:
        return transcription_service.transcribe_audio(db, language_id, audio)
    except RecognizerUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
