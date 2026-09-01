"""Provider credential endpoints (ADR-10, supersedes ADR-09's deferral).

Admin-only, WRITE-ONLY contract: values go IN (encrypted with Fernet under
CREDENTIAL_ENCRYPTION_KEY), and no response body, log line, or audit entry
ever carries the raw or encrypted value back out. Reads expose ONLY
{provider, is_active, masked_suffix, updated_at}.

Precedence (ADR-10 §4): an active stored credential beats the env var; the
env var remains the bootstrap/CI path when no active row exists.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import CurrentStaff, get_current_admin_staff, get_db
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.models.provider_credential import CREDENTIAL_PROVIDERS
from app.schemas.admin import CredentialStatusRead, CredentialWrite
from app.services.audit import AuditService
from app.services.credential_service import CredentialConfigError, CredentialService

router = APIRouter(prefix="/admin/credentials", tags=["admin"])

# Secret writes get the tightest budget in the API (auth-tier per
# sdlc-security rule 5): 5 per 5 minutes per admin.
CREDENTIAL_WRITE_LIMITER = FixedWindowRateLimiter(limit=5, window_seconds=300.0)


def _service(db: Session, settings: Settings) -> CredentialService:
    try:
        return CredentialService(db, settings)
    except CredentialConfigError as exc:
        # Fail secure: never fall back to plaintext storage.
        raise HTTPException(status_code=503, detail=str(exc))


def _status_read(provider: str, row) -> CredentialStatusRead:
    # Only these four fields can ever leave the API — the schema has no
    # field capable of carrying the raw or encrypted value.
    return CredentialStatusRead(
        provider=provider,
        is_active=bool(row.is_active) if row else False,
        masked_suffix=row.masked_suffix if row else None,
        updated_at=row.updated_at if row else None,
        model_name=row.model_name if row else None,
    )


@router.put("/{provider}")
def store_credential(
    provider: str,
    payload: CredentialWrite,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    if provider not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")
    if not CREDENTIAL_WRITE_LIMITER.allow(str(admin.staff_id)):
        raise HTTPException(
            status_code=429, detail="Too many credential writes; try again later"
        )

    service = _service(db, settings)
    try:
        row = service.store(
            provider=provider,
            value=payload.value,
            staff_id=admin.staff_id,
            model_name=payload.model,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    # Audit records actor + provider + timestamp — NEVER the value.
    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="credential.store",
        resource_type="provider_credential",
        resource_id=provider,
        institution_id=str(admin.institution_id),
    )
    return envelope(_status_read(provider, row).model_dump(mode="json"))


@router.get("")
def list_credentials(
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Status for both providers. The query returns full rows, but the
    response schema exposes only provider/is_active/masked_suffix/
    updated_at — encrypted_value is structurally never serialized."""
    rows = _service(db, settings).status_rows()
    items = [
        _status_read(provider, row).model_dump(mode="json")
        for provider, row in rows.items()
    ]
    return envelope({"providers": items})


@router.delete("/{provider}")
def delete_credential(
    provider: str,
    admin: CurrentStaff = Depends(get_current_admin_staff),
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db),
):
    """Soft delete: deactivates the stored credential; the system falls
    back to the environment variable per the precedence rule."""
    if provider not in CREDENTIAL_PROVIDERS:
        raise HTTPException(status_code=404, detail="Unknown provider")

    service = _service(db, settings)
    deactivated = service.deactivate(provider)
    if not deactivated:
        raise HTTPException(
            status_code=404, detail="No active credential for this provider"
        )

    AuditService(db).append(
        actor_id=str(admin.staff_id),
        action="credential.deactivate",
        resource_type="provider_credential",
        resource_id=provider,
        institution_id=str(admin.institution_id),
    )
    return envelope(_status_read(provider, None).model_dump(mode="json"))
