"""Shared column types and mixins for SIGNAL models.

Models render correct Postgres types (UUID, JSONB, timestamptz) in Alembic
migrations. All SIGNAL tests run against real PostgreSQL — never SQLite.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, func
from sqlalchemy import Uuid as UuidType
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

# JSONB on Postgres; the JSON fallback variant keeps models dialect-portable
# but SIGNAL tests and runtime never use SQLite.
JSONVariant = JSONB().with_variant(JSON(), "sqlite")


class IdMixin:
    """UUID v4 primary key, generated application-side (TRD §4 MUST #8)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UuidType, primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """Server-generated timestamps (TRD §4 MUST #9 — never client-supplied)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
