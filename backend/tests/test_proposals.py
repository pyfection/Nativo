"""
Tests for change proposals: collective "preferred word" decisions.

The contract under test:
- Only editors can propose; proposing records the author's approval.
- Editors/reviewers vote; a proposal is ACCEPTED (and applied) once approvals
  reach the language threshold with no objection, REJECTED once objections
  reach it. Admins vote like anyone else — no override.
- One open proposal per word; votes can be changed while open; only the
  author can withdraw; closed proposals take no votes.
- The recommendation can't be set through the normal lexeme update.
"""

import os
import uuid
from datetime import UTC, datetime

import pytest

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

sqlalchemy = pytest.importorskip("sqlalchemy")
from app.api.v1.endpoints.proposals import (  # noqa: E402
    list_lexeme_proposals,
    list_proposals,
    propose_recommendation,
    vote,
    withdraw,
)
from app.database import Base  # noqa: E402
from app.models.change_proposal import ProposalStatus, VoteChoice  # noqa: E402
from app.models.language import Language  # noqa: E402
from app.models.location import Location  # noqa: E402
from app.models.user import User, UserRole  # noqa: E402
from app.models.user_language import ProficiencyLevel, UserLanguage  # noqa: E402
from app.models.word import (  # noqa: E402
    Lexeme,
    LexemeOrigin,
    LexemeRecommendation,
    SynonymNuance,
    word_form_locations,
)
from app.schemas.proposal import RecommendationProposalCreate, VoteCreate  # noqa: E402
from app.schemas.word import (  # noqa: E402
    LexemeCreate,
    LexemeUpdate,
    SynonymCreate,
    WordFormCreateNested,
)
from app.services import lexeme_service  # noqa: E402
from fastapi import HTTPException  # noqa: E402
from sqlalchemy import create_engine, insert  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

engine = create_engine("sqlite:///:memory:", future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)

PREFERRED = LexemeRecommendation.PREFERRED


@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Session:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def _now() -> datetime:
    return datetime.now(UTC)


