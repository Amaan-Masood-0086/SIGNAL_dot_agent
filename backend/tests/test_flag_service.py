"""FlagService — FEAT-05 service-layer enforcement of the reasoning trail.

TEST_PLAN §2 rules pinned here:
- "Flag requires reasoning_trail" → empty trail rejected AT THE SERVICE LAYER
- "Reasoning-trail citation integrity" → every cited citation_ref must resolve
  to a real ingested knowledge-base row — dangling citations rejected, not
  stored "for review" (ADR-03 + ADR-08: the trail is a regulatory surface)

The schema constraint (reasoning_trail NOT NULL) only stops the field being
skipped entirely; the service layer enforces the substance.
"""

from __future__ import annotations

import datetime
import uuid

import pytest


@pytest.fixture(scope="module")
def loaded_kb(pg_engine):
    """Knowledge base ingested once for this module (94 rows, v2 CSV).
    Torn down again — the shared session DB must stay clean for the
    FEAT-04 loader/idempotency tests."""
    from sqlalchemy import delete
    from sqlalchemy.orm import Session

    from app.models.milestone import Milestone
    from app.services.knowledge import load_knowledge_base

    session = Session(bind=pg_engine, expire_on_commit=False)
    load_knowledge_base(session)
    session.commit()
    yield session
    session.execute(delete(Milestone))
    session.commit()
    session.close()


@pytest.fixture()
def db(db_session):
    return db_session


@pytest.fixture()
def tenant(db_session):
    """Institution + staff + child + session for FK-complete flag writes."""
    from app.models.child import Child
    from app.models.institution import Institution
    from app.models.session import Session as ConversationSession
    from app.models.staff import Staff

    inst = Institution(name="Flag Service Tenant", is_synthetic=True)
    db_session.add(inst)
    db_session.flush()
    staff = Staff(
        id=uuid.uuid4(),
        institution_id=inst.id,
        email=f"{uuid.uuid4().hex}@signal.example",
        hashed_password="unused",
        role="caretaker",
        is_synthetic=True,
    )
    db_session.add(staff)
    child = Child(
        institution_id=inst.id,
        name="Flag Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False,
        estimated_age_range="24-30 months",
        is_synthetic=True,
    )
    db_session.add(child)
    db_session.flush()
    session = ConversationSession(
        institution_id=inst.id, child_id=child.id, staff_id=staff.id, mode="text"
    )
    db_session.add(session)
    db_session.flush()
    return {"institution": inst, "child": child, "session": session}


def _create(db, tenant, **overrides):
    from app.services.flag_service import FlagService

    payload = dict(
        institution_id=tenant["institution"].id,
        session_id=tenant["session"].id,
        child_id=tenant["child"].id,
        domain="Speech_Language",
        confidence_grade="high",
        reasoning_trail=[
            {"citation_ref": "SL-RF-018", "basis": "expressive language red flag"}
        ],
        status="flagged",
    )
    payload.update(overrides)
    return FlagService(db).create_flag(**payload)


def test_flag_with_empty_reasoning_trail_rejected(db, tenant):
    """TEST_PLAN §2: empty trail → rejection at the service layer."""
    from app.services.flag_service import FlagService, FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(db, tenant, reasoning_trail=[])


def test_flag_with_missing_reasoning_trail_rejected(db, tenant):
    from app.services.flag_service import FlagService, FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(db, tenant, reasoning_trail=None)


def test_flag_with_dangling_citation_rejected(db, tenant):
    """A citation that does not resolve to a real knowledge-base row is a
    compliance failure — rejected, never stored (ADR-03/08)."""
    from app.services.flag_service import FlagValidationError

    with pytest.raises(FlagValidationError, match="SL-RF-999"):
        _create(
            db, tenant,
            reasoning_trail=[{"citation_ref": "SL-RF-999", "basis": "invented"}],
        )


def test_flag_with_partial_dangling_citation_rejected(db, tenant):
    """One real ref + one fake ref is still rejected — a trail is only as
    credible as its weakest citation."""
    from app.services.flag_service import FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(
            db, tenant,
            reasoning_trail=[
                {"citation_ref": "SL-RF-018", "basis": "real"},
                {"citation_ref": "HEAR-RF-777", "basis": "invented"},
            ],
        )


def test_flag_trail_entry_without_citation_ref_rejected(db, tenant):
    from app.services.flag_service import FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(db, tenant, reasoning_trail=[{"basis": "no citation at all"}])


def test_valid_flag_persists_with_resolving_trail(db, tenant, loaded_kb):
    from app.models.flag import Flag

    flag = _create(
        db, tenant,
        confidence_grade="moderate",
        reasoning_trail=[
            {"citation_ref": "SL-RF-020", "basis": "expressive concern at 5 yr"},
            {"citation_ref": "SL-M-031", "basis": "supporting milestone"},
        ],
        explanation_text="plain-language text",
    )
    db.flush()
    stored = db.get(Flag, flag.id)
    assert stored.domain == "Speech_Language"
    assert stored.confidence_grade == "moderate"
    assert stored.status == "flagged"
    refs = [entry["citation_ref"] for entry in stored.reasoning_trail]
    assert refs == ["SL-RF-020", "SL-M-031"]


def test_flag_rejects_dld_domain_name(db, tenant):
    """ADR-07: the domain is Speech_Language — 'DLD' must never be written."""
    from app.services.flag_service import FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(db, tenant, domain="DLD")


def test_flag_rejects_unknown_grade(db, tenant):
    from app.services.flag_service import FlagValidationError

    with pytest.raises(FlagValidationError):
        _create(db, tenant, confidence_grade="no_concern")
