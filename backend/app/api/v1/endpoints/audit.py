"""Audit log viewer — TRD §4 `GET /audit_log`, admin-only.

READ-ONLY: no write surface exists here (the table is append-only at the DB
role level too). The admin role is SYSTEM-LEVEL, so this endpoint reads
across institutions BY DESIGN — THREAT_MODEL §2 grants audit_log reads to
the NextaSol/dev admin only. Institution-scoped endpoints are untouched.

Filters: actor_id, exact action, ISO-8601 date range. Newest first — an
operator investigating an incident wants the latest entries immediately.
`/integrity` exposes the hash-chain state: "chain intact" or the exact
sequence where tamper-evidence first breaks.
"""

from __future__ import annotations

import datetime
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.envelope import envelope
from app.models.audit_log import AuditLogEntry
from app.schemas.admin import AuditChainStatus, AuditLogEntryRead, AuditLogPage
from app.services.audit import verify_audit_chain_detail

router = APIRouter(prefix="/audit_log", tags=["audit"])


@router.get("/integrity")
def audit_chain_integrity(
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """Hash-chain health: intact flag + count + first broken sequence."""
    intact, checked, first_broken = verify_audit_chain_detail(db)
    result = AuditChainStatus(
        chain_intact=intact,
        entries_checked=checked,
        first_broken_sequence=first_broken,
    )
    return envelope(result.model_dump(mode="json"))


@router.get("")
def list_audit_log(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    actor_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None, max_length=120),
    start: datetime.datetime | None = Query(default=None),
    end: datetime.datetime | None = Query(default=None),
    admin: CurrentStaff = Depends(get_current_admin_staff),
    db: Session = Depends(get_db),
):
    """CROSS-INSTITUTION BYPASS (justified): THREAT_MODEL §2 — reading the
    audit_log is a system-level admin capability, never per-institution."""
    stmt = select(AuditLogEntry)
    count_stmt = select(func.count(AuditLogEntry.id))
    if actor_id is not None:
        stmt = stmt.where(AuditLogEntry.actor_id == actor_id)
        count_stmt = count_stmt.where(AuditLogEntry.actor_id == actor_id)
    if action is not None:
        stmt = stmt.where(AuditLogEntry.action == action)
        count_stmt = count_stmt.where(AuditLogEntry.action == action)
    if start is not None:
        stmt = stmt.where(AuditLogEntry.timestamp >= start)
        count_stmt = count_stmt.where(AuditLogEntry.timestamp >= start)
    if end is not None:
        stmt = stmt.where(AuditLogEntry.timestamp <= end)
        count_stmt = count_stmt.where(AuditLogEntry.timestamp <= end)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        stmt.order_by(AuditLogEntry.sequence.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    result = AuditLogPage(
        items=[AuditLogEntryRead.model_validate(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )
    return envelope(result.model_dump(mode="json"))
