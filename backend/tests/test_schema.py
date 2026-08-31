"""Schema integrity — TRD §3 full model set, ADR-02 and ADR-03 fields.

Runs against real PostgreSQL (FEAT-01 acceptance: never SQLite) on a
database migrated via Alembic; see conftest.py::pg_engine.
"""

from __future__ import annotations

import datetime

from app.db.base import Base

EXPECTED_TABLES = {
    "institutions",
    "staff",
    "children",
    "sessions",
    "observations",
    "milestones",
    "flags",
    "referrals",
    "safeguarding_escalations",
    "audit_log",
}


def test_all_trd_section3_tables_exist():
    from app import models  # noqa: F401

    assert EXPECTED_TABLES <= set(Base.metadata.tables.keys())


def test_children_dual_age_fields_per_adr02():
    """ADR-02: dob_confirmed + nullable dob + estimated range, not a single DOB."""
    from app.models.child import Child

    cols = Child.__table__.columns
    for required in ("dob_confirmed", "dob", "estimated_age_range", "estimated_age_note"):
        assert required in cols, f"children.{required} missing (ADR-02)"
    assert cols["dob"].nullable is True


def test_flags_reasoning_trail_is_jsonb_container_per_adr03():
    from app.models.flag import Flag

    col = Flag.__table__.columns["reasoning_trail"]
    assert col.nullable is False, "reasoning_trail is mandatory per ADR-03"
    # JSONB on Postgres, JSON variant elsewhere — both are JSON container types
    assert "json" in col.type.__class__.__name__.lower()


def test_safeguarding_escalations_is_a_separate_table():
    """Never merged with flags — separate table with its own identity."""
    from app.models.flag import Flag
    from app.models.safeguarding_escalation import SafeguardingEscalation

    assert SafeguardingEscalation.__tablename__ == "safeguarding_escalations"
    assert SafeguardingEscalation.__tablename__ != Flag.__tablename__
    assert SafeguardingEscalation.__table__ is not Flag.__table__


def test_full_synthetic_record_chain_roundtrips(db_session):
    """One synthetic institution → child → session → observation → flag → referral."""
    from app.models.child import Child
    from app.models.flag import Flag
    from app.models.institution import Institution
    from app.models.milestone import Milestone
    from app.models.observation import Observation
    from app.models.referral import Referral
    from app.models.session import Session as CaseSession
    from app.models.staff import Staff

    institution = Institution(name="Synthetic Care Home A", is_synthetic=True)
    db_session.add(institution)
    db_session.flush()  # institution.id must exist before tenant rows cite it
    staff = Staff(
        institution_id=institution.id,
        email="synthetic-staff@signal.example",
        hashed_password="stub",
        role="caretaker",
        is_synthetic=True,
    )
    # ADR-02: estimated-age child (no confirmed DOB)
    child = Child(
        institution_id=institution.id,
        name="Synthetic Child",
        intake_date=datetime.date(2026, 8, 1),
        dob_confirmed=False,
        dob=None,
        estimated_age_range="8-10 months",
        estimated_age_note="intake worker estimate",
        is_synthetic=True,
    )
    db_session.add_all([staff, child])
    db_session.flush()  # ids must exist before dependent rows cite them
    session = CaseSession(
        child_id=child.id, staff_id=staff.id, institution_id=institution.id,
        status="in_progress", mode="text",
    )
    db_session.add(session)
    db_session.flush()
    observation = Observation(
        session_id=session.id,
        institution_id=institution.id,
        turn_number=1,
        raw_input="does not respond to name",
        extracted_signals={"signals": ["no_response_to_name"]},
    )
    milestone = Milestone(
        citation_ref="SL-M-FIXTURE-001",
        entry_type="milestone",
        domain="Speech_Language",
        age_min_months=6,
        age_max_months=12,
        description="Responds to own name",
        source="WHO milestones (synthetic fixture)",
        phase_scope="in scope",
        provenance="test fixture",
    )
    db_session.add_all([observation, milestone])
    db_session.flush()  # milestone.id must exist before a flag may cite it
    flag = Flag(
        session_id=session.id,
        child_id=child.id,
        institution_id=institution.id,
        domain="Speech_Language",
        confidence_grade="moderate",
        # ADR-08: the trail cites the human-readable citation_ref, not the UUID
        reasoning_trail=[{"citation_ref": milestone.citation_ref, "basis": "fixture"}],
        explanation_text="Synthetic explanation",
        status="flagged",
    )
    db_session.add(flag)
    db_session.flush()  # flag.id must exist before a referral may cite it
    referral = Referral(
        flag_id=flag.id,
        institution_id=institution.id,
        status="pending_capacity",
        responsible_person="Synthetic supervisor",
        review_date=datetime.date(2026, 9, 15),
        escalated=False,
        caretaker_confirmed=True,
    )
    db_session.add(referral)
    db_session.commit()

    assert flag.reasoning_trail[0]["citation_ref"] == "SL-M-FIXTURE-001"
    assert child.dob_confirmed is False
    assert child.dob is None
    assert referral.flag_id == flag.id
