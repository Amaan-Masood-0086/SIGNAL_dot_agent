"""Child intake + profile endpoints (FEAT-02).

TRD §4: `GET /children/{id}` is IDOR-sensitive (T1 mandatory) — scope is
derived ONLY from the signed JWT's institution claim. Unknown or
out-of-scope ids return a uniform 403 so record existence never leaks
across the tenant boundary. Every create is audit-chained (non-repudiation,
THREAT_MODEL §1) and passes the synthetic gate.
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
    get_tenant_db,
    require_active_staff,
)
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.synthetic_gate import assert_synthetic_write
from app.models.child import Child
from app.models.institution import Institution
from app.schemas.child import ChildArchive, ChildCreate, ChildPage, ChildRead
from app.services.audit import AuditService

router = APIRouter(prefix="/children", tags=["children"])


@router.post("", status_code=201)
def create_child(
    payload: ChildCreate,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_tenant_db),
):
    """Register a child at the caller's institution (ADR-02 dual-age intake)."""
    institution = db.get(Institution, current_staff.institution_id)
    if institution is None:
        # The JWT's institution claim must resolve to a tenant — fail closed.
        raise HTTPException(status_code=403, detail="Institution not recognized")

    is_synthetic = bool(institution.is_synthetic)
    assert_synthetic_write(is_synthetic, environment=settings.ENVIRONMENT)

    # ADR-02: store exactly one representation, never both.
    child = Child(
        institution_id=current_staff.institution_id,
        name=payload.name.strip(),
        intake_date=payload.intake_date or datetime.date.today(),
        dob_confirmed=payload.dob_confirmed,
        dob=payload.dob if payload.dob_confirmed else None,
        estimated_age_range=(
            None if payload.dob_confirmed else payload.estimated_age_range
        ),
        estimated_age_note=(
            None if payload.dob_confirmed else payload.estimated_age_note
        ),
        is_synthetic=is_synthetic,
    )
    db.add(child)
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="child.create",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


@router.get("")
def list_children(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str = Query(
        default="active",
        pattern="^(active|archived|all)$",
        description="active (default) | archived | all",
    ),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    """Institution-scoped roster for the dashboard — scope derives ONLY from
    the signed JWT claim, so cross-tenant rows can never appear."""
    # Archived children leave the roster but not the database (migration
    # 0006) — the record survives for whatever retention policy is set, and
    # `status=archived` is how a caretaker finds it again. Hiding archived
    # rows with no way to list them would make the archive a black hole.
    scope = [Child.institution_id == current_staff.institution_id]
    if status == "active":
        scope.append(Child.archived_at.is_(None))
    elif status == "archived":
        scope.append(Child.archived_at.is_not(None))

    total = db.execute(select(func.count(Child.id)).where(*scope)).scalar_one()
    # Archived rows read newest-first: the useful question there is "what
    # left recently", not "who has been here longest".
    order = (
        (Child.archived_at.desc(),)
        if status == "archived"
        else (Child.created_at.asc(), Child.name.asc())
    )
    rows = db.execute(
        select(Child)
        .where(*scope)
        .order_by(*order)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = ChildPage(
        items=[ChildRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))


@router.get("/{child_id}")
def get_child(
    child_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    """Read a child profile — institution-scoped via the JWT claim only."""
    child = db.execute(
        select(Child).where(Child.id == child_id)
    ).scalar_one_or_none()
    if child is None or child.institution_id != current_staff.institution_id:
        # Uniform 403 (IDOR T1/T2): never distinguish "not found" from
        # "exists in another institution".
        raise HTTPException(status_code=403, detail="Access denied")
    # Clinical record access is auditable (audit F3): "who opened this
    # child's record" must be answerable. Denied attempts are NOT logged
    # here on purpose — the 403 path never confirms the record exists, and
    # writing a row keyed to an id the caller may not own would leak that.
    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="child.read",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


@router.post("/{child_id}/archive")
def archive_child(
    child_id: uuid.UUID,
    payload: ChildArchive,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    _: CurrentStaff = Depends(require_active_staff),
    db: Session = Depends(get_tenant_db),
):
    """Take a child off the active roster WITHOUT destroying the record.

    Deliberately not a DELETE. Two different situations arrive here — a
    mistaken registration, and a child who has left the institution — and
    only the second one has a retention question attached. Archiving serves
    both and forecloses neither: flags, sessions and observations keep their
    foreign keys, and the row is still there when a retention policy is
    finally decided. `signal_app` holds no DELETE grant on children, so this
    is the only removal path that exists at all.
    """
    child = db.execute(
        select(Child).where(Child.id == child_id)
    ).scalar_one_or_none()
    if child is None or child.institution_id != current_staff.institution_id:
        # Uniform 403 (IDOR T1/T2): never distinguish missing from foreign.
        raise HTTPException(status_code=403, detail="Access denied")
    if child.archived_at is not None:
        raise HTTPException(status_code=409, detail="Child is already archived")

    child.archived_at = datetime.datetime.now(datetime.timezone.utc)
    child.archived_reason = payload.reason.strip()
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="child.archive",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


@router.post("/{child_id}/restore")
def restore_child(
    child_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    _: CurrentStaff = Depends(require_active_staff),
    db: Session = Depends(get_tenant_db),
):
    """Undo an archive. Archiving is reversible on purpose — a caretaker who
    archives the wrong child must not need a DBA to fix it."""
    child = db.execute(
        select(Child).where(Child.id == child_id)
    ).scalar_one_or_none()
    if child is None or child.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
    if child.archived_at is None:
        raise HTTPException(status_code=409, detail="Child is not archived")

    child.archived_at = None
    child.archived_reason = None
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="child.restore",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))
