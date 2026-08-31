"""Session — one caretaker conversation; supports save/resume (feature #8)."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, func
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

SESSION_STATUSES = ("in_progress", "completed", "abandoned")
SESSION_MODES = ("voice", "text")


class Session(IdMixin, TimestampMixin, Base):
    __tablename__ = "sessions"

    # Denormalized tenant column for RLS (masterDataSDLC §3.2).
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("children.id"), nullable=False, index=True
    )
    staff_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("staff.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        Enum(*SESSION_STATUSES, name="session_status", native_enum=False),
        nullable=False,
        default="in_progress",
    )
    mode: Mapped[str] = mapped_column(
        Enum(*SESSION_MODES, name="session_mode", native_enum=False), nullable=False
    )
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    resumed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
