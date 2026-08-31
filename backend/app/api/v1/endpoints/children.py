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

from app.api.deps import CurrentStaff, get_current_verified_staff, get_db
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.synthetic_gate import assert_synthetic_write
from app.models.child import Child
from app.models.institution import Institution
from app.schemas.child import ChildCreate, ChildPage, ChildRead
from app.services.audit import AuditService

router = APIRouter(prefix="/children", tags=["children"])


@router.post("", status_code=201)
def create_child(
    payload: ChildCreate,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
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
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    """Institution-scoped roster for the dashboard — scope derives ONLY from
    the signed JWT claim, so cross-tenant rows can never appear."""
    total = db.execute(
        select(func.count(Child.id)).where(
            Child.institution_id == current_staff.institution_id
        )
    ).scalar_one()
    rows = db.execute(
        select(Child)
        .where(Child.institution_id == current_staff.institution_id)
        .order_by(Child.created_at.asc(), Child.name.asc())
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
    db: Session = Depends(get_db),
):
    """Read a child profile — institution-scoped via the JWT claim only."""
    child = db.execute(
        select(Child).where(Child.id == child_id)
    ).scalar_one_or_none()
    if child is None or child.institution_id != current_staff.institution_id:
        # Uniform 403 (IDOR T1/T2): never distinguish "not found" from
        # "exists in another institution".
        raise HTTPException(status_code=403, detail="Access denied")
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))
