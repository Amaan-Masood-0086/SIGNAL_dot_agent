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
from decimal import Decimal
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.core.synthetic_gate import assert_synthetic_write
from app.models.child import Child
from app.models.institution import Institution
from app.models.staff import STAFF_ROLES, Staff
from app.models.usage_log import UsageLog
from app.schemas.admin import (
    AllUsage,
    AdminChildCreate,
    AdminChildPage,
    AdminChildRead,
    ChildAssignment,
    InstitutionCreate,
    InstitutionPage,
    InstitutionRead,
    ProviderStatus,
    ProviderTestResult,
    StaffActiveUpdate,
    StaffCreate,
    StaffPage,
    StaffRead,
    StaffRoleUpdate,
    UsageByInstitution,
    UsageByStaff,
    UsageByProvider,
    UsageTotals,
    cost_or_none,
)
from app.schemas.child import ChildArchive, ChildRead
from app.services.audit import AuditService
from app.services.usage import UsageService
from app.services.credential_service import CredentialConfigError, CredentialService
from app.services.provider_checks import (
    llm_configured,
    stt_configured,
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


# ── Onboarding: institution → staff → child ────────────────────────────
#
# Without these a fresh system is unusable: there was no way to create a
# staff row through the product at all, so an admin could promote and
# deactivate people who already existed but never add one — and with no
# caretaker, no session can be opened and the screening pipeline cannot run.
#
# Each takes the institution EXPLICITLY. See the note on `InstitutionCreate`:
# deriving it from the admin's own token is precisely the "quietly wrong"
# filing that the caretaker-only nav guard exists to prevent.


def _institution_or_404(db: Session, institution_id: uuid.UUID) -> Institution:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise HTTPException(status_code=404, detail="Institution not found")
    return institution


@router.get("/institutions")
def list_institutions(
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified): the picker behind every
    onboarding form. An explicit institution_id is unusable in a UI without
    a way to enumerate the choices."""
    rows = db.execute(select(Institution).order_by(Institution.name.asc())).scalars().all()
    result = InstitutionPage(
        items=[InstitutionRead.model_validate(row) for row in rows],
        total=len(rows),
    )
    return envelope(result.model_dump(mode="json"))


@router.post("/institutions", status_code=201)
def create_institution(
    payload: InstitutionCreate,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Register a care institution.

    `is_synthetic` is forced to match the environment rather than accepted
    from the body. In `synthetic_only` a non-synthetic institution would be
    a dead end — every child write into it would be refused by the synthetic
    gate — so the tenant is created in the only state that can actually be
    used, and the client cannot ask for otherwise.
    """
    is_synthetic = settings.ENVIRONMENT == "synthetic_only"
    institution = Institution(name=payload.name, is_synthetic=is_synthetic)
    db.add(institution)
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="institution.create",
        resource_type="institution",
        resource_id=str(institution.id),
        institution_id=str(institution.id),
    )
    return envelope(InstitutionRead.model_validate(institution).model_dump(mode="json"))


