"""
Change proposals: collective, auditable decisions on published content.

Flow: an editor proposes (their own approval is recorded with it), members
with edit or verify rights on the language vote, and the proposal resolves
as soon as either side reaches the language's `proposal_approval_threshold`:

- ACCEPTED when approvals >= threshold and nobody objects — the change is
  applied in the same transaction;
- REJECTED when rejections >= threshold.

An open objection blocks acceptance until it is withdrawn (votes can be
changed) or enough people object to reject. Admins vote like anyone else;
there is no override.

Additions from the suggester tier to existing entries (a spelling variant, a
translation link — REVIEWED_TYPES) are factual rather than prescriptive, so
they skip the vote: one reviewer with verify rights accepts or rejects them.
A spelling variant proposed from a text card (`fix_texts`) also corrects the
old spelling in the language's texts when accepted.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, distinct, func, insert, select
from sqlalchemy.orm import Session

from app.models.change_proposal import (
    REVIEWED_TYPES,
    ChangeProposal,
    ProposalStatus,
    ProposalType,
    ProposalVote,
    VoteChoice,
)
from app.models.language import Language
from app.models.location import Location
from app.models.text_word_link import TextWordLink, TextWordLinkStatus
from app.models.user import User
from app.models.word import (
    Lexeme,
    LexemeRecommendation,
    SpellingVariant,
    WordForm,
    lexeme_translations,
    word_form_audio,
    word_form_locations,
)
from app.schemas.proposal import ChangeProposal as ChangeProposalSchema
from app.schemas.proposal import LexemeUsage, RecommendationProposalCreate, VoteCreate
from app.schemas.proposal import ProposalVote as ProposalVoteSchema
from app.services import lexeme_service, spelling_service
from app.services.auth_service import can_user_edit_language, can_user_verify_language


def _now() -> datetime:
    return datetime.now(UTC)


def can_vote(db: Session, user: User, language_id: UUID) -> bool:
    return can_user_edit_language(db, user.id, language_id) or can_user_verify_language(
        db, user.id, language_id
    )


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def propose_recommendation(
    db: Session, lexeme: Lexeme, data: RecommendationProposalCreate, author: User
) -> ChangeProposal:
    if lexeme.recommendation == data.recommendation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This word is already marked {data.recommendation.value}",
        )
    already_open = (
        db.query(ChangeProposal)
        .filter(
            ChangeProposal.lexeme_id == lexeme.id,
            ChangeProposal.proposal_type == ProposalType.SET_RECOMMENDATION,
            ChangeProposal.status == ProposalStatus.OPEN,
        )
        .first()
    )
    if already_open:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="There is already an open proposal for this word — vote on that one",
        )

    proposal = ChangeProposal(
        language_id=lexeme.language_id,
        lexeme_id=lexeme.id,
        proposal_type=ProposalType.SET_RECOMMENDATION,
        payload={"recommendation": data.recommendation.value, "note": data.note},
        rationale=data.rationale,
        created_by_id=author.id,
    )
    # Proposing counts as the author's approval.
    proposal.votes.append(ProposalVote(user_id=author.id, choice=VoteChoice.APPROVE))
    db.add(proposal)
    db.flush()
    _resolve(db, proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def cast_vote(
    db: Session, proposal: ChangeProposal, voter: User, data: VoteCreate
) -> ChangeProposal:
    if proposal.proposal_type in REVIEWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This proposal is reviewed, not voted on",
        )
    if proposal.status != ProposalStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This proposal is already closed"
        )
    if not can_vote(db, voter, proposal.language_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only editors and reviewers of this language can vote",
        )

    vote = next((v for v in proposal.votes if v.user_id == voter.id), None)
    if vote is None:
        proposal.votes.append(
            ProposalVote(user_id=voter.id, choice=data.choice, comment=data.comment)
        )
    else:  # changing your mind is allowed while the proposal is open
        vote.choice = data.choice
        vote.comment = data.comment
        vote.updated_at = _now()
    db.flush()
    _resolve(db, proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


def propose_addition(
    db: Session,
    *,
    language_id: UUID,
    lexeme_id: UUID,
    proposal_type: ProposalType,
    payload: dict,
    author: User,
) -> ChangeProposal:
    """Queue a suggester's addition to an existing entry for one reviewer.
    The same open addition twice is the same proposal. Does not commit."""
    for open_one in (
        db.query(ChangeProposal)
        .filter(
            ChangeProposal.lexeme_id == lexeme_id,
            ChangeProposal.proposal_type == proposal_type,
            ChangeProposal.status == ProposalStatus.OPEN,
        )
        .all()
    ):
        if open_one.payload == payload:
            return open_one
    proposal = ChangeProposal(
        language_id=language_id,
        lexeme_id=lexeme_id,
        proposal_type=proposal_type,
        payload=payload,
        created_by_id=author.id,
    )
    db.add(proposal)
    db.flush()
    return proposal


def review_addition(
    db: Session, proposal: ChangeProposal, reviewer: User, approve: bool
) -> ChangeProposal:
    """Accept (applying it) or reject a suggester's addition."""
    if proposal.proposal_type not in REVIEWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This proposal is decided by vote",
        )
    if proposal.status != ProposalStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This proposal is already closed"
        )
    if not can_user_verify_language(db, reviewer.id, proposal.language_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only reviewers of this language can settle this",
        )
    if proposal.created_by_id == reviewer.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Someone else has to review this"
        )
    if approve:
        _apply(db, proposal)
        proposal.status = ProposalStatus.ACCEPTED
    else:
        proposal.status = ProposalStatus.REJECTED
    proposal.resolved_at = _now()
    db.commit()
    db.refresh(proposal)
    return proposal


