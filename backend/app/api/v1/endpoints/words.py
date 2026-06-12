"""
Lexeme + WordForm endpoints (formerly /words).

A Lexeme is the dictionary entry; WordForms are its surface forms. The
public URL prefix stays at `/words` so older clients keep working — the
underlying resource is the Lexeme.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import require_admin, require_contributor, require_native_speaker
from app.database import get_db
from app.limiter import limiter
from app.models.user import User
from app.models.word import Lexeme, LexemeStatus, WordForm
from app.schemas.word import (
    AntonymCreate,
    AntonymLink,
    Lexeme as LexemeSchema,
    LexemeCreate,
    LexemeListItem,
    LexemeUpdate,
    LexemeWithForms,
    RhymeMatch,
    SynonymCreate,
    SynonymLink,
    TranslationCreate,
    TranslationLink,
    TranslationUpdate,
    WordForm as WordFormSchema,
    WordFormCreate,
    WordFormUpdate,
)
from app.services import lexeme_service
from app.services.auth_service import require_resource_owner

router = APIRouter()


# ---------------------------------------------------------------------------
# Lexeme CRUD
# ---------------------------------------------------------------------------


@router.get("/", response_model=list[LexemeListItem])
async def list_lexemes(
    skip: int = 0,
    limit: int = 100,
    language_id: UUID | None = None,
    status_filter: LexemeStatus | None = None,
    include_all_statuses: bool = False,
    db: Session = Depends(get_db),
):
    query = db.query(Lexeme)
    if language_id:
        query = query.filter(Lexeme.language_id == language_id)
    if status_filter:
        query = query.filter(Lexeme.status == status_filter)
    elif not include_all_statuses:
        query = query.filter(Lexeme.status == LexemeStatus.PUBLISHED)
    return query.offset(skip).limit(limit).all()


@router.get("/search", response_model=list[LexemeWithForms])
@limiter.limit("30/minute")
async def search_lexemes(
    request: Request,
    q: str,
    language_ids: str | None = None,
    include_unpublished: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Full-ish text search over lemma + any WordForm's `form` / `romanization`.
    """
    query = db.query(Lexeme).distinct()
    if include_unpublished:
        query = query.filter(
            Lexeme.status.in_(
                [LexemeStatus.PUBLISHED, LexemeStatus.PENDING_REVIEW, LexemeStatus.DRAFT]
            )
        )
    else:
        query = query.filter(Lexeme.status == LexemeStatus.PUBLISHED)

    if q:
        like = f"%{q}%"
        query = query.outerjoin(WordForm, WordForm.lexeme_id == Lexeme.id).filter(
            or_(
                Lexeme.lemma.ilike(like),
                WordForm.form.ilike(like),
                WordForm.romanization.ilike(like),
            )
        )

    if language_ids:
        try:
            ids = [UUID(s.strip()) for s in language_ids.split(",") if s.strip()]
            if ids:
                query = query.filter(Lexeme.language_id.in_(ids))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid language ID format")

    return query.offset(skip).limit(limit).all()


@router.get("/{lexeme_id}", response_model=LexemeWithForms)
async def get_lexeme(lexeme_id: UUID, db: Session = Depends(get_db)):
    lexeme = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    if not lexeme:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    return lexeme


