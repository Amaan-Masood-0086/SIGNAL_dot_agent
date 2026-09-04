"""Flag display endpoints (FEAT-09 backend half).

TRD §4: `GET /flags/{id}` is IDOR-sensitive — scope derives ONLY from the
signed JWT's institution claim; unknown or cross-institution ids return a
uniform 403 (no existence leakage). Lists serve the caretaker-facing UI:
flags for one child (profile) and for one session.

The trail is resolved against the knowledge base so every displayed flag
carries a clinician-reviewable basis (ADR-03/08).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_verified_staff, get_tenant_db
from app.core.envelope import envelope
from app.models.child import Child
from app.services.audit import AuditService
from app.models.flag import Flag
from app.models.milestone import Milestone
from app.models.session import Session as ConversationSession
from app.schemas.flag import FlagPage, FlagRead, TrailEntryRead

router = APIRouter(tags=["flags"])


def _build_trail(flag: Flag, by_ref: dict) -> list[TrailEntryRead]:
    """Resolve a flag's trail, preferring the SNAPSHOT over the live row.

    The knowledge base is upserted on citation_ref, so resolving descriptions
    live meant a six-month-old flag displayed today's wording rather than the
    wording that actually produced its grade (audit F11). The snapshot taken
    at flag creation is the record; the live row is only consulted for older
    flags written before snapshots existed, and to report drift.
    """
    entries = []
    for raw in flag.reasoning_trail or []:
        if not isinstance(raw, dict) or not raw.get("citation_ref"):
            continue
        ref = str(raw["citation_ref"])
        row = by_ref.get(ref)
        snapshot = raw.get("basis")
        live = row.description if row else None
        entries.append(
            TrailEntryRead(
                citation_ref=ref,
                basis=snapshot,
                # Snapshot first. Fall back to the live row only when this
                # flag predates snapshotting, so old records still render.
                description=snapshot or live,
                source=raw.get("source") or (row.source if row else None),
                # True when the knowledge base has been edited since: the
                # basis shown is still the real one, and the reader is told
                # the reference text has moved on.
                kb_drifted=bool(snapshot and live and snapshot != live),
            )
        )
    return entries


def _flag_read(db: Session, flag: Flag) -> FlagRead:
    data = FlagRead.model_validate(flag)
    data.reasoning_trail = _build_trail(flag, _milestones_by_ref(db, flag))
    return data


def _milestones_by_ref(db: Session, flag: Flag) -> dict:
    refs = [
        str(entry.get("citation_ref"))
        for entry in (flag.reasoning_trail or [])
        if isinstance(entry, dict) and entry.get("citation_ref")
    ]
    if not refs:
        return {}
    rows = db.execute(
        select(Milestone).where(Milestone.citation_ref.in_(refs))
    ).scalars().all()
    return {row.citation_ref: row for row in rows}


@router.get("/flags/{flag_id}")
def get_flag(
    flag_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    flag = db.get(Flag, flag_id)
    if flag is None or flag.institution_id != current_staff.institution_id:
        # Uniform 403 (IDOR T1/T2): never distinguish missing from foreign.
        raise HTTPException(status_code=403, detail="Access denied")
    # A flag IS the clinical finding — reading one is the access that most
    # needs a trail (audit F3).
    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="flag.read",
        resource_type="flag",
        resource_id=str(flag.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(_flag_read(db, flag).model_dump(mode="json"))


@router.get("/children/{child_id}/flags")
def list_child_flags(
    child_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    child = db.get(Child, child_id)
    if child is None or child.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total = db.execute(
        select(func.count(Flag.id)).where(Flag.child_id == child.id)
    ).scalar_one()
    rows = db.execute(
        select(Flag)
        .where(Flag.child_id == child.id)
        .order_by(Flag.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    # Per-query, not per-row: opening a child's screening history is one act
    # of access. Logging every row would bury the chain in noise and make the
    # log unreadable for the audit it exists to serve.
    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="flag.list",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(current_staff.institution_id),
    )
    result = FlagPage(
        items=[_flag_read(db, row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))


@router.get("/sessions/{session_id}/flags")
def list_session_flags(
    session_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    session = db.get(ConversationSession, session_id)
    if session is None or session.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total = db.execute(
        select(func.count(Flag.id)).where(Flag.session_id == session.id)
    ).scalar_one()
    rows = db.execute(
        select(Flag)
        .where(Flag.session_id == session.id)
        .order_by(Flag.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = FlagPage(
        items=[_flag_read(db, row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))
