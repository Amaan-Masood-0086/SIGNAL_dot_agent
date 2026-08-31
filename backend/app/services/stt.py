"""Speech-to-text seam (FEAT-03).

TRD locks "Cloud Urdu STT (Azure Speech, ur-PK)" and web-development.md locks
the capture path "Browser MediaRecorder API → backend STT endpoint". This
module is the provider seam: a small protocol plus an Azure Speech REST
adapter (short-audio transcription — no vendor SDK, httpx only). Audio is
processed in memory and NEVER persisted (data minimization; caretaker voices
are sensitive data).

The text fallback path never touches this module — zero STT dependency is a
FEAT-03 acceptance criterion.
"""

from __future__ import annotations

from typing import Protocol

import httpx

from app.core.config import Settings


class SttProvider(Protocol):
    """Anything that turns audio bytes into transcript text."""

    language: str

    def transcribe(self, audio: bytes) -> str: ...


class AzureSpeechProvider:
    """Azure Speech REST short-audio transcription (NextaSol WA VoiceAgent
    pattern: plain HTTP call with the subscription key, no SDK)."""

    def __init__(self, *, key: str, region: str, language: str):
        self._key = key
        self._region = region
        self.language = language

    def transcribe(self, audio: bytes) -> str:
        url = (
            f"https://{self._region}.stt.speech.microsoft.com"
            "/speech/recognition/conversation/cognitiveservices/v1.0"
        )
        response = httpx.post(
            url,
            params={"language": self.language},
            headers={
                "Ocp-Apim-Subscription-Key": self._key,
                # MediaRecorder emits webm/opus; Azure accepts ogg/opus —
                # forward as ogg so browser capture works without re-encoding.
                "Content-Type": "audio/ogg; codecs=opus",
                "Accept": "application/json",
            },
            content=audio,
            timeout=30.0,
        )
        response.raise_for_status()
        return str(response.json().get("DisplayText", ""))


def provider_from_settings(settings: Settings) -> SttProvider | None:
    """Resolve the configured provider; None = STT disabled (voice UI then
    degrades gracefully and the text fallback carries the product)."""
    if settings.STT_PROVIDER == "azure":
        if not settings.AZURE_SPEECH_KEY or not settings.AZURE_SPEECH_REGION:
            return None
        return AzureSpeechProvider(
            key=settings.AZURE_SPEECH_KEY,
            region=settings.AZURE_SPEECH_REGION,
            language=settings.STT_LANGUAGE,
        )
    return None
