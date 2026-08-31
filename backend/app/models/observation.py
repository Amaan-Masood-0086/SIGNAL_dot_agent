"""Observation — Observation Agent output (extraction only, no judgment)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, JSONVariant, TimestampMixin


class Observation(IdMixin, TimestampMixin, Base):
    __tablename__ = "observations"

    # Denormalized tenant column for RLS (masterDataSDLC §3.2).
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("institutions.id"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UuidType, ForeignKey("sessions.id"), nullable=False, index=True
    )
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Raw caretaker input (voice-transcribed or typed). Treated strictly as
    # data — never as instructions to any agent (prompt-injection defense).
    raw_input: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_signals: Mapped[dict | None] = mapped_column(JSONVariant, nullable=True)
