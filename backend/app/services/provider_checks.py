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
# Minimal real calls: cheap enough that a curious admin clicking "test"
# cannot drive meaningful cost, real enough to prove the credential works.
TEST_TIMEOUT_SECONDS = 15.0


def stt_configured(settings: Settings) -> bool:
    return (
        settings.STT_PROVIDER == "azure"
        and bool(settings.AZURE_SPEECH_KEY)
        and bool(settings.AZURE_SPEECH_REGION)
    )


def llm_configured(settings: Settings) -> bool:
    return settings.LLM_PROVIDER != "none" and bool(settings.LLM_API_KEY)


def provider_statuses(settings: Settings) -> list[dict]:
    """Status cards for the admin panel — env presence only, never values."""
    stt_ok = stt_configured(settings)
    llm_ok = llm_configured(settings)
    return [
        {
            "provider": "stt",
            "backend": "azure" if settings.STT_PROVIDER == "azure" else "none",
            "configured": stt_ok,
            "detail": (
                "Azure Speech configured"
                if stt_ok
                else "Speech-to-text is not configured (text fallback active)"
            ),
        },
        {
            "provider": "llm",
            "backend": settings.LLM_PROVIDER if settings.LLM_PROVIDER != "none" else "none",
            "configured": llm_ok,
            "detail": (
                f"{settings.LLM_PROVIDER} configured"
                if llm_ok
                else "LLM provider is not configured"
            ),
        },
    ]


def test_stt_connection(settings: Settings) -> tuple[bool, str]:
    """One minimal authenticated call: Azure issueToken proves the Speech key
    works without uploading any audio. Returns (success, sanitized detail)."""
    if not stt_configured(settings):
        return False, "STT provider is not configured"
    url = (
        f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"
        "/sts/v1.0/issueToken"
    )
    try:
        response = httpx.post(
            url,
            headers={"Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY or ""},
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except httpx.HTTPError:
        # Sanitized: never surface provider internals (MUST-NOT #1).
        return False, "Provider unreachable"
    if response.status_code == 200:
        return True, "Credentials accepted by provider"
    return False, f"Provider rejected the credentials (HTTP {response.status_code})"


def test_llm_connection(settings: Settings) -> tuple[bool, str]:
    """One trivial OpenAI-compatible chat completion (max_tokens=1)."""
    if not llm_configured(settings):
        return False, "LLM provider is not configured"
    base_url = (settings.LLM_BASE_URL or DEFAULT_LLM_BASE_URL).rstrip("/")
    try:
        response = httpx.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"},
            json={
                "model": settings.LLM_MODEL or "gpt-4o-mini",
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
