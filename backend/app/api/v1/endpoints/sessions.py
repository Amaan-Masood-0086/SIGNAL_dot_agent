"""Session + observation endpoints — the FEAT-03 input layer.

One conversation per child (TRD §3 `sessions`), carrying caretaker input as
observations (TRD §3 `observations`). The observation endpoint is
MODE-AGNOSTIC: voice transcripts and typed text submit the identical payload,
so downstream never knows which mode captured a turn (FEAT-03 acceptance).

Security: every lookup is institution-scoped via the signed JWT claim only;
unknown or cross-tenant ids return a uniform 403 (IDOR T1/T2). Every write is
audit-chained and passes the synthetic gate.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentStaff,
    get_current_verified_staff,
    get_db,
    require_active_staff,
)
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.synthetic_gate import assert_synthetic_write
from app.models.child import Child
from app.models.institution import Institution
from app.models.observation import Observation
from app.models.session import Session as ConversationSession
from app.models.staff import Staff
from app.schemas.session import (
    ObservationCreate,
    ObservationPage,
    ObservationRead,
    SessionCreate,
    SessionRead,
)
from app.services.audit import AuditService

router = APIRouter(prefix="/sessions", tags=["sessions"])

# TRD §4: "POST /sessions/{id}/messages — 30/min per staff member" (this
# observations endpoint is the implemented turn-capture surface).
OBSERVATION_LIMITER = FixedWindowRateLimiter(limit=30, window_seconds=60.0)


def rate_limited_observation(
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
) -> None:
    if not OBSERVATION_LIMITER.allow(str(current_staff.staff_id)):
        raise HTTPException(
            status_code=429,
            detail="Too many requests; try again in a minute",
        )


def _scoped_session(
    db: Session, current_staff: CurrentStaff, session_id: uuid.UUID
) -> ConversationSession:
    """Fetch a session or fail closed — uniform 403 for not-found and
    cross-institution alike (no existence leakage)."""
    session = db.get(ConversationSession, session_id)
    if session is None or session.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return session


@router.post("", status_code=201)
def create_session(
    payload: SessionCreate,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Open a conversation for a child of the caller's institution."""
    # The JWT identity must resolve to a real staff row in the same tenant —
    # fail closed otherwise (MUST-NOT #3: identity is never client-supplied).
    # Deactivated accounts cannot open new sessions (soft-delete enforcement).
    staff = db.get(Staff, current_staff.staff_id)
    if (
        staff is None
        or staff.institution_id != current_staff.institution_id
        or not staff.is_active
    ):
        raise HTTPException(status_code=403, detail="Staff identity not recognized")

    child = db.get(Child, payload.child_id)
    if child is None or child.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")

    institution = db.get(Institution, current_staff.institution_id)
    if institution is None:
        raise HTTPException(status_code=403, detail="Institution not recognized")
    assert_synthetic_write(bool(institution.is_synthetic), environment=settings.ENVIRONMENT)

    session = ConversationSession(
        institution_id=current_staff.institution_id,
        child_id=child.id,
        staff_id=current_staff.staff_id,
        mode=payload.mode,
    )
    db.add(session)
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="session.create",
        resource_type="session",
        resource_id=str(session.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(SessionRead.model_validate(session).model_dump(mode="json"))


@router.get("/{session_id}")
def get_session(
    session_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    session = _scoped_session(db, current_staff, session_id)
    return envelope(SessionRead.model_validate(session).model_dump(mode="json"))


@router.post("/{session_id}/complete")
def complete_session(
    session_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    session = _scoped_session(db, current_staff, session_id)
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")
    session.status = "completed"
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="session.complete",
        resource_type="session",
        resource_id=str(session.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(SessionRead.model_validate(session).model_dump(mode="json"))


@router.post("/{session_id}/resume")
def resume_session(
    session_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    """FEAT-08 interrupted-shift handling: an in_progress session left idle
    is resumed by a new request. Turn history and reasoning state live in
    persisted observations, so context is intact by construction — this
    endpoint stamps the resume and audits it."""
    session = _scoped_session(db, current_staff, session_id)
    if session.status != "in_progress":
        raise HTTPException(
            status_code=409,
            detail="Only an interrupted (in-progress) session can be resumed",
        )
    session.resumed_at = datetime.datetime.now(datetime.timezone.utc)
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="session.resume",
        resource_type="session",
        resource_id=str(session.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(SessionRead.model_validate(session).model_dump(mode="json"))


@router.post("/{session_id}/observations", status_code=201)
def add_observation(
    session_id: uuid.UUID,
    payload: ObservationCreate,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    _: None = Depends(rate_limited_observation),
    __: CurrentStaff = Depends(require_active_staff),
    db: Session = Depends(get_db),
):
    """Capture one caretaker turn. Voice transcripts and typed text arrive
    through this same endpoint — the stored observation is identical either
    way. `turn_number` is server-assigned; the body cannot influence it."""
    session = _scoped_session(db, current_staff, session_id)
    if session.status != "in_progress":
        raise HTTPException(status_code=409, detail="Session is not in progress")

    last_turn = db.execute(
        select(func.max(Observation.turn_number)).where(
            Observation.session_id == session.id
        )
    ).scalar_one()
    next_turn = (last_turn or 0) + 1

    observation = Observation(
        institution_id=session.institution_id,
        session_id=session.id,
        turn_number=next_turn,
        raw_input=payload.raw_input,
    )
    db.add(observation)
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="observation.create",
        resource_type="observation",
        resource_id=str(observation.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(ObservationRead.model_validate(observation).model_dump(mode="json"))


@router.get("/{session_id}/observations")
def list_observations(
    session_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    """Turn history for one session, paginated (contract #4; page_size ≤ 100)."""
    session = _scoped_session(db, current_staff, session_id)

    total = db.execute(
        select(func.count(Observation.id)).where(Observation.session_id == session.id)
    ).scalar_one()
    rows = db.execute(
        select(Observation)
        .where(Observation.session_id == session.id)
        .order_by(Observation.turn_number.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = ObservationPage(
        items=[ObservationRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))
