"""CredentialService — ADR-10 encryption-at-rest for provider keys.

Fernet symmetric encryption keyed by the required env var
CREDENTIAL_ENCRYPTION_KEY. The plaintext value exists only:
  1. transiently on write (before `store` encrypts it), and
  2. at the point of actually calling the provider (`resolve` → client
     construction). Nowhere else — never in responses, logs, or audit.

Precedence rule (ADR-10 §4): an ACTIVE stored credential beats the
equivalent environment variable; with no active row the env var keeps
working exactly as before (FEAT-03/FEAT-05 bootstrap/CI path untouched).
"""

from __future__ import annotations

import datetime
import uuid

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import select, update
from sqlalchemy.orm import Session, load_only

from app.core.config import Settings
from app.models.provider_credential import CREDENTIAL_PROVIDERS, ProviderCredential


class CredentialConfigError(RuntimeError):
    """CREDENTIAL_ENCRYPTION_KEY missing/malformed — the credential surface
    fails secure rather than storing anything in plaintext."""


class CredentialService:
    def __init__(self, session: Session, settings: Settings):
        self._session = session
        try:
            self._fernet = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY.encode())
        except (ValueError, TypeError) as exc:
            raise CredentialConfigError(
                "CREDENTIAL_ENCRYPTION_KEY is not a valid Fernet key"
            ) from exc

    # ── write path ─────────────────────────────────────────────────────────

    def store(
        self, *, provider: str, value: str, staff_id: uuid.UUID | None
    ) -> ProviderCredential:
        if provider not in CREDENTIAL_PROVIDERS:
            raise ValueError(f"unknown provider {provider!r}")
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("credential value must not be blank")

        encrypted = self._fernet.encrypt(cleaned.encode()).decode()
        masked_suffix = cleaned[-4:]

        # Rotation: any prior active row for this provider is deactivated —
        # exactly one active credential per provider.
        self._session.execute(
            update(ProviderCredential)
            .where(ProviderCredential.provider == provider)
            .where(ProviderCredential.is_active.is_(True))
            .values(is_active=False, updated_at=datetime.datetime.now(datetime.timezone.utc))
        )
        row = ProviderCredential(
            provider=provider,
            encrypted_value=encrypted,
            masked_suffix=masked_suffix,
            is_active=True,
            created_by_staff_id=staff_id,
        )
        self._session.add(row)
        self._session.flush()
        self._session.refresh(row)  # populate server-default timestamps
        return row

    def deactivate(self, provider: str) -> bool:
        """Soft delete — the row stays (auditability); DELETE is never
        granted to the app role at the DB level either."""
        result = self._session.execute(
            update(ProviderCredential)
            .where(ProviderCredential.provider == provider)
            .where(ProviderCredential.is_active.is_(True))
            .values(is_active=False, updated_at=datetime.datetime.now(datetime.timezone.utc))
        )
        return result.rowcount > 0

    # ── read path (decryption happens ONLY here) ──────────────────────────

    def resolve(self, provider: str) -> str | None:
        """The active credential's plaintext, or None. A token that cannot
        be decrypted (e.g. master key regenerated) degrades to None so the
        caller falls back to the env var instead of crashing."""
        row = self._session.execute(
            select(ProviderCredential)
            .where(ProviderCredential.provider == provider)
            .where(ProviderCredential.is_active.is_(True))
            .order_by(ProviderCredential.created_at.desc())
            .limit(1)
        ).scalar_one_or_none()
        if row is None:
            return None
        try:
            return self._fernet.decrypt(row.encrypted_value.encode()).decode()
        except (InvalidToken, ValueError):
            return None

    def status_rows(self) -> dict[str, ProviderCredential | None]:
        """Latest row per provider for the status list. ADR-10 write-only
        contract at the SQL level: the query selects ONLY the display
        columns — encrypted_value is never part of this query, not merely
        omitted by the serializer."""
        out: dict[str, ProviderCredential | None] = {p: None for p in CREDENTIAL_PROVIDERS}
        rows = self._session.execute(
            select(ProviderCredential)
            .options(
                load_only(
                    ProviderCredential.provider,
                    ProviderCredential.is_active,
                    ProviderCredential.masked_suffix,
                    ProviderCredential.updated_at,
                )
            )
            .order_by(ProviderCredential.created_at.desc())
        ).scalars().all()
        for row in rows:
            if out.get(row.provider) is None:
                out[row.provider] = row
        return out
