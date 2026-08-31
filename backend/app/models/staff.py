"""Staff — role ∈ {caretaker, admin} (TRD §3)."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

STAFF_ROLES = ("caretaker", "admin")


class Staff(IdMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    # Denormalized tenant column: RLS policies need a direct institution_id
    # on every tenant-scoped table (masterDataSDLC §3.2 pattern).
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    # bcrypt cost 12 per sdlc-security.md OWASP A02 — hashing arrives with
    # real login (FEAT-12); FEAT-01 stores the column only.
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        Enum(*STAFF_ROLES, name="staff_role", native_enum=False), nullable=False
    )
    # Soft delete (Admin Panel): accounts are deactivated, NEVER hard-deleted
    # — health-adjacent data with an audit trail. Default active.
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
