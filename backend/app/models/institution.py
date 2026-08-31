"""Institution — the tenant boundary for RLS (TRD §3)."""

from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin


class Institution(IdMixin, TimestampMixin, Base):
    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    # is_synthetic propagates down from institutions (TRD §3) and is checked
    # against the ENVIRONMENT=synthetic_only gate on every write.
    is_synthetic: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
