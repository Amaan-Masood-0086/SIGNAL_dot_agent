"""Provider credential rows (ADR-10) — Fernet-encrypted keys at rest.

SYSTEM-LEVEL table, same tier as audit_log: NO institution_id, NO RLS
(state explicitly in migration 0004 — access control comes from grants and
the admin-only, write-only API contract). The plaintext exists only
transiently: on write (before encryption) and at provider-construction time
(decryption). It never appears in any response, log line, or audit entry.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, String, Text
from sqlalchemy import Uuid as UuidType
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

from .types import IdMixin, TimestampMixin

CREDENTIAL_PROVIDERS = ("stt", "llm")


class ProviderCredential(IdMixin, TimestampMixin, Base):
    __tablename__ = "provider_credentials"

    provider: Mapped[str] = mapped_column(String(8), nullable=False)
    # Fernet token (base64) — never the plaintext.
    encrypted_value: Mapped[str] = mapped_column(Text, nullable=False)
    # Last 4 chars of the RAW value, stored separately — display only.
    masked_suffix: Mapped[str] = mapped_column(String(4), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # No FK to staff (audit_log precedent): the attribution trail must
    # survive any future staff-row changes; staff are never hard-deleted.
    created_by_staff_id: Mapped[uuid.UUID | None] = mapped_column(
        UuidType, nullable=True
    )