@router.post("/", response_model=LexemeWithForms, status_code=status.HTTP_201_CREATED)
async def create_lexeme(
    data: LexemeCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    return lexeme_service.create_lexeme(db, data, creator_id=current_user.id)


@router.put("/{lexeme_id}", response_model=LexemeSchema)
async def update_lexeme(
    lexeme_id: UUID,
    data: LexemeUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    lexeme = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    if not lexeme:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    require_resource_owner(current_user, lexeme.created_by_id)
    return lexeme_service.update_lexeme(db, lexeme, data)


@router.delete("/{lexeme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lexeme(
    lexeme_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    lexeme = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    if not lexeme:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    db.delete(lexeme)
    db.commit()
    return None


@router.post("/{lexeme_id}/verify", response_model=LexemeSchema)
async def verify_lexeme(
    lexeme_id: UUID,
    current_user: User = Depends(require_native_speaker),
    db: Session = Depends(get_db),
):
    lexeme = db.query(Lexeme).filter(Lexeme.id == lexeme_id).first()
    if not lexeme:
        raise HTTPException(status_code=404, detail="Lexeme not found")
    lexeme.is_verified = True
    lexeme.verified_by_id = current_user.id
    lexeme.status = LexemeStatus.PUBLISHED
    db.commit()
    db.refresh(lexeme)
    return lexeme


# ---------------------------------------------------------------------------
# WordForm CRUD (nested under lexeme)
# ---------------------------------------------------------------------------


@router.get("/{lexeme_id}/forms", response_model=list[WordFormSchema])
async def list_forms(lexeme_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(WordForm)
        .filter(WordForm.lexeme_id == lexeme_id)
        .order_by(WordForm.is_lemma.desc(), WordForm.form.asc())
        .all()
    )


@router.post(
    "/{lexeme_id}/forms",
    response_model=WordFormSchema,
    status_code=status.HTTP_201_CREATED,
)
async def add_form(
    lexeme_id: UUID,
    data: WordFormCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    if data.lexeme_id != lexeme_id:
        raise HTTPException(status_code=400, detail="Path lexeme_id does not match payload")
    return lexeme_service.create_word_form(db, data)


@router.put("/forms/{form_id}", response_model=WordFormSchema)
async def update_form(
    form_id: UUID,
    data: WordFormUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    word_form = db.query(WordForm).filter(WordForm.id == form_id).first()
    if not word_form:
        raise HTTPException(status_code=404, detail="WordForm not found")
    require_resource_owner(current_user, word_form.lexeme.created_by_id)
    return lexeme_service.update_word_form(db, word_form, data)


@router.delete("/forms/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    word_form = db.query(WordForm).filter(WordForm.id == form_id).first()
    if not word_form:
        raise HTTPException(status_code=404, detail="WordForm not found")
    require_resource_owner(current_user, word_form.lexeme.created_by_id)
    if word_form.is_lemma:
        raise HTTPException(
            status_code=400,
            detail="Refusing to delete the canonical lemma form — promote another form first",
        )
    db.delete(word_form)
    db.commit()
    return None


# ---------------------------------------------------------------------------
# Relations
# ---------------------------------------------------------------------------


@router.get("/{lexeme_id}/synonyms", response_model=list[SynonymLink])
async def list_synonyms(lexeme_id: UUID, db: Session = Depends(get_db)):
    return lexeme_service.list_synonyms(db, lexeme_id)


@router.post(
    "/{lexeme_id}/synonyms",
    response_model=SynonymLink,
    status_code=status.HTTP_201_CREATED,
)
async def add_synonym(
    lexeme_id: UUID,
    data: SynonymCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    return lexeme_service.add_synonym(db, lexeme_id, data)


@router.delete(
    "/{lexeme_id}/synonyms/{other_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_synonym(
    lexeme_id: UUID,
    other_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    lexeme_service.remove_synonym(db, lexeme_id, other_id)
    return None


@router.get("/{lexeme_id}/antonyms", response_model=list[AntonymLink])
async def list_antonyms(lexeme_id: UUID, db: Session = Depends(get_db)):
    return lexeme_service.list_antonyms(db, lexeme_id)


@router.post(
    "/{lexeme_id}/antonyms",
    response_model=AntonymLink,
    status_code=status.HTTP_201_CREATED,
)
async def add_antonym(
    lexeme_id: UUID,
    data: AntonymCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    return lexeme_service.add_antonym(db, lexeme_id, data)


@router.delete(
    "/{lexeme_id}/antonyms/{other_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_antonym(
    lexeme_id: UUID,
    other_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    lexeme_service.remove_antonym(db, lexeme_id, other_id)
    return None


@router.get("/{lexeme_id}/translations", response_model=list[TranslationLink])
async def list_translations(lexeme_id: UUID, db: Session = Depends(get_db)):
    return lexeme_service.list_translations(db, lexeme_id)


@router.post(
    "/{lexeme_id}/translations",
    response_model=TranslationLink,
    status_code=status.HTTP_201_CREATED,
)
async def add_translation(
    lexeme_id: UUID,
    data: TranslationCreate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    return lexeme_service.add_translation(db, lexeme_id, data, creator_id=current_user.id)


@router.put(
    "/{lexeme_id}/translations/{other_id}", response_model=TranslationLink
)
async def update_translation(
    lexeme_id: UUID,
    other_id: UUID,
    data: TranslationUpdate,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    return lexeme_service.update_translation_notes(db, lexeme_id, other_id, data.notes)


@router.delete(
    "/{lexeme_id}/translations/{other_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_translation(
    lexeme_id: UUID,
    other_id: UUID,
    current_user: User = Depends(require_contributor),
    db: Session = Depends(get_db),
):
    lexeme_service.remove_translation(db, lexeme_id, other_id)
    return None


# ---------------------------------------------------------------------------
# Rhymes
# ---------------------------------------------------------------------------


@router.get("/forms/{form_id}/rhymes", response_model=list[RhymeMatch])
async def find_rhymes(
    form_id: UUID,
    near: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    forms = lexeme_service.find_rhymes(db, form_id, near=near, limit=limit)
    out: list[RhymeMatch] = []
    for wf in forms:
        out.append(
            RhymeMatch(
                word_form_id=wf.id,
                lexeme_id=wf.lexeme_id,
                form=wf.form,
                lemma=wf.lexeme.lemma,
                ipa_pronunciation=wf.ipa_pronunciation,
                language_id=wf.lexeme.language_id,
            )
        )
    return out
