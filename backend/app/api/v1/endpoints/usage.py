"""Usage views — "my usage" for any staff member.

The admin cross-institution counterpart lives on the admin router
(GET /admin/usage) — see the RBAC boundary note there. This endpoint is
deliberately NOT admin-gated: every staff member sees their own call
count/cost, which is what turns cost-DoS mitigation from blind rate
limiting into visible accountability (RISK_REGISTER).
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_verified_staff, get_db
from app.core.envelope import envelope
from app.models.usage_log import UsageLog
from app.schemas.admin import MyUsage, UsageByProvider, UsageTotals

router = APIRouter(prefix="/usage", tags=["usage"])


def _totals(db: Session, *filters) -> UsageTotals:
    calls, cost = db.execute(
        select(func.count(UsageLog.id), func.sum(UsageLog.estimated_cost)).where(*filters)
    ).one()
    return UsageTotals(calls=calls or 0, estimated_cost=float(cost) if cost else 0.0)


@router.get("/me")
def my_usage(
    start: datetime.datetime | None = Query(default=None),
    end: datetime.datetime | None = Query(default=None),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    db: Session = Depends(get_db),
):
    """Caller's own usage only — the scope is the JWT's staff identity, so
    no other staff member's rows can ever appear here."""
    filters = [UsageLog.staff_id == current_staff.staff_id]
    if start is not None:
        filters.append(UsageLog.timestamp >= start)
    if end is not None:
        filters.append(UsageLog.timestamp <= end)

    total = _totals(db, *filters)
    by_provider = {}
    for provider in ("stt", "llm"):
        by_provider[provider] = _totals(db, *filters, UsageLog.provider == provider)

    result = MyUsage(
        staff_id=current_staff.staff_id,
        total=total,
        by_provider=UsageByProvider(**by_provider),
    )
    return envelope(result.model_dump(mode="json"))
