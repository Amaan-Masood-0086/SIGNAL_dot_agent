"""Output budgets are OFF, deliberately — and this pins why.

Capping `max_tokens` per tier looked like the obvious fix for a concluding
turn that reached 89 seconds. It broke the pipeline on the first turn:
`deepseek-v4-flash` spends its budget on internal reasoning before emitting
anything, so a 400-token ceiling left nothing for the reply and the model
returned an EMPTY string — AgentContractError, turn lost.

A cap is a guess about a specific model's reasoning overhead, and guessing
low does not slow a turn down, it destroys it. These tests exist so nobody
reintroduces a blanket cap without measuring first.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.llm import (
    MAX_TOKENS_BY_TIER,
    TIER_CHEAP,
    TIER_MID,
    TIER_STRONG,
    OpenAICompatibleLLM,
)


def _capture(monkeypatch) -> list[dict]:
    sent: list[dict] = []

    def fake_post(url, **kwargs):
        sent.append(kwargs["json"])
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={"choices": [{"message": {"content": '{"ok": true}'}}]},
        )

    monkeypatch.setattr("app.services.llm.httpx.post", fake_post)
    return sent


@pytest.mark.parametrize("tier", [TIER_CHEAP, TIER_MID, TIER_STRONG])
def test_no_cap_is_sent_when_none_is_configured(monkeypatch, tier):
    """The empty default must mean "omit the field", not "send null" — a
    provider handed max_tokens=None can reject the whole request."""
    sent = _capture(monkeypatch)
    provider = OpenAICompatibleLLM(api_key="k", model="m", base_url="https://x")
    provider.complete(agent="a", tier=tier, system="s", user="u")

    assert "max_tokens" not in sent[0], (
        "a budget was sent for a tier with none configured — an under-budget "
        "cap returns an empty completion and costs the caretaker the turn"
    )


def test_a_configured_cap_is_honoured(monkeypatch):
    """The mechanism still works for whoever measures a model properly."""
    monkeypatch.setitem(MAX_TOKENS_BY_TIER, TIER_STRONG, 1500)
    sent = _capture(monkeypatch)
    provider = OpenAICompatibleLLM(api_key="k", model="m", base_url="https://x")
    provider.complete(agent="a", tier=TIER_STRONG, system="s", user="u")

    assert sent[0]["max_tokens"] == 1500


def test_configuring_one_tier_does_not_cap_the_others(monkeypatch):
    monkeypatch.setitem(MAX_TOKENS_BY_TIER, TIER_STRONG, 1500)
    sent = _capture(monkeypatch)
    provider = OpenAICompatibleLLM(api_key="k", model="m", base_url="https://x")
    provider.complete(agent="a", tier=TIER_CHEAP, system="s", user="u")

    assert "max_tokens" not in sent[0]


def test_temperature_stays_deterministic(monkeypatch):
    """Screening output must be reproducible (ADR-06)."""
    sent = _capture(monkeypatch)
    provider = OpenAICompatibleLLM(api_key="k", model="m", base_url="https://x")
    provider.complete(agent="a", tier=TIER_STRONG, system="s", user="u")
    assert sent[0]["temperature"] == 0.0


def test_an_empty_completion_is_reported_as_a_contract_error():
    """The signature of an under-budget cap. It must fail loudly rather than
    be mistaken for a model that simply had nothing to say."""
    from app.services.pipeline_agents import AgentContractError, _parse_agent_json

    with pytest.raises(AgentContractError) as excinfo:
        _parse_agent_json("")
    assert "not JSON" in str(excinfo.value)