@router.post("/staff", status_code=201)
def create_staff(
    payload: StaffCreate,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Create a staff account in a named institution.

    This is the only way to onboard a caretaker through the product; before
    it existed the sole paths were two seed scripts run by someone with
    database access.

    The stored hash is an unusable placeholder, exactly as `seed_admin.py`
    does it. Login does not verify passwords yet (FEAT-12), so storing a
    real one would imply a guarantee the system does not make — and storing
    a guessable one would be worse than storing none.
    """
    institution = _institution_or_404(db, payload.institution_id)
    assert_synthetic_write(bool(institution.is_synthetic), environment=settings.ENVIRONMENT)

    email = payload.email.strip().lower()
    existing = db.execute(select(Staff).where(Staff.email == email)).scalar_one_or_none()
    if existing is not None:
        # `staff.email` is unique at the DB level; say so cleanly instead of
        # letting an IntegrityError surface as a 500.
        raise HTTPException(
            status_code=409, detail="A staff account with that email already exists"
        )

    staff = Staff(
        institution_id=institution.id,
        email=email,
        hashed_password=f"!created-{secrets.token_urlsafe(24)}",
        role=payload.role,
        is_active=True,
        is_synthetic=bool(institution.is_synthetic),
    )
    db.add(staff)
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="staff.create",
        resource_type="staff",
        resource_id=str(staff.id),
        institution_id=str(institution.id),
    )
    return envelope(StaffRead.model_validate(staff).model_dump(mode="json"))


@router.post("/children", status_code=201)
def create_child_for_institution(
    payload: AdminChildCreate,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Register a child under an EXPLICITLY named institution.

    The caretaker route (`POST /children`) derives scope from the token and
    is deliberately untouched. This one cannot: a system-level admin has no
    care institution of their own, so the field is required and the admin
    states it every time.

    The ADR-02 dual-age contract is inherited from `ChildCreate`, not
    reimplemented — an admin-entered record is the same clinical record.
    """
    institution = _institution_or_404(db, payload.institution_id)
    is_synthetic = bool(institution.is_synthetic)
    assert_synthetic_write(is_synthetic, environment=settings.ENVIRONMENT)

    child = Child(
        institution_id=institution.id,
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
        actor_id=str(admin.staff_id),
        action="child.create",
        resource_type="child",
        resource_id=str(child.id),
        # The institution the child was FILED UNDER, not the admin's own —
        # that is the field an auditor would check.
        institution_id=str(institution.id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


# ── Removal: delete what is empty, archive what is not ─────────────────
#
# Nothing in SIGNAL was hard-deletable, and that was deliberate: staff
# deactivate, children archive, `signal_app` holds no DELETE grant, and
# REMEDIATION_BACKLOG R7 ("retention + defensible deletion") is open pending a
# policy decision. A flag is a clinical finding and the audit chain names the
# staff member behind it — destroying either removes the evidence the product
# exists to produce.
#
# That reasoning only binds records that HAVE such content. A mistyped
# registration with no sessions and no flags raises no retention question at
# all, and refusing to remove it just leaves junk on the roster forever.
#
# So deletion is permitted exactly there and refused everywhere else, with the
# safe alternative named in the refusal. The rule is a property of the ROW,
# not a permission of the caller: there is no force flag and no admin
# override, because privilege does not change what a record contains.


def _child_history_counts(db: Session, child_id: uuid.UUID) -> dict[str, int]:
    from app.models.flag import Flag
    from app.models.observation import Observation
    from app.models.session import Session as ConversationSession

    session_ids = select(ConversationSession.id).where(
        ConversationSession.child_id == child_id
    )
    return {
        "sessions": db.execute(
            select(func.count(ConversationSession.id)).where(
                ConversationSession.child_id == child_id
            )
        ).scalar_one(),
        "flags": db.execute(
            select(func.count(Flag.id)).where(Flag.child_id == child_id)
        ).scalar_one(),
        "observations": db.execute(
            select(func.count(Observation.id)).where(
                Observation.session_id.in_(session_ids)
            )
        ).scalar_one(),
    }


@router.delete("/children/{child_id}")
def delete_child(
    child_id: uuid.UUID,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Permanently remove a child that has no clinical record.

    Refuses the moment any screening history exists and points at archive,
    which keeps the record and takes the child off the roster.
    """
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")

    counts = _child_history_counts(db, child.id)
    if any(counts.values()):
        detail = (
            "This child has a screening record ("
            + ", ".join(f"{n} {name}" for name, n in counts.items() if n)
            + "). Deleting it would destroy clinical evidence — archive the "
            "child instead, which removes them from the roster and keeps the "
            "record."
        )
        raise HTTPException(status_code=409, detail=detail)

    name_len = len(child.name)  # nothing identifying goes to the audit row
    db.delete(child)
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="child.delete",
        resource_type="child",
        resource_id=str(child_id),
        institution_id=str(child.institution_id),
    )
    return envelope({"deleted": True, "id": str(child_id), "name_length": name_len})


@router.post("/children/{child_id}/archive")
def admin_archive_child(
    child_id: uuid.UUID,
    payload: ChildArchive,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """The safe removal, reachable from the admin console.

    Archive already existed, but only on the caretaker's child profile — a
    page the admin console cannot open, which left the delete refusal above
    pointing at a control the admin had no way to reach.
    """
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    if child.archived_at is not None:
        raise HTTPException(status_code=409, detail="Child is already archived")

    child.archived_at = datetime.datetime.now(datetime.timezone.utc)
    child.archived_reason = payload.reason.strip()
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="child.archive",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(child.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


@router.post("/children/{child_id}/restore")
def admin_restore_child(
    child_id: uuid.UUID,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Archiving is reversible on purpose — a wrong archive must not need a
    DBA to undo."""
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")
    if child.archived_at is None:
        raise HTTPException(status_code=409, detail="Child is not archived")

    child.archived_at = None
    child.archived_reason = None
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="child.restore",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(child.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


@router.delete("/staff/{staff_id}")
def delete_staff(
    staff_id: uuid.UUID,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Permanently remove a staff account that never did anything.

    Refuses once the account has run sessions or spent provider budget: the
    audit chain names this person as the actor behind graded findings, and a
    row that no longer exists cannot answer "who did this" — which is the
    non-repudiation the chain exists to provide. Deactivation keeps the
    identity and removes the access.
    """
    staff = _get_staff_or_404(db, staff_id)
    if staff.id == admin.staff_id:
        # Same anti-lockout rail as role change and deactivation.
        raise HTTPException(
            status_code=409,
            detail="You cannot delete your own account; ask another admin",
        )

    from app.models.session import Session as ConversationSession

    sessions = db.execute(
        select(func.count(ConversationSession.id)).where(
            ConversationSession.staff_id == staff.id
        )
    ).scalar_one()
    usage = db.execute(
        select(func.count(UsageLog.id)).where(UsageLog.staff_id == staff.id)
    ).scalar_one()
    if sessions or usage:
        raise HTTPException(
            status_code=409,
            detail=(
                f"This account has activity on the record ({sessions} session(s), "
                f"{usage} provider call(s)) and the audit trail names it as the "
                f"actor. Deactivate it instead — that removes access and keeps "
                f"the attribution."
            ),
        )

    institution_id = staff.institution_id
    db.delete(staff)
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="staff.delete",
        resource_type="staff",
        resource_id=str(staff_id),
        institution_id=str(institution_id),
    )
    return envelope({"deleted": True, "id": str(staff_id)})


# ── Assignment: who is responsible for this child ───────────────────────


@router.patch("/children/{child_id}/assignment")
def assign_child(
    child_id: uuid.UUID,
    payload: ChildAssignment,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Record which staff member is responsible for a child (migration 0007).

    RESPONSIBILITY, not ACCESS. Nothing reads this column to decide what a
    caretaker may see — every institution member still sees every child, and
    a test pins that. Narrowing visibility is REMEDIATION_BACKLOG R8 and a
    separate product decision: a child whose assigned caretaker is off shift
    must not disappear for the colleague covering the ward.
    """
    child = db.get(Child, child_id)
    if child is None:
        raise HTTPException(status_code=404, detail="Child not found")

    if payload.staff_id is None:
        child.assigned_staff_id = None
    else:
        staff = db.get(Staff, payload.staff_id)
        if staff is None:
            raise HTTPException(status_code=404, detail="Staff member not found")
        if staff.institution_id != child.institution_id:
            # A carer who works elsewhere cannot be responsible for this
            # child, and recording it would imply a relationship the tenant
            # boundary forbids.
            raise HTTPException(
                status_code=409,
                detail="That staff member works at a different institution",
            )
        if not staff.is_active:
            raise HTTPException(
                status_code=409,
                detail="That account is deactivated and cannot be assigned",
            )
        child.assigned_staff_id = staff.id
    db.flush()

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="child.assign",
        resource_type="child",
        resource_id=str(child.id),
        institution_id=str(child.institution_id),
    )
    return envelope(ChildRead.model_validate(child).model_dump(mode="json"))


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
            assigned_staff_id=child.assigned_staff_id,
            archived_at=child.archived_at,
            archived_reason=child.archived_reason,
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
        attempted = bool(stored) or stt_configured(settings)
        success, detail = test_stt_connection(settings, key=stored)
    else:
        attempted = bool(stored) or llm_configured(settings)
        success, detail = test_llm_connection(settings, key=stored, model=stored_model)

    # A test connection is a REAL provider call, and for the LLM it is a
    # billed one. It was previously audit-logged but never written to the
    # usage ledger, so the page whose entire job is cost visibility
    # under-reported actual billed calls (five of them, in this build).
    #
    # Cost is left NULL for the LLM rather than invented: the response's
    # token usage is not parsed on this path, and a made-up figure in a cost
    # column is worse than an honest blank. The STT check hits a free
    # endpoint (Azure issueToken / Knowlez /v1/usage), so zero is accurate.
    #
    # Nothing is recorded when the provider is unconfigured — no call left
    # the process, so there is nothing to account for.
    if attempted:
        UsageService(db).record(
            staff_id=admin.staff_id,
            institution_id=admin.institution_id,
            provider=provider,
            call_type="test_connection",
            estimated_cost=Decimal("0") if provider == "stt" else None,
        )

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

    # `COUNT(estimated_cost)` skips NULLs, so it counts the calls that
    # actually carry a price. The gap against `COUNT(id)` is what stops a
    # partial sum from reading as a complete bill — see `cost_or_none`.
    calls, priced, cost = db.execute(
        select(
            func.count(UsageLog.id),
            func.count(UsageLog.estimated_cost),
            func.sum(UsageLog.estimated_cost),
        ).where(*filters)
    ).one()
    total = UsageTotals.from_counts(calls, priced, cost)

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
            estimated_cost=cost_or_none(row.calls, row.cost),
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
            estimated_cost=cost_or_none(row.calls, row.cost),
        )
        for row in db.execute(inst_stmt).all()
    ]

    # Per-vendor split: DeepSeek (llm) and the speech provider bill
    # separately, so one merged number is not reconcilable against either.
    by_provider = {}
    for name in ("stt", "llm"):
        p_calls, p_priced, p_cost = db.execute(
            select(
                func.count(UsageLog.id),
                func.count(UsageLog.estimated_cost),
                func.sum(UsageLog.estimated_cost),
            ).where(*filters, UsageLog.provider == name)
        ).one()
        # This split is where NULL matters most: an STT provider test records
        # Decimal("0") because that endpoint is genuinely free, while an LLM
        # test connection records NULL because it is a real billed call whose
        # price we cannot compute. Reporting both as $0.00 made the LLM
        # invoice look like the STT one.
        by_provider[name] = UsageTotals.from_counts(p_calls, p_priced, p_cost)

    result = AllUsage(
        total=total,
        by_provider=UsageByProvider(**by_provider),
        by_staff=by_staff,
        by_institution=by_institution,
    )
    return envelope(result.model_dump(mode="json"))
