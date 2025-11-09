"""
Endpoints for managing links between text content spans and words.
"""
from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_contributor
from app.database import get_db
from app.models.text import Text
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User
from app.schemas.text import (
    TextWordLink as TextWordLinkSchema,
    TextWordLinkCreate,
    TextWordLinkUpdate,
)
from app.services.document_service import suggest_links_for_text

router = APIRouter()


def _get_text_or_404(db: Session, text_id: UUID) -> Text:
    text = db.query(Text).filter(Text.id == text_id).first()
    if not text:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Text not found")
    return text


def _get_link_or_404(db: Session, text_id: UUID, link_id: UUID) -> TextWordLink:
    link = (
        db.query(TextWordLink)
        .filter(TextWordLink.id == link_id, TextWordLink.text_id == text_id)
        .first()
    )
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return link


@router.get(
    "/texts/{text_id}/links",
    response_model=List[TextWordLinkSchema],
)
async def list_text_links(
    text_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve all links for a given text. Requires an authenticated user.
    """
    _get_text_or_404(db, text_id)

    links = (
        db.query(TextWordLink)
        .filter(TextWordLink.text_id == text_id)
        .order_by(TextWordLink.start_char)
        .all()
    )
    return links


@router.post(
    "/texts/{text_id}/links",
    response_model=TextWordLinkSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_text_link(
    text_id: UUID,
    link_data: TextWordLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_contributor),
):
    """
    Create a link between a text span and an existing word.
    """
    _get_text_or_404(db, text_id)

    existing = (
        db.query(TextWordLink)
        .filter(
            TextWordLink.text_id == text_id,
            TextWordLink.start_char == link_data.start_char,
            TextWordLink.end_char == link_data.end_char,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A link already exists for the selected span",
        )

    link = TextWordLink(
        text_id=text_id,
        word_id=link_data.word_id,
        start_char=link_data.start_char,
        end_char=link_data.end_char,
        status=link_data.status,
        notes=link_data.notes,
        created_by_id=current_user.id,
    )

    if link_data.status == TextWordLinkStatus.CONFIRMED:
        link.verified_by_id = current_user.id
        link.verified_at = datetime.utcnow()

    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@router.patch(
    "/texts/{text_id}/links/{link_id}",
    response_model=TextWordLinkSchema,
)
async def update_text_link(
    text_id: UUID,
    link_id: UUID,
    link_update: TextWordLinkUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_contributor),
):
    """
    Update link metadata or verification status.
    """
    link = _get_link_or_404(db, text_id, link_id)

    if link_update.notes is not None:
        link.notes = link_update.notes

    if link_update.word_id is not None:
        link.word_id = link_update.word_id

    if link_update.status is not None:
        link.status = link_update.status
        if link.status == TextWordLinkStatus.CONFIRMED:
            link.verified_by_id = current_user.id
            link.verified_at = datetime.utcnow()
        elif link.status == TextWordLinkStatus.REJECTED:
            link.verified_by_id = current_user.id
            link.verified_at = datetime.utcnow()
        else:
            link.verified_by_id = None
            link.verified_at = None

    db.commit()
    db.refresh(link)
    return link


@router.delete(
    "/texts/{text_id}/links/{link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_text_link(
    text_id: UUID,
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_contributor),
):
    """
    Delete a link or suggestion.
    """
    link = _get_link_or_404(db, text_id, link_id)
    db.delete(link)
    db.commit()
    return None


@router.post(
    "/texts/{text_id}/links/suggest",
    response_model=List[TextWordLinkSchema],
)
async def regenerate_text_link_suggestions(
    text_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_contributor),
):
    """
    Re-run auto-link suggestions for a text, replacing existing suggestions.
    Confirmed or rejected links remain untouched.
    """
    text = _get_text_or_404(db, text_id)
    created_links = suggest_links_for_text(
        db,
        text,
        creator_id=current_user.id,
        replace_existing_suggestions=True,
    )
    db.commit()
    return created_links

