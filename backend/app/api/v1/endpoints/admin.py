"""Admin Panel endpoints — SYSTEM-LEVEL admin role (THREAT_MODEL §2).

RBAC BOUNDARY — read before touching this file:
The admin role is system-level (NextaSol/dev), not per-institution. This
router is the ONLY place where queries intentionally skip institution
scoping, and every such bypass is marked below with "CROSS-INSTITUTION".
Nothing here weakens the caretaker-facing surface: those endpoints keep
`get_current_verified_staff` + explicit institution checks, unchanged.

Every state change here is audit-chained (who/what/when) — the admin panel
itself is under the same tamper-evidence regime it administers.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.models.child import Child
from app.models.institution import Institution
from app.models.staff import STAFF_ROLES, Staff
from app.models.usage_log import UsageLog
from app.schemas.admin import (
    AllUsage,
    AdminChildPage,
    AdminChildRead,
    ProviderStatus,
    ProviderTestResult,
    StaffActiveUpdate,
    StaffPage,
    StaffRead,
    StaffRoleUpdate,
    UsageByInstitution,
    UsageByStaff,
    UsageTotals,
)
from app.services.audit import AuditService
from app.services.credential_service import CredentialConfigError, CredentialService
from app.services.provider_checks import (
    provider_statuses,
    test_llm_connection,
    test_stt_connection,
)

router = APIRouter(prefix="/admin", tags=["admin"])

# Test-connection fires a REAL paid-provider call, so it gets the tightest
# budget in the API (auth-tier per sdlc-security rule 5): 5 per 5 minutes.
PROVIDER_TEST_LIMITER = FixedWindowRateLimiter(limit=5, window_seconds=300.0)


def _get_staff_or_404(db: Session, staff_id: uuid.UUID) -> Staff:
    """System-level lookup: unknown id is a plain 404. The uniform-403
    tenant-leakage rule does not apply here — the admin role is already
    system-wide, there is no institution boundary to protect."""
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise HTTPException(status_code=404, detail="Staff member not found")
    return staff


@router.get("/staff")
def list_staff(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    institution_id: uuid.UUID | None = Query(default=None),
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified): system-level staff directory.
    The only staff-list view that crosses institutions — the regular staff
    surface stays institution-scoped. Optional institution filter narrows."""
    stmt = select(Staff)
    count_stmt = select(func.count(Staff.id))
    if institution_id is not None:
        stmt = stmt.where(Staff.institution_id == institution_id)
        count_stmt = count_stmt.where(Staff.institution_id == institution_id)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        stmt.order_by(Staff.created_at.asc(), Staff.email.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = StaffPage(
        items=[StaffRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))


@router.get("/staff/{staff_id}")
def get_staff(
    staff_id: uuid.UUID,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified): single staff detail, system-level."""
    staff = _get_staff_or_404(db, staff_id)
    return envelope(StaffRead.model_validate(staff).model_dump(mode="json"))


@router.patch("/staff/{staff_id}/role")
def change_staff_role(
    staff_id: uuid.UUID,
    payload: StaffRoleUpdate,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Promote/demote — the ONLY promotion path besides the seed script
    (which bootstraps the FIRST admin; there is deliberately no open
    self-service endpoint for that)."""
    if payload.role not in STAFF_ROLES:
        raise HTTPException(status_code=422, detail="Unknown role")
    staff = _get_staff_or_404(db, staff_id)
    if staff.id == admin.staff_id:
        # Lockout rail: self-demotion could leave the system with zero
        # admins. A second admin must make this change.
        raise HTTPException(
            status_code=409,
            detail="You cannot change your own role; ask another admin",
        )
    staff.role = payload.role
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="staff.role_change",
        resource_type="staff",
        resource_id=str(staff.id),
        institution_id=str(staff.institution_id),
    )
    return envelope(StaffRead.model_validate(staff).model_dump(mode="json"))


