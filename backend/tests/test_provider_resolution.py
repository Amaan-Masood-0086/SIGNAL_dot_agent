"""Provider resolution gate — SyntheticRuleLLM must ONLY engage when
LLM_PROVIDER=none AND the environment is synthetic_only.

With real keys configured (LLM_PROVIDER/LLM_API_KEY/LLM_MODEL in .env) the
OpenAI-compatible adapter wins and the deterministic fallback is never
constructed. Outside synthetic_only, an unconfigured pipeline fails to a
clean 503 instead of silently substituting a rule engine.
"""

from __future__ import annotations


def _settings(**overrides):
    from app.core.config import Settings

    base = dict(
        _env_file=None,
        ENVIRONMENT="synthetic_only",
        JWT_PRIVATE_KEY="unused",
        JWT_PUBLIC_KEY="unused",
    )
    base.update(overrides)
    return Settings(**base)


def test_configured_llm_wins_over_synthetic_fallback():
    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM

    provider = get_reasoning_provider(
        _settings(
            LLM_PROVIDER="openai_compatible",
            LLM_API_KEY="sk-real",
            LLM_MODEL="gpt-4o-mini",
        )
    )
    assert isinstance(provider, OpenAICompatibleLLM)


def test_synthetic_fallback_only_when_unconfigured_and_synthetic_only():
    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.synthetic_llm import SyntheticRuleLLM

    provider = get_reasoning_provider(_settings())  # LLM_PROVIDER defaults "none"
    assert isinstance(provider, SyntheticRuleLLM)


def test_no_provider_outside_synthetic_only_when_unconfigured():
    from app.api.v1.endpoints.reasoning import get_reasoning_provider

    provider = get_reasoning_provider(_settings(ENVIRONMENT="staging"))
    assert provider is None


def test_synthetic_fallback_never_engages_with_partial_config():
    """LLM_PROVIDER set but key missing = not configured; under synthetic_only
    that still falls back (demo keeps working), but the adapter itself must
    not be constructed from a half-config."""
    from app.api.v1.endpoints.reasoning import get_reasoning_provider
    from app.services.llm import OpenAICompatibleLLM
    from app.services.synthetic_llm import SyntheticRuleLLM

    provider = get_reasoning_provider(_settings(LLM_PROVIDER="openai_compatible"))
    assert not isinstance(provider, OpenAICompatibleLLM)
    assert isinstance(provider, SyntheticRuleLLM)
