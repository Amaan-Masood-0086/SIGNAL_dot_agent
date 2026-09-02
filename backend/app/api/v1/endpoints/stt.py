"""STT transcribe endpoint (FEAT-03 — voice mode only).

Locked capture path: Browser MediaRecorder → this backend endpoint (web-
development.md tech stack). The provider is a dependency seam so tests and
future providers never touch the route itself. Audio is read into memory,
transcribed, and discarded — NEVER persisted (data minimization).

Unconfigured ⇒ 503 with a clean message; the text fallback never depends on
this endpoint (FEAT-03 acceptance: zero STT dependency for text).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import (
    CurrentStaff,
    get_current_verified_staff,
    get_tenant_db,
    require_active_staff,
)
from app.core.config import Settings, get_settings
from app.core.envelope import envelope
from app.core.rate_limit import FixedWindowRateLimiter
from app.services.credential_service import CredentialConfigError, CredentialService
from app.services.stt import (
    AzureSpeechProvider,
    KnowlezSttProvider,
    SttProvider,
    provider_from_settings,
)
from app.services.usage import UsageService, estimate_stt_cost

router = APIRouter(prefix="/stt", tags=["stt"])

# Audio budget (DoS / cost). The 60 s duration cap is client-side and
# bypassable via direct API calls, so THIS is the real guard: 1.5 MB
# brackets ~90 s of opus voice (browser opus ~32-64 kbps => ~0.4-0.8 MB
# for 90 s) with headroom over the UI cap, but admits nothing close to
# multi-minute abuse. Pinned by test_transcribe_size_cap_pins_90s_budget.
MAX_AUDIO_BYTES = int(1.5 * 1024 * 1024)

# Cost-DoS guard (THREAT_MODEL): every call forwards to a paid cloud
# provider. Same 30/min per staff member as the turn-capture endpoint.
TRANSCRIBE_LIMITER = FixedWindowRateLimiter(limit=30, window_seconds=60.0)


def rate_limited_transcribe(
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
) -> None:
    if not TRANSCRIBE_LIMITER.allow(str(current_staff.staff_id)):
        raise HTTPException(
            status_code=429,
            detail="Too many transcription requests; try again in a minute",
        )


def get_stt_provider(
    settings: Settings = Depends(get_settings),
    db: Session | None = Depends(get_tenant_db),
) -> SttProvider | None:
    """ADR-10 precedence: an ACTIVE stored STT credential beats the env var.
    Which adapter wraps that stored key is decided by STT_PROVIDER — the
    key itself carries no vendor identity, unlike an env-only credential
    where the *_KEY var it came from is the tell. With no stored row the
    env path (FEAT-03) runs exactly as before."""
    if db is not None:
        try:
            stored, _model = CredentialService(db, settings).resolve_with_model("stt")
        except CredentialConfigError:
            stored = None
        if stored:
            if settings.STT_PROVIDER == "knowlez":
                return KnowlezSttProvider(key=stored, language=settings.STT_LANGUAGE)
            if settings.AZURE_SPEECH_REGION:
                return AzureSpeechProvider(
                    key=stored,
                    region=settings.AZURE_SPEECH_REGION,
                    language=settings.STT_LANGUAGE,
                )
    return provider_from_settings(settings)


@router.post("/transcribe")
def transcribe(
    audio: UploadFile = File(...),
    current_staff: CurrentStaff = Depends(get_current_verified_staff),
    _: None = Depends(rate_limited_transcribe),
    __: CurrentStaff = Depends(require_active_staff),
    provider: SttProvider | None = Depends(get_stt_provider),
    db: Session = Depends(get_tenant_db),
):
    if provider is None:
        raise HTTPException(
            status_code=503,
            detail="Speech-to-text is not configured; use the text input",
        )

    payload = audio.file.read(MAX_AUDIO_BYTES + 1)
    if len(payload) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio too large")

    try:
        transcript = provider.transcribe(payload)
    except Exception:
        # Never surface provider internals (MUST-NOT #1).
        raise HTTPException(status_code=502, detail="Transcription failed")

    # Usage ledger: exactly one row per ACTUAL successful provider call
    # (cost-DoS visibility, RISK_REGISTER). Failed/unconfigured calls log
    # nothing — nothing was billed. Same transaction as the response.
    UsageService(db).record(
        staff_id=current_staff.staff_id,
        institution_id=current_staff.institution_id,
        provider="stt",
        call_type="transcribe",
        estimated_cost=estimate_stt_cost(len(payload)),
    )

    return envelope({"transcript": transcript, "language": provider.language})
