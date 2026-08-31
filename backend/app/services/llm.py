"""LLM provider seam (FEAT-05) — provider-agnostic, no vendor SDK.

ADR-01 / ai-agent-development.md: agent code never hard-codes one vendor.
This mirrors the FEAT-03 STT seam exactly: protocol + OpenAI-compatible
REST adapter (httpx only) + resolution from Settings (the RBAC ticket's
env-only config per ADR-09 — LLM_PROVIDER / LLM_API_KEY / LLM_MODEL /
LLM_BASE_URL).

Model tiering (ai-agent-development.md): `tier` rides along every call as
metadata (cheap=Observation, strong=Risk Reasoning, mid=Explanation). At
Phase-1 single-model config the same model serves all tiers; the tier is
recorded on the usage ledger and honored by any future multi-model adapter.
Fallback provider + circuit breaker are Track-B scope — documented known
limitation, not a silent gap.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Protocol

import httpx

from app.core.config import Settings

TIER_CHEAP = "cheap"
TIER_MID = "mid"
TIER_STRONG = "strong"

AGENT_OBSERVATION = "observation"
AGENT_RISK_REASONING = "risk_reasoning"
AGENT_EXPLANATION = "explanation"

DEFAULT_LLM_BASE_URL = "https://api.openai.com/v1"
LLM_TIMEOUT_SECONDS = 60.0


class LLMError(RuntimeError):
    """Provider failure — mapped to a clean 502 upstream, never surfaced raw."""


class LLMProvider(Protocol):
    """Anything that turns (system, user) prompts into completion text."""

    def complete(self, *, agent: str, tier: str, system: str, user: str) -> str: ...


class OpenAICompatibleLLM:
    """OpenAI-compatible chat-completions REST adapter.

    Sets `last_call_cost` after every successful call (best-effort, from the
    response's token usage + the configured per-million rates) so the usage
    ledger can carry an estimate; stays None when the provider reports no
    usage block.
    """

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        cost_per_million_input: float = 0.15,
        cost_per_million_output: float = 0.60,
    ):
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._input_rate = Decimal(str(cost_per_million_input))
        self._output_rate = Decimal(str(cost_per_million_output))
        self.last_call_cost: Decimal | None = None

    @property
    def api_key(self) -> str:
        """In-process access only (precedence checks in tests / test-call
        seam). Never serialized into any API response — response schemas
        have no field for it (ADR-09/10)."""
        return self._api_key

    def complete(self, *, agent: str, tier: str, system: str, user: str) -> str:
        try:
            response = httpx.post(
                f"{self._base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.0,  # screening output must be reproducible
                },
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except httpx.HTTPError as exc:
            raise LLMError("LLM provider unreachable") from exc
        if response.status_code != 200:
            raise LLMError(
                f"LLM provider rejected the call (HTTP {response.status_code})"
            )
        try:
            payload = response.json()
            text = str(payload["choices"][0]["message"]["content"])
        except (KeyError, IndexError, ValueError) as exc:
            raise LLMError("LLM provider returned an unexpected payload") from exc
        self.last_call_cost = self._estimate_cost(payload.get("usage"))
        return text

    def _estimate_cost(self, usage: dict | None) -> Decimal | None:
        if not isinstance(usage, dict):
            return None
        prompt_tokens = usage.get("prompt_tokens")
        completion_tokens = usage.get("completion_tokens")
        if not isinstance(prompt_tokens, int) or not isinstance(completion_tokens, int):
            return None
        per_million = Decimal(1_000_000)
        cost = (
            Decimal(prompt_tokens) * self._input_rate
            + Decimal(completion_tokens) * self._output_rate
        ) / per_million
        return cost.quantize(Decimal("0.000001"))


def build_llm_provider(settings: Settings, *, api_key: str) -> "LLMProvider":
    """Construct the (optionally resilient) provider around ONE key. Shared
    by the env path and the ADR-10 stored-credential path so both get the
    identical cost model + fallback wiring."""
    primary = OpenAICompatibleLLM(
        api_key=api_key,
        model=settings.LLM_MODEL or "gpt-4o-mini",
        base_url=settings.LLM_BASE_URL or DEFAULT_LLM_BASE_URL,
        cost_per_million_input=settings.LLM_COST_PER_MILLION_INPUT,
        cost_per_million_output=settings.LLM_COST_PER_MILLION_OUTPUT,
    )
    if not settings.LLM_FALLBACK_API_KEY:
        return primary
    from app.services.llm_resilience import ResilientLLM

    fallback = OpenAICompatibleLLM(
        api_key=settings.LLM_FALLBACK_API_KEY,
        model=settings.LLM_FALLBACK_MODEL or settings.LLM_MODEL or "gpt-4o-mini",
        base_url=settings.LLM_FALLBACK_BASE_URL or DEFAULT_LLM_BASE_URL,
        cost_per_million_input=settings.LLM_COST_PER_MILLION_INPUT,
        cost_per_million_output=settings.LLM_COST_PER_MILLION_OUTPUT,
    )
    return ResilientLLM(primary, fallback=fallback)


def provider_from_settings(settings: Settings) -> LLMProvider | None:
    """Resolve the ENV-VAR provider; None = no LLM configured via env.

    ADR-10 precedence lives at the call sites (reasoning endpoint): an
    active stored credential wins over this env path, which stays the
    bootstrap/CI mechanism exactly as FEAT-05 shipped it (the FEAT-05
    smoke script uses this function directly — unchanged).
    """
    if settings.LLM_PROVIDER == "none" or not settings.LLM_API_KEY:
        return None
    return build_llm_provider(settings, api_key=settings.LLM_API_KEY)
