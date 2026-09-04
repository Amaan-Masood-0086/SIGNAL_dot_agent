"""Referral endpoints (FEAT-10) — closing the loop from flag to follow-up.

Scoping follows TRD §4: referral scope derives via referral → flag →
institution, flag scope via flag itself; unknown/cross-institution ids get
the uniform 403. The confirmation gate is enforced in ReferralService —
the endpoint maps the violation to 409 so the UI can show the confirm step.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_verified_staff, get_tenant_db
from app.core.envelope import envelope
from app.models.flag import Flag
from app.models.referral import Referral
from app.schemas.referral import ReferralCreate, ReferralRead, ReferralUpdate
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


@router.post("/flags/{flag_id}/referral", status_code=201)
def create_referral(
    flag_id: uuid.UUID,
    payload: ReferralCreate,
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_tenant_db),
):
    flag = _scoped_flag(db, current_staff, flag_id)
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
    return envelope(_read(db, referral).model_dump(mode="json"))


@router.patch("/referrals/{referral_id}")
def update_referral(
    referral_id: uuid.UUID,
    payload: ReferralUpdate,
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