def _user(db: Session, role: UserRole = UserRole.PUBLIC) -> User:
    user = User(
        id=uuid.uuid4(),
        email=f"u-{uuid.uuid4()}@example.com",
        username=f"user-{uuid.uuid4().hex[:8]}",
        hashed_password="x",
        role=role,
        is_active=True,
        is_superuser=role == UserRole.ADMIN,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(user)
    db.flush()
    return user


def _language(db: Session, threshold: int = 2) -> Language:
    lang = Language(
        id=uuid.uuid4(),
        name=f"L-{uuid.uuid4().hex[:6]}",
        proposal_approval_threshold=threshold,
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(lang)
    db.flush()
    return lang


def _member(db: Session, lang: Language, *, can_edit=False, can_verify=False) -> User:
    user = _user(db)
    db.add(
        UserLanguage(
            user_id=user.id,
            language_id=lang.id,
            proficiency_level=ProficiencyLevel.NATIVE,
            can_edit=can_edit,
            can_verify=can_verify,
        )
    )
    db.flush()
    return user


def _lexeme(db: Session, lang: Language, lemma: str, creator: User, **kw) -> Lexeme:
    return lexeme_service.create_lexeme(
        db,
        LexemeCreate(
            language_id=lang.id,
            lemma=lemma,
            lemma_form=WordFormCreateNested(form=lemma, is_lemma=True),
            **kw,
        ),
        creator_id=creator.id,
    )


async def _propose(db, lexeme, author, rec=PREFERRED, note="Native word"):
    return await propose_recommendation(
        lexeme.id,
        RecommendationProposalCreate(recommendation=rec, note=note, rationale="Why not"),
        current_user=author,
        db=db,
    )


async def _vote(db, proposal, voter, choice, comment=None):
    return await vote(
        proposal.id, VoteCreate(choice=choice, comment=comment), current_user=voter, db=db
    )


@pytest.fixture
def setup(db):
    lang = _language(db)
    editor = _member(db, lang, can_edit=True)
    reviewer = _member(db, lang, can_verify=True)
    word = _lexeme(db, lang, "Párádaisa", editor)
    return lang, editor, reviewer, word


# ---------------------------------------------------------------------------


async def test_only_editors_can_propose(db, setup):
    lang, _, reviewer, word = setup
    viewer = _member(db, lang)
    for user in (viewer, reviewer):  # reviewers vote, but don't open proposals
        with pytest.raises(HTTPException) as exc:
            await _propose(db, word, user)
        assert exc.value.status_code == 403


async def test_proposal_counts_author_and_waits_for_second_vote(db, setup):
    _, editor, _, word = setup
    proposal = await _propose(db, word, editor)

    assert proposal.status == ProposalStatus.OPEN
    assert (proposal.approvals, proposal.rejections, proposal.threshold) == (1, 0, 2)
    assert proposal.votes[0].user_id == editor.id
    db.refresh(word)
    assert word.recommendation == LexemeRecommendation.NEUTRAL  # nothing applied yet


async def test_second_approval_accepts_and_applies(db, setup):
    _, editor, reviewer, word = setup
    proposal = await _propose(db, word, editor)
    proposal = await _vote(db, proposal, reviewer, VoteChoice.APPROVE)

    assert proposal.status == ProposalStatus.ACCEPTED
    assert proposal.resolved_at is not None
    db.refresh(word)
    assert word.recommendation == PREFERRED
    assert word.recommendation_note == "Native word"


async def test_objection_blocks_until_withdrawn(db, setup):
    lang, editor, reviewer, word = setup
    third = _member(db, lang, can_edit=True)
    proposal = await _propose(db, word, editor)

    proposal = await _vote(db, proposal, reviewer, VoteChoice.REJECT, "Tomadn is more common")
    proposal = await _vote(db, proposal, third, VoteChoice.APPROVE)
    assert proposal.status == ProposalStatus.OPEN  # 2 approvals, but an open objection
    assert (proposal.approvals, proposal.rejections) == (2, 1)

    # The objector changes their mind -> accepted.
    proposal = await _vote(db, proposal, reviewer, VoteChoice.APPROVE)
    assert proposal.status == ProposalStatus.ACCEPTED
    assert len(proposal.votes) == 3  # vote was updated, not duplicated


async def test_enough_objections_reject(db, setup):
    lang, editor, reviewer, word = setup
    third = _member(db, lang, can_verify=True)
    proposal = await _propose(db, word, editor)
    await _vote(db, proposal, reviewer, VoteChoice.REJECT)
    proposal = await _vote(db, proposal, third, VoteChoice.REJECT)

    assert proposal.status == ProposalStatus.REJECTED
    db.refresh(word)
    assert word.recommendation == LexemeRecommendation.NEUTRAL


async def test_threshold_one_applies_immediately(db):
    lang = _language(db, threshold=1)
    editor = _member(db, lang, can_edit=True)
    word = _lexeme(db, lang, "Tomadn", editor)

    proposal = await _propose(db, word, editor, rec=LexemeRecommendation.DISCOURAGED)
    assert proposal.status == ProposalStatus.ACCEPTED
    db.refresh(word)
    assert word.recommendation == LexemeRecommendation.DISCOURAGED


async def test_outsiders_cant_vote_and_admins_get_one_vote(db, setup):
    lang, editor, _, word = setup
    proposal = await _propose(db, word, editor)

    outsider = _member(db, lang)  # viewer
    with pytest.raises(HTTPException) as exc:
        await _vote(db, proposal, outsider, VoteChoice.APPROVE)
    assert exc.value.status_code == 403

    # An admin can vote (no membership needed) but it's one vote, not an override:
    # with a threshold of 3 it doesn't decide alone.
    lang.proposal_approval_threshold = 3
    db.commit()
    admin = _user(db, UserRole.ADMIN)
    proposal = await _vote(db, proposal, admin, VoteChoice.APPROVE)
    assert proposal.status == ProposalStatus.OPEN
    assert proposal.approvals == 2


async def test_one_open_proposal_per_word_and_no_noop(db, setup):
    _, editor, _, word = setup
    with pytest.raises(HTTPException) as exc:
        await _propose(db, word, editor, rec=LexemeRecommendation.NEUTRAL)
    assert exc.value.status_code == 400  # already neutral

    await _propose(db, word, editor)
    with pytest.raises(HTTPException) as exc:
        await _propose(db, word, editor, rec=LexemeRecommendation.DISCOURAGED)
    assert exc.value.status_code == 400


async def test_withdraw_is_author_only_and_closes(db, setup):
    _, editor, reviewer, word = setup
    proposal = await _propose(db, word, editor)

    with pytest.raises(HTTPException) as exc:
        await withdraw(proposal.id, current_user=reviewer, db=db)
    assert exc.value.status_code == 403

    proposal = await withdraw(proposal.id, current_user=editor, db=db)
    assert proposal.status == ProposalStatus.WITHDRAWN
    with pytest.raises(HTTPException) as exc:
        await _vote(db, proposal, reviewer, VoteChoice.APPROVE)
    assert exc.value.status_code == 400

    # A new proposal can be opened after withdrawal.
    assert (await _propose(db, word, editor)).status == ProposalStatus.OPEN


async def test_usage_covers_word_and_its_alternatives(db, setup):
    lang, editor, _, word = setup
    loan = _lexeme(db, lang, "Tomadn", editor, origin=LexemeOrigin.LOANWORD)
    lexeme_service.add_synonym(
        db, word.id, SynonymCreate(other_lexeme_id=loan.id, nuance=SynonymNuance.LOAN_VARIANT)
    )
    place = Location(id=uuid.uuid4(), latitude=48.1, longitude=11.6, name="Minga")
    db.add(place)
    db.flush()
    db.execute(
        insert(word_form_locations).values(
            word_form_id=loan.forms[0].id, location_id=place.id, created_at=_now()
        )
    )
    db.commit()

    proposal = await _propose(db, word, editor)
    usage = {u.lemma: u for u in proposal.usage}
    assert list(usage) == ["Párádaisa", "Tomadn"]  # target first
    assert usage["Tomadn"].locations == ["Minga"]
    assert usage["Tomadn"].origin == LexemeOrigin.LOANWORD
    assert usage["Párádaisa"].locations == []


async def test_audit_trail_and_queue(db, setup):
    lang, editor, reviewer, word = setup
    other_lang = _language(db)
    proposal = await _propose(db, word, editor)
    await _vote(db, proposal, reviewer, VoteChoice.APPROVE, "Agreed")

    [history] = await list_lexeme_proposals(word.id, db=db)
    assert history.status == ProposalStatus.ACCEPTED
    assert [(v.username, v.choice, v.comment) for v in history.votes] == [
        (editor.username, VoteChoice.APPROVE, None),
        (reviewer.username, VoteChoice.APPROVE, "Agreed"),
    ]
    assert history.created_by_username == editor.username

    assert await list_proposals(language_id=lang.id, db=db) == []  # default: open only
    closed = await list_proposals(language_id=lang.id, status_filter=ProposalStatus.ACCEPTED, db=db)
    assert [p.id for p in closed] == [proposal.id]
    assert await list_proposals(language_id=other_lang.id, status_filter=None, db=db) == []


def test_recommendation_is_not_directly_editable():
    update = LexemeUpdate(**{"recommendation": "preferred", "notes": "x"})
    assert "recommendation" not in update.model_dump(exclude_unset=True)
