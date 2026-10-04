"""
Change-proposal endpoints: propose, vote, withdraw, and read the audit trail.

Reads are public (the decision history is part of the record); writes need
edit rights to propose and edit-or-verify rights to vote.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database import get_db
from app.models.change_proposal import ChangeProposal, ProposalStatus
from app.models.user import User
from app.models.word import Lexeme
from app.schemas.proposal import ChangeProposal as ChangeProposalSchema
from app.schemas.proposal import RecommendationProposalCreate, VoteCreate
from app.services import proposal_service
from app.services.auth_service import require_language_edit_permission

router = APIRouter()


def _get_proposal_or_404(db: Session, proposal_id: UUID) -> ChangeProposal:
    proposal = db.get(ChangeProposal, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Proposal not found")
    return proposal


@router.get("/words/{lexeme_id}/proposals", response_model=list[ChangeProposalSchema])
async def list_lexeme_proposals(lexeme_id: UUID, db: Session = Depends(get_db)):
    return [
        proposal_service.to_schema(db, p, with_usage=p.status == ProposalStatus.OPEN)
        for p in proposal_service.list_for_lexeme(db, lexeme_id)
    ]


@router.post(
    "/words/{lexeme_id}/proposals/recommendation",
    response_model=ChangeProposalSchema,
    status_code=status.HTTP_201_CREATED,
)
async def propose_recommendation(
    lexeme_id: UUID,
    data: RecommendationProposalCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    lexeme = db.get(Lexeme, lexeme_id)
    if not lexeme:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lexeme not found")
    require_language_edit_permission(db, current_user, lexeme.language_id)
    proposal = proposal_service.propose_recommendation(db, lexeme, data, current_user)
    return proposal_service.to_schema(db, proposal)


@router.get("/proposals", response_model=list[ChangeProposalSchema])
async def list_proposals(
    language_id: UUID | None = None,
    status_filter: ProposalStatus | None = ProposalStatus.OPEN,
    db: Session = Depends(get_db),
):
    return [
        proposal_service.to_schema(db, p)
        for p in proposal_service.list_proposals(db, language_id, status_filter)
    ]


@router.post("/proposals/{proposal_id}/votes", response_model=ChangeProposalSchema)
async def vote(
    proposal_id: UUID,
    data: VoteCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    proposal = _get_proposal_or_404(db, proposal_id)
    proposal = proposal_service.cast_vote(db, proposal, current_user, data)
    return proposal_service.to_schema(db, proposal)


@router.post("/proposals/{proposal_id}/withdraw", response_model=ChangeProposalSchema)
async def withdraw(
    proposal_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    proposal = _get_proposal_or_404(db, proposal_id)
    proposal = proposal_service.withdraw(db, proposal, current_user)
    return proposal_service.to_schema(db, proposal)