@router.patch("/staff/{staff_id}/active")
def set_staff_active(
    staff_id: uuid.UUID,
    payload: StaffActiveUpdate,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Deactivate/reactivate — SOFT delete only. Staff rows are never
    hard-deleted: this is health-adjacent data with an audit trail."""
    staff = _get_staff_or_404(db, staff_id)
    if staff.id == admin.staff_id:
        # Same lockout rail as role change: no self-deactivation.
        raise HTTPException(
            status_code=409,
            detail="You cannot deactivate yourself; ask another admin",
        )
    staff.is_active = payload.is_active
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="staff.reactivate" if payload.is_active else "staff.deactivate",
        resource_type="staff",
        resource_id=str(staff.id),
        institution_id=str(staff.institution_id),
    )
    return envelope(StaffRead.model_validate(staff).model_dump(mode="json"))


# ── Children oversight (owner-requested 2026-09-01) ─────────────────────


@router.get("/children")
def list_all_children(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified, owner-requested): system-level
    oversight roster of every child across institutions, read-only. RBAC
    matrix extension: admin sees children data in the admin console ONLY —
    caretaker-facing surfaces remain strictly institution-scoped."""
    total = db.execute(select(func.count(Child.id))).scalar_one()
    rows = db.execute(
        select(Child, Institution.name)
        .join(Institution, Institution.id == Child.institution_id)
        .order_by(Child.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items = [
        AdminChildRead(
            id=child.id,
            name=child.name,
            institution_id=child.institution_id,
            institution_name=inst_name,
            dob_confirmed=child.dob_confirmed,
            dob=child.dob,
            estimated_age_range=child.estimated_age_range,
            intake_date=child.intake_date,
        )
        for child, inst_name in rows
    ]
    # This is the ONE read that crosses the tenant boundary, so it is the one
    # that most needs a trail (audit F3). Recorded per query with the page
    # actually returned — enough to reconstruct what an admin looked at
    # without writing a row per child.
    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="admin.children_list",
        resource_type="child",
        resource_id=f"page={page},size={page_size},returned={len(items)}",
        institution_id=str(admin.institution_id),
    )
    result = AdminChildPage(items=items, total=total, page=page, page_size=page_size)
    return envelope(result.model_dump(mode="json"))


# ── Provider status (ADR-09 controls + ADR-10 stored credentials) ──────


def _credential_sources(db: Session, settings: Settings) -> tuple[str | None, str | None]:
    """Where the ACTIVE key for each provider lives (ADR-10 precedence):
    "ui" when a provider_credentials row is active, else None (the caller
    then checks the env path). Never returns the key itself."""
    try:
        service = CredentialService(db, settings)
    except CredentialConfigError:
        return None, None
    stt_key, _ = service.resolve_with_model("stt")
    llm_key, _ = service.resolve_with_model("llm")
    stt_source = "ui" if stt_key else None
    llm_source = "ui" if llm_key else None
    return stt_source, llm_source


@router.get("/providers")
def provider_status(
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Configured/not-configured per provider + the SOURCE of the active
    credential (ui / env). Key VALUES are never displayed — the response
    schema has no field that could carry them (ADR-09/10)."""
    stt_source, llm_source = _credential_sources(db, settings)
    cards = [
        ProviderStatus(**card)
        for card in provider_statuses(
            settings, stt_key_source=stt_source, llm_key_source=llm_source
        )
    ]
    return envelope({"providers": [card.model_dump() for card in cards]})


@router.post("/providers/{provider}/test")
def provider_test_connection(
    provider: str,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Fire ONE minimal real call (Azure issueToken / 1-token LLM ping)
    against whichever credential source is ACTIVE per the ADR-10 precedence
    rule, and report success/failure only. Never returns or logs key
    material."""
    if provider not in {"stt", "llm"}:
        raise HTTPException(status_code=404, detail="Unknown provider")
    if not PROVIDER_TEST_LIMITER.allow(str(admin.staff_id)):
        raise HTTPException(
            status_code=429,
            detail="Too many provider tests; try again later",
        )

    try:
        stored, stored_model = CredentialService(db, settings).resolve_with_model(provider)
    except CredentialConfigError:
        stored = None
        stored_model = None

    if provider == "stt":
        success, detail = test_stt_connection(settings, key=stored)
    else:
        success, detail = test_llm_connection(settings, key=stored, model=stored_model)

    # Every admin action is audit-chained — including this one.
    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="provider.test_connection",
        resource_type="provider",
        resource_id=provider,
        institution_id=str(admin.institution_id),
    )
    result = ProviderTestResult(provider=provider, success=success, detail=detail)
    return envelope(result.model_dump(mode="json"))


# ── Usage tracking: the admin half of the cost-DoS visibility story ─────


@router.get("/usage")
def all_usage(
    start: datetime.datetime | None = Query(default=None),
    end: datetime.datetime | None = Query(default=None),
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified): system-level cost breakdown by
    staff member and by institution (RISK_REGISTER cost-DoS mitigation —
    the numbers must be visible, not just rate-limited blindly)."""
    filters = []
    if start is not None:
        filters.append(UsageLog.timestamp >= start)
    if end is not None:
        filters.append(UsageLog.timestamp <= end)

    calls, cost = db.execute(
        select(
            func.count(UsageLog.id), func.sum(UsageLog.estimated_cost)
        ).where(*filters)
    ).one()
    total = UsageTotals(calls=calls or 0, estimated_cost=float(cost) if cost else 0.0)

    staff_stmt = (
        select(
            UsageLog.staff_id,
            Staff.email,
            Staff.institution_id,
            func.count(UsageLog.id).label("calls"),
            func.sum(UsageLog.estimated_cost).label("cost"),
        )
        .join(Staff, UsageLog.staff_id == Staff.id)
        .where(*filters)
        .group_by(UsageLog.staff_id, Staff.email, Staff.institution_id)
        .order_by(func.count(UsageLog.id).desc())
    )
    by_staff = [
        UsageByStaff(
            staff_id=row.staff_id,
            email=row.email,
            institution_id=row.institution_id,
            calls=row.calls,
            estimated_cost=float(row.cost) if row.cost else 0.0,
        )
        for row in db.execute(staff_stmt).all()
    ]

    inst_stmt = (
        select(
            UsageLog.institution_id,
            Institution.name,
            func.count(UsageLog.id).label("calls"),
            func.sum(UsageLog.estimated_cost).label("cost"),
        )
        .join(Institution, UsageLog.institution_id == Institution.id)
        .where(*filters)
        .group_by(UsageLog.institution_id, Institution.name)
        .order_by(func.count(UsageLog.id).desc())
    )
    by_institution = [
        UsageByInstitution(
            institution_id=row.institution_id,
            name=row.name,
            calls=row.calls,
            estimated_cost=float(row.cost) if row.cost else 0.0,
        )
        for row in db.execute(inst_stmt).all()
    ]

    result = AllUsage(total=total, by_staff=by_staff, by_institution=by_institution)
    return envelope(result.model_dump(mode="json"))
