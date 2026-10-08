"""Embedding seam for optional semantic retrieval (ADR-11).

Any OpenAI-compatible `/embeddings` endpoint. The text sent is the caretaker's
observation (or a knowledge-base description) — never a name, ID or
institution, the same boundary as the LLM calls. Every failure raises
`EmbeddingError`; callers treat that as "fall back to full context", never as
"retrieve less".
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from typing import Protocol

import httpx

from app.core.config import Settings
from app.db.vector import EMBEDDING_DIMENSIONS


class EmbeddingError(Exception):
    """Embedding unavailable or malformed. Message is for server logs only."""


class Embedder(Protocol):
    model: str

    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OpenAICompatibleEmbedder:
    def __init__(self, *, base_url: str, model: str, api_key: str, timeout: float):
        self._url = base_url.rstrip("/") + "/embeddings"
        self.model = model
        self._api_key = api_key
        self._timeout = timeout

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = httpx.post(
                self._url,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": self.model, "input": list(texts)},
                timeout=self._timeout,
            )
            response.raise_for_status()
            data = sorted(response.json()["data"], key=lambda item: item["index"])
            vectors = [[float(x) for x in item["embedding"]] for item in data]
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            raise EmbeddingError(f"embedding request failed: {type(exc).__name__}") from exc
        if len(vectors) != len(texts):
            raise EmbeddingError("embedding count does not match input count")
        for vector in vectors:
            if len(vector) != EMBEDDING_DIMENSIONS:
                raise EmbeddingError(
                    f"expected {EMBEDDING_DIMENSIONS} dimensions, got {len(vector)}"
                )
        return vectors


def get_embedder(settings: Settings) -> Embedder | None:
    """None when not configured — the caller then uses full context."""
    if not (settings.EMBEDDING_BASE_URL and settings.EMBEDDING_MODEL and settings.EMBEDDING_API_KEY):
        return None
    return OpenAICompatibleEmbedder(
        base_url=settings.EMBEDDING_BASE_URL,
        model=settings.EMBEDDING_MODEL,
        api_key=settings.EMBEDDING_API_KEY,
        timeout=settings.EMBEDDING_TIMEOUT_SECONDS,
    )


def embedding_text(description: str) -> str:
    return description.strip()


def embedding_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
