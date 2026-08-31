"""Audit log entry — append-only, hash-chained (THREAT_MODEL §1 Tampering).

Tamper-evidence is the technical basis of SIGNAL's liability-protection
value proposition, not generic logging. Append-only is enforced at the DB
level too: the migration revokes UPDATE/DELETE from the app role.
"""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin


class AuditLogEntry(IdMixin, Base):
    __tablename__ = "audit_log"

    # Monotonic chain position — ordering for hash verification.
    sequence: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, index=True
    )
    # Server-side only — actor_id MUST never come from a request body.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(UuidType, nullable=True)
    institution_id: Mapped[uuid.UUID | None] = mapped_column(UuidType, nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(60), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(64), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    hash_prev: Mapped[str] = mapped_column(String(64), nullable=False)
    hash_self: Mapped[str] = mapped_column(String(64), nullable=False)