def withdraw(db: Session, proposal: ChangeProposal, user: User) -> ChangeProposal:
    if proposal.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can withdraw a proposal"
        )
    if proposal.status != ProposalStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This proposal is already closed"
        )
    proposal.status = ProposalStatus.WITHDRAWN
    proposal.resolved_at = _now()
    db.commit()
    db.refresh(proposal)
    return proposal


def _threshold(db: Session, language_id: UUID) -> int:
    language = db.get(Language, language_id)
    return max(1, language.proposal_approval_threshold or 1) if language else 1


def _tally(proposal: ChangeProposal) -> tuple[int, int]:
    approvals = sum(1 for v in proposal.votes if v.choice == VoteChoice.APPROVE)
    return approvals, len(proposal.votes) - approvals


def _resolve(db: Session, proposal: ChangeProposal) -> None:
    threshold = _threshold(db, proposal.language_id)
    approvals, rejections = _tally(proposal)
    if rejections >= threshold:
        proposal.status = ProposalStatus.REJECTED
        proposal.resolved_at = _now()
    elif approvals >= threshold and rejections == 0:
        _apply(db, proposal)
        proposal.status = ProposalStatus.ACCEPTED
        proposal.resolved_at = _now()


def _apply(db: Session, proposal: ChangeProposal) -> None:
    payload = proposal.payload
    if proposal.proposal_type == ProposalType.SET_RECOMMENDATION:
        lexeme = db.get(Lexeme, proposal.lexeme_id)
        lexeme.recommendation = LexemeRecommendation(payload["recommendation"])
        lexeme.recommendation_note = payload.get("note")
    elif proposal.proposal_type == ProposalType.ADD_SPELLING_VARIANT:
        word_form_id = UUID(payload["word_form_id"])
        exists = (
            db.query(SpellingVariant)
            .filter(
                SpellingVariant.word_form_id == word_form_id,
                SpellingVariant.variant == payload["variant"],
            )
            .first()
        )
        form = db.get(WordForm, word_form_id)
        if exists is None and form is not None:
            db.add(
                SpellingVariant(
                    word_form_id=word_form_id,
                    variant=payload["variant"],
                    note=payload.get("note"),
                    created_by_id=proposal.created_by_id,
                )
            )
        if form is not None and payload.get("fix_texts"):
            spelling_service.correct_texts(
                db,
                proposal.language_id,
                payload["variant"],
                form.form,
                user_id=proposal.created_by_id,
            )
    elif proposal.proposal_type == ProposalType.ADD_TRANSLATION:
        other_id = UUID(payload["other_lexeme_id"])
        if db.get(Lexeme, other_id) is None:
            return
        low, high = lexeme_service._ordered_pair(proposal.lexeme_id, other_id)
        linked = db.execute(
            select(lexeme_translations).where(
                and_(
                    lexeme_translations.c.lexeme_id == low,
                    lexeme_translations.c.translation_id == high,
                )
            )
        ).first()
        if linked is None:
            db.execute(
                insert(lexeme_translations).values(
                    lexeme_id=low,
                    translation_id=high,
                    created_at=_now(),
                    created_by_id=proposal.created_by_id,
                )
            )


