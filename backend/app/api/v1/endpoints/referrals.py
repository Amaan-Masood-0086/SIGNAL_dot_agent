"""Referral endpoints (FEAT-10) — closing the loop from flag to follow-up.

Scoping follows TRD §4: referral scope derives via referral → flag →
institution, flag scope via flag itself; unknown/cross-institution ids get
the uniform 403. The confirmation gate is enforced in ReferralService —
the endpoint maps the violation to 409 so the UI can show the confirm step.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, or_
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_verified_staff, get_tenant_db, require_active_staff
from app.core.envelope import envelope
from app.models.flag import Flag
from app.models.referral import Referral
from app.schemas.referral import ReferralCreate, ReferralRead, ReferralUpdate, ReferralPage, ReferralStatus
from app.services.audit import AuditService
from app.services.referral_service import ReferralService, ReferralValidationError

router = APIRouter(tags=["referrals"])


def _scoped_flag(
    db: Session, current_staff: CurrentStaff, flag_id: uuid.UUID
) -> Flag:
    flag = db.get(Flag, flag_id)
    if flag is None or flag.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return flag


def _scoped_referral(
    db: Session, current_staff: CurrentStaff, referral_id: uuid.UUID
) -> Referral:
    referral = db.get(Referral, referral_id)
    if referral is None or referral.institution_id != current_staff.institution_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return referral


def _read(db: Session, referral: Referral) -> ReferralRead:
    data = ReferralRead.model_validate(referral)
    data.escalated = ReferralService(db).effective_escalated(referral)
    return data


@router.get("/referrals")
def list_referrals(
    flag_id: uuid.UUID | None = None,
    status: ReferralStatus | None = None,
    overdue: bool = False,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    if flag_id is not None:
        _scoped_flag(db, current_staff, flag_id)
    filters = [Referral.institution_id == current_staff.institution_id]
    if flag_id is not None:
        filters.append(Referral.flag_id == flag_id)
    if status is not None:
        filters.append(Referral.status == status)
    if overdue:
        filters.extend([Referral.status != "closed", or_(Referral.escalated.is_(True), Referral.review_date < datetime.date.today())])
    total = db.execute(select(func.count(Referral.id)).where(*filters)).scalar_one()
    rows = db.execute(select(Referral).where(*filters).order_by(Referral.review_date.asc().nulls_last(), Referral.created_at.desc(), Referral.id).offset((page - 1) * page_size).limit(page_size)).scalars().all()
    AuditService(db).append(actor_id=str(current_staff.staff_id), action="referral.list", resource_type="institution", resource_id=str(current_staff.institution_id), institution_id=str(current_staff.institution_id))
    return envelope(ReferralPage(items=[_read(db, row) for row in rows], total=total, page=page, page_size=page_size).model_dump(mode="json"))


@router.post("/flags/{flag_id}/referral", status_code=201)
def create_referral(
    flag_id: uuid.UUID,
    payload: ReferralCreate,
    _: CurrentStaff = Depends(require_active_staff),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    flag = _scoped_flag(db, current_staff, flag_id)
    # Serialize confirmation retries for the same flag across workers.
    db.execute(select(Flag.id).where(Flag.id == flag.id).with_for_update()).scalar_one()
    existing = db.execute(select(Referral.id).where(Referral.flag_id == flag.id, Referral.status != "closed").limit(1)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="An open referral already exists for this result")
    try:
        referral = ReferralService(db).create_referral(
            institution_id=flag.institution_id,
            flag_id=flag.id,
            caretaker_confirmed=payload.caretaker_confirmed,
            responsible_person=payload.responsible_person,
            review_date=payload.review_date,
        )
    except ReferralValidationError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="referral.create",
        resource_type="referral",
        resource_id=str(referral.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(_read(db, referral).model_dump(mode="json"))


@router.get("/referrals/{referral_id}")
def get_referral(
    referral_id: uuid.UUID,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    referral = _scoped_referral(db, current_staff, referral_id)
    AuditService(db).append(actor_id=str(current_staff.staff_id), action="referral.read", resource_type="referral", resource_id=str(referral.id), institution_id=str(current_staff.institution_id))
    return envelope(_read(db, referral).model_dump(mode="json"))


@router.patch("/referrals/{referral_id}")
def update_referral(
    referral_id: uuid.UUID,
    payload: ReferralUpdate,
    _: CurrentStaff = Depends(require_active_staff),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    referral = _scoped_referral(db, current_staff, referral_id)
    if payload.status is not None:
        referral.status = payload.status
    if payload.responsible_person is not None:
        referral.responsible_person = payload.responsible_person
    if payload.review_date is not None:
        referral.review_date = payload.review_date
    if payload.outcome is not None:
        if payload.status != "closed" and referral.status != "closed":
            raise HTTPException(status_code=409, detail="Outcome can be recorded only when referral is closed")
        referral.outcome = payload.outcome
    if payload.clinician_note is not None:
        referral.clinician_note = payload.clinician_note

    # Persist escalation state on every write so the record reflects the
    # missed-review-date reality at the moment of the update.
    service = ReferralService(db)
    referral.escalated = service.is_overdue(referral, datetime.date.today())
    db.flush()

    AuditService(db).append(
        actor_id=str(current_staff.staff_id),
        action="referral.update",
        resource_type="referral",
        resource_id=str(referral.id),
        institution_id=str(current_staff.institution_id),
    )
    return envelope(_read(db, referral).model_dump(mode="json"))
