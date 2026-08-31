"""Usage ledger — one row per paid provider call (STT / LLM).

Cost-visibility support for RISK_REGISTER's cost-DoS mitigation: rate
limiting alone is blind; this table makes per-staff / per-institution spend
actually visible. Append-only like audit_log (the migration grants the app
role SELECT + INSERT only). Tenant-scoped via RLS; the cross-institution
admin breakdown is an application-layer SYSTEM-LEVEL view restricted to the
admin endpoints (THREAT_MODEL §2).
"""

from __future__ import annotations

import datetime
import uuid
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin

USAGE_PROVIDERS = ("stt", "llm")


class UsageLog(IdMixin, Base):
    __tablename__ = "usage_log"

    staff_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("staff.id"), nullable=False, index=True
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(8), nullable=False)
    # e.g. "transcribe" (STT) or the pipeline stage name for LLM calls.
    call_type: Mapped[str] = mapped_column(String(40), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
    # Best-effort estimate; NULL when no cost model exists for the provider.
    estimated_cost: Mapped[Decimal | None] = mapped_column(
        Numeric(precision=12, scale=6), nullable=True
    )