# ---------------------------------------------------------------------------
# Reads
# ---------------------------------------------------------------------------


def list_for_lexeme(db: Session, lexeme_id: UUID) -> list[ChangeProposal]:
    """The word page's recommendation history (votes only, not additions)."""
    return (
        db.query(ChangeProposal)
        .filter(
            ChangeProposal.lexeme_id == lexeme_id,
            ChangeProposal.proposal_type == ProposalType.SET_RECOMMENDATION,
        )
        .order_by(ChangeProposal.created_at.desc())
        .all()
    )


def list_proposals(
    db: Session,
    language_id: UUID | None,
    status_filter: ProposalStatus | None,
    proposal_type: ProposalType | None = ProposalType.SET_RECOMMENDATION,
) -> list[ChangeProposal]:
    query = db.query(ChangeProposal)
    if proposal_type:
        query = query.filter(ChangeProposal.proposal_type == proposal_type)
    if language_id:
        query = query.filter(ChangeProposal.language_id == language_id)
    if status_filter:
        query = query.filter(ChangeProposal.status == status_filter)
    return query.order_by(ChangeProposal.created_at.desc()).limit(200).all()


def lexeme_usage(db: Session, lexeme: Lexeme) -> LexemeUsage:
    form_ids = select(WordForm.id).where(WordForm.lexeme_id == lexeme.id)
    text_count = db.scalar(
        select(func.count(distinct(TextWordLink.text_id))).where(
            TextWordLink.word_form_id.in_(form_ids),
            TextWordLink.status != TextWordLinkStatus.REJECTED,
        )
    )
    audio_count = db.scalar(
        select(func.count())
        .select_from(word_form_audio)
        .where(word_form_audio.c.word_form_id.in_(form_ids))
    )
    places = db.execute(
        select(Location)
        .join(word_form_locations, word_form_locations.c.location_id == Location.id)
        .where(word_form_locations.c.word_form_id.in_(form_ids))
        .distinct()
    ).scalars()
    return LexemeUsage(
        lexeme_id=lexeme.id,
        lemma=lexeme.lemma,
        origin=lexeme.origin,
        recommendation=lexeme.recommendation,
        text_count=text_count or 0,
        audio_count=audio_count or 0,
        locations=sorted(
            {loc.name or f"{loc.latitude:.2f}, {loc.longitude:.2f}" for loc in places}
        ),
    )


def to_schema(
    db: Session, proposal: ChangeProposal, *, with_usage: bool = True
) -> ChangeProposalSchema:
    approvals, rejections = _tally(proposal)
    usernames = {
        u.id: u.username
        for u in db.query(User)
        .filter(User.id.in_({v.user_id for v in proposal.votes} | {proposal.created_by_id}))
        .all()
    }

    usage: list[LexemeUsage] = []
    lexeme = proposal.lexeme
    if with_usage and lexeme is not None:
        alternatives = [
            link.id
            for link in lexeme_service.list_synonyms(db, lexeme.id)
            if link.language_id == lexeme.language_id
        ]
        others = db.query(Lexeme).filter(Lexeme.id.in_(alternatives)).all() if alternatives else []
        usage = [lexeme_usage(db, lx) for lx in [lexeme, *others]]

    return ChangeProposalSchema(
        id=proposal.id,
        language_id=proposal.language_id,
        lexeme_id=proposal.lexeme_id,
        lexeme_lemma=lexeme.lemma if lexeme is not None else None,
        proposal_type=proposal.proposal_type,
        payload=proposal.payload,
        rationale=proposal.rationale,
        status=proposal.status,
        created_by_id=proposal.created_by_id,
        created_by_username=usernames.get(proposal.created_by_id),
        created_at=proposal.created_at,
        resolved_at=proposal.resolved_at,
        approvals=approvals,
        rejections=rejections,
        threshold=_threshold(db, proposal.language_id),
        votes=[
            ProposalVoteSchema(
                user_id=v.user_id,
                username=usernames.get(v.user_id),
                choice=v.choice,
                comment=v.comment,
                created_at=v.created_at,
                updated_at=v.updated_at,
            )
            for v in proposal.votes
        ],
        usage=usage,
    )
