"""LLM provider seam (FEAT-05) — provider-agnostic wrapper per ADR-01 /
ai-agent-development.md ("never hard-code a call to one vendor's SDK
directly in agent code").

Mirrors the FEAT-03 STT seam: a protocol + an OpenAI-compatible REST
adapter (httpx only, no vendor SDK) + resolution from Settings. The RBAC
ticket's env-only config (ADR-09) is consumed unchanged: LLM_PROVIDER /
LLM_API_KEY / LLM_MODEL / LLM_BASE_URL.
"""

from __future__ import annotations

import pytest


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


def test_no_provider_when_llm_disabled():
    from app.services.llm import provider_from_settings

    assert provider_from_settings(_settings()) is None  # LLM_PROVIDER defaults "none"


def test_no_provider_when_key_missing():
    from app.services.llm import provider_from_settings

    settings = _settings(LLM_PROVIDER="openai_compatible", LLM_MODEL="gpt-4o-mini")
    assert provider_from_settings(settings) is None


def test_provider_resolved_when_configured():
    from app.services.llm import OpenAICompatibleLLM, provider_from_settings

    settings = _settings(
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-test",
        LLM_MODEL="gpt-4o-mini",
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, OpenAICompatibleLLM)


def test_complete_posts_chat_completion_with_tier_and_agent(monkeypatch):
    """One HTTP call per complete(); agent + tier travel as metadata (usage
    attribution), the wire payload is a plain chat completion."""
    from app.services.llm import OpenAICompatibleLLM, provider_from_settings

    settings = _settings(
        LLM_PROVIDER="openai_compatible",
        LLM_API_KEY="sk-sentinel",
        LLM_MODEL="gpt-4o-mini",
        LLM_BASE_URL="https://llm.example.test/v1/",
    )
    provider = provider_from_settings(settings)
    assert isinstance(provider, OpenAICompatibleLLM)

    calls = []

    def fake_post(url, **kwargs):
        calls.append((url, kwargs))
        return __import__("httpx").Response(
            200,
            request=__import__("httpx").Request("POST", url),
            json={"choices": [{"message": {"content": '{"ok": true}'}}]},
        )

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)

    text = provider.complete(
        agent="risk_reasoning",
        tier="strong",
        system="SYSTEM PROMPT",
        user="USER PROMPT",
    )
    assert text == '{"ok": true}'
    assert len(calls) == 1
    url, kwargs = calls[0]
    assert url == "https://llm.example.test/v1/chat/completions"  # trailing / handled
    assert kwargs["headers"]["Authorization"] == "Bearer sk-sentinel"
    body = kwargs["json"]
    assert body["model"] == "gpt-4o-mini"
    assert body["messages"] == [
        {"role": "system", "content": "SYSTEM PROMPT"},
        {"role": "user", "content": "USER PROMPT"},
    ]


def test_complete_maps_provider_failure_to_llm_error(monkeypatch):
    from app.services.llm import LLMError, provider_from_settings

    provider = provider_from_settings(
        _settings(
            LLM_PROVIDER="openai_compatible",
            LLM_API_KEY="sk-sentinel",
            LLM_MODEL="gpt-4o-mini",
        )
    )

    def fake_post(url, **kwargs):
        return __import__("httpx").Response(
            401, request=__import__("httpx").Request("POST", url), content=b"denied"
        )

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    with pytest.raises(LLMError):
        provider.complete(agent="observation", tier="cheap", system="s", user="u")


def test_complete_maps_network_error_to_llm_error(monkeypatch):
    from app.services.llm import LLMError, provider_from_settings

    provider = provider_from_settings(
        _settings(
            LLM_PROVIDER="openai_compatible",
            LLM_API_KEY="sk-sentinel",
            LLM_MODEL="gpt-4o-mini",
        )
    )

    def fake_post(url, **kwargs):
        raise __import__("httpx").ConnectError("unreachable")

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    with pytest.raises(LLMError):
        provider.complete(agent="observation", tier="cheap", system="s", user="u")
