"""LLM resilience — fallback provider + circuit breaker.

ai-agent-development.md: "Fallback provider + circuit breaker required
before this is considered production-ready." Phase-1 single-provider is a
documented known limitation; this closes it:

- primary call fails → the configured fallback serves the same call;
- repeated primary failures OPEN the breaker → the primary is skipped
  entirely (no wasted paid calls, no latency pile-up) until a cooldown
  elapses, then one probe decides close-vs-reopen;
- with no fallback configured, failures surface as LLMError (clean 502 at
  the endpoint) — the deterministic synthetic engine is NEVER silently
  substituted for a configured model.
"""

from __future__ import annotations

import pytest


class CountingProvider:
    def __init__(self, *, fail: bool = False, text: str = "ok", cost=None):
        self.fail = fail
        self.text = text
        self.calls = 0
        self.last_call_cost = cost

    def complete(self, *, agent, tier, system, user):
        self.calls += 1
        if self.fail:
            from app.services.llm import LLMError

            raise LLMError("primary down")
        return self.text


def _call(provider):
    return provider.complete(
        agent="risk_reasoning", tier="strong", system="s", user="u"
    )


# ── cost model: usage_log.estimated_cost for LLM calls ──────────────────────


def test_adapter_computes_cost_from_token_usage(monkeypatch):
    from decimal import Decimal

    from app.core.config import Settings
    from app.services.llm import OpenAICompatibleLLM, provider_from_settings

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY="unused",
        JWT_PUBLIC_KEY="unused",
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-x",
        LLM_MODEL="gpt-4o-mini",
        LLM_COST_PER_MILLION_INPUT=0.15,
        LLM_COST_PER_MILLION_OUTPUT=0.60,
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, OpenAICompatibleLLM)

    def fake_post(url, **kwargs):
        return __import__("httpx").Response(
            200,
            request=__import__("httpx").Request("POST", url),
            json={
                "choices": [{"message": {"content": "{}"}}],
                "usage": {"prompt_tokens": 1000, "completion_tokens": 500},
            },
        )

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    _call(provider)
    # 1000 * 0.15/1e6 + 500 * 0.60/1e6 = 0.00015 + 0.00030 = 0.00045
    assert provider.last_call_cost == Decimal("0.000450")


def test_adapter_cost_is_none_without_usage_block(monkeypatch):
    from app.core.config import Settings
    from app.services.llm import OpenAICompatibleLLM, provider_from_settings

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY="unused",
        JWT_PUBLIC_KEY="unused",
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-x",
        LLM_MODEL="gpt-4o-mini",
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, OpenAICompatibleLLM)

    def fake_post(url, **kwargs):
        return __import__("httpx").Response(
            200,
            request=__import__("httpx").Request("POST", url),
            json={"choices": [{"message": {"content": "{}"}}]},
        )

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    _call(provider)
    assert provider.last_call_cost is None


# ── fallback + circuit breaker ───────────────────────────────────────────────


def test_primary_success_never_touches_fallback():
    from app.services.llm_resilience import ResilientLLM

    primary = CountingProvider(text="primary")
    fallback = CountingProvider(text="fallback")
    provider = ResilientLLM(primary, fallback=fallback)
    assert _call(provider) == "primary"
    assert primary.calls == 1 and fallback.calls == 0


def test_primary_failure_falls_back_immediately():
    from app.services.llm_resilience import ResilientLLM

    primary = CountingProvider(fail=True)
    fallback = CountingProvider(text="fallback")
    provider = ResilientLLM(primary, fallback=fallback)
    assert _call(provider) == "fallback"
    assert primary.calls == 1 and fallback.calls == 1


def test_no_fallback_propagates_llm_error():
    from app.services.llm import LLMError
    from app.services.llm_resilience import ResilientLLM

    primary = CountingProvider(fail=True)
    provider = ResilientLLM(primary, fallback=None)
    with pytest.raises(LLMError):
        _call(provider)


def test_breaker_opens_after_consecutive_failures_and_skips_primary():
    from app.services.llm_resilience import CircuitBreaker, ResilientLLM

    primary = CountingProvider(fail=True)
    fallback = CountingProvider(text="fallback")
    breaker = CircuitBreaker(failure_threshold=3, recovery_seconds=60.0)
    provider = ResilientLLM(primary, fallback=fallback, breaker=breaker)

    for _ in range(3):
        assert _call(provider) == "fallback"
    assert primary.calls == 3

    # Breaker open: the primary is not even attempted now.
    assert _call(provider) == "fallback"
    assert primary.calls == 3
    assert fallback.calls == 4


def test_breaker_probe_closes_on_recovery():
    from app.services.llm_resilience import CircuitBreaker, ResilientLLM

    clock = {"now": 0.0}
    primary = CountingProvider(fail=True)
    fallback = CountingProvider(text="fallback")
    breaker = CircuitBreaker(
        failure_threshold=2, recovery_seconds=30.0, clock=lambda: clock["now"]
    )
    provider = ResilientLLM(primary, fallback=fallback, breaker=breaker)

    _call(provider)
    _call(provider)  # breaker opens
    assert breaker.is_open

    # Advance past the cooldown — the next call probes the primary.
    clock["now"] = 31.0
    primary.fail = False
    primary.text = "recovered"
    assert _call(provider) == "recovered"
    assert not breaker.is_open

    # Subsequent calls go straight to the primary again.
    assert _call(provider) == "recovered"
    assert fallback.calls == 2  # only the two pre-open calls


def test_breaker_probe_reopens_on_continued_failure():
    from app.services.llm_resilience import CircuitBreaker, ResilientLLM

    clock = {"now": 0.0}
    primary = CountingProvider(fail=True)
    fallback = CountingProvider(text="fallback")
    breaker = CircuitBreaker(
        failure_threshold=1, recovery_seconds=10.0, clock=lambda: clock["now"]
    )
    provider = ResilientLLM(primary, fallback=fallback, breaker=breaker)

    _call(provider)  # one failure opens the breaker
    assert breaker.is_open

    clock["now"] = 11.0
    assert _call(provider) == "fallback"  # probe failed → open again
    assert breaker.is_open


def test_resilient_provider_exposes_underlying_cost():
    from decimal import Decimal

    from app.services.llm_resilience import ResilientLLM

    primary = CountingProvider(fail=True, cost=Decimal("0.001"))
    fallback = CountingProvider(text="fallback", cost=Decimal("0.0002"))
    provider = ResilientLLM(primary, fallback=fallback)
    _call(provider)
    assert provider.last_call_cost == Decimal("0.0002")  # from the fallback


def test_provider_from_settings_wires_fallback_when_configured():
    from app.core.config import Settings
    from app.services.llm_resilience import ResilientLLM
    from app.services.llm import provider_from_settings

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY="unused",
        JWT_PUBLIC_KEY="unused",
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-primary",
        LLM_MODEL="gpt-4o-mini",
        LLM_FALLBACK_API_KEY="sk-fallback",
        LLM_FALLBACK_MODEL="gpt-4o-mini-fallback",
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, ResilientLLM)


def test_provider_from_settings_plain_adapter_without_fallback():
    from app.core.config import Settings
    from app.services.llm import OpenAICompatibleLLM, provider_from_settings
    from app.services.llm_resilience import ResilientLLM

    settings = Settings(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY="unused",
        JWT_PUBLIC_KEY="unused",
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-primary",
        LLM_MODEL="gpt-4o-mini",
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, OpenAICompatibleLLM)
    assert not isinstance(provider, ResilientLLM)
