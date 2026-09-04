"""Provider status + minimal test-connection calls (ADR-09).

ADR-09 locks API keys to environment variables: the admin panel shows
configured/not-configured status and can fire ONE minimal real call to prove
the credentials work. This module is the only place that touches provider
credentials at runtime — and it returns success/failure + a sanitized detail
string ONLY. Key values are never returned, logged, or stored.
"""

from __future__ import annotations

import httpx

from app.core.config import Settings

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
KNOWLEZ_USAGE_URL = "https://api-stt.knowlez.com/v1/usage"
# Minimal real calls: cheap enough that a curious admin clicking "test"
# cannot drive meaningful cost, real enough to prove the credential works.
TEST_TIMEOUT_SECONDS = 15.0


def stt_configured(settings: Settings) -> bool:
    if settings.STT_PROVIDER == "azure":
        return bool(settings.AZURE_SPEECH_KEY) and bool(settings.AZURE_SPEECH_REGION)
    if settings.STT_PROVIDER == "knowlez":
        return bool(settings.KNOWLEZ_STT_API_KEY)
    return False


def llm_configured(settings: Settings) -> bool:
    return settings.LLM_PROVIDER != "none" and bool(settings.LLM_API_KEY)


def provider_statuses(
    settings: Settings,
    *,
    stt_key_source: str | None = None,
    llm_key_source: str | None = None,
) -> list[dict]:
    """Status cards for the admin panel — presence + source only, NEVER
    values. `*_key_source` says where the ACTIVE key lives (ADR-10
    precedence): "ui" = provider_credentials row, "env" = env var, None =
    not configured. With no stored credential the env logic is exactly the
    ADR-09 behavior."""
    if stt_key_source is not None:
        # Stored credential: which vendor it belongs to is decided by
        # STT_PROVIDER (the key itself carries no vendor identity). Azure
        # additionally needs a region from env; Knowlez needs nothing else.
        if settings.STT_PROVIDER == "knowlez":
            stt_ok = True
            stt_backend = "knowlez"
            stt_detail = f"Knowlez Speech-to-Text configured via {stt_key_source}"
        else:
            stt_ok = bool(settings.AZURE_SPEECH_REGION)
            stt_backend = "azure"
            stt_detail = (
                f"Azure Speech configured via {stt_key_source}"
                if stt_ok
                else "Stored STT credential present but AZURE_SPEECH_REGION is missing"
            )
        stt_source = stt_key_source if stt_ok else None
    else:
        stt_ok = stt_configured(settings)
        stt_backend = settings.STT_PROVIDER if stt_ok else "none"
        stt_source = "env" if stt_ok else None
        stt_detail = (
            f"{stt_backend} configured via env"
            if stt_ok
            else "Speech-to-text is not configured (text fallback active)"
        )

    if llm_key_source is not None:
        llm_ok = True
        llm_backend = (
            settings.LLM_PROVIDER if settings.LLM_PROVIDER != "none"
            else "openai_compatible"
        )
        llm_source = llm_key_source
        llm_detail = f"{llm_backend} configured via {llm_key_source}"
    else:
        llm_ok = llm_configured(settings)
        llm_backend = settings.LLM_PROVIDER if settings.LLM_PROVIDER != "none" else "none"
        llm_source = "env" if llm_ok else None
        llm_detail = (
            f"{settings.LLM_PROVIDER} configured via env"
            if llm_ok
            else "LLM provider is not configured"
        )

    return [
        {
            "provider": "stt",
            "backend": stt_backend,
            "configured": stt_ok,
            "detail": stt_detail,
            "source": stt_source,
        },
        {
            "provider": "llm",
            "backend": llm_backend,
            "configured": llm_ok,
            "detail": llm_detail,
            "source": llm_source,
        },
    ]


def test_stt_connection(settings: Settings, *, key: str | None = None) -> tuple[bool, str]:
    """One minimal authenticated call — Azure issueToken or Knowlez's usage
    endpoint — proves the Speech key works without uploading any audio (and,
    for Knowlez, without spending a transcription credit). `key` overrides
    the env value (ADR-10 precedence — callers pass whichever source is
    active). Which vendor's check runs is decided by STT_PROVIDER. Returns
    (success, sanitized detail)."""
    if settings.STT_PROVIDER == "knowlez":
        effective_key = key if key is not None else settings.KNOWLEZ_STT_API_KEY
        if not effective_key:
            return False, "STT provider is not configured"
        try:
            response = httpx.get(
                KNOWLEZ_USAGE_URL,
                headers={"x-api-key": effective_key},
                timeout=TEST_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError:
            return False, "Provider unreachable"
        if response.status_code == 200:
            return True, "Credentials accepted by provider"
        return False, f"Provider rejected the credentials (HTTP {response.status_code})"

    if key is None and not stt_configured(settings):
        return False, "STT provider is not configured"
    effective_key = key if key is not None else settings.AZURE_SPEECH_KEY
    if not effective_key or not settings.AZURE_SPEECH_REGION:
        return False, "STT provider is not configured"
    url = (
        f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"
        "/sts/v1.0/issueToken"
    )
    try:
        response = httpx.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": effective_key},
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        # Sanitized: never surface provider internals (MUST-NOT #1).
        return False, "Provider unreachable"
    if response.status_code == 200:
        return True, "Credentials accepted by provider"
    return False, f"Provider rejected the credentials (HTTP {response.status_code})"


def test_llm_connection(
    settings: Settings, *, key: str | None = None, model: str | None = None
) -> tuple[bool, str]:
    """One trivial OpenAI-compatible chat completion (max_tokens=1). `key`
    and `model` override the env values (ADR-10 precedence) — a stored
    model override (e.g. a non-OpenAI model on a DB-stored key) must be
    honored here exactly as it is by the real reasoning call, or this test
    silently pings the wrong model and reports a false negative."""
    if key is None and not llm_configured(settings):
        return False, "LLM provider is not configured"
    effective_key = key if key is not None else settings.LLM_API_KEY
    if not effective_key:
        return False, "LLM provider is not configured"
    effective_model = model or settings.LLM_MODEL or "gpt-4o-mini"
    base_url = (settings.LLM_BASE_URL or DEFAULT_LLM_BASE_URL).rstrip("/")
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {effective_key}"},
            json={
                "model": effective_model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
            },
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        return False, "Provider unreachable"
    if response.status_code == 200:
        return True, "Credentials accepted by provider"
    return False, f"Provider rejected the credentials (HTTP {response.status_code})"
