"""A transient provider hiccup must not cost the caretaker their turn.

Measured against Gemini's free tier on 2026-09-06: roughly half of first
calls came back **HTTP 503 "model overloaded"**, and a direct retry seconds
later succeeded. With no retry, `complete()` raised `LLMError` on the first
hop, the reasoning endpoint mapped it to 502 "Reasoning failed", and the
caretaker lost both their input and one of only five turns — for a condition
that clears in about a second.

`ResilientLLM` does not cover this. It fails over to a SECOND endpoint, which
only exists when `LLM_FALLBACK_API_KEY` is configured, and it treats the
primary as broken rather than busy. Overload is not a broken provider.

The distinction that matters here is transient vs. terminal:

  * 500/502/503/504 — the provider is busy or briefly unwell. Retrying is
    the correct response, and it demonstrably recovers within a second.
  * 400/401/403/404 — the request or the credential is wrong. Retrying is
    pointless, and it turns a clear configuration error into a slow one.
    A bad API key must fail immediately and say so.
  * 429 — looks transient, is not. Gemini's 429 carries `retryDelay: 55s`
    and names `GenerateRequestsPerDayPerProjectPerModel` — a DAILY cap. A
    one-second backoff cannot help with either, so retrying only delays
    telling the operator the budget is gone rather than the key being wrong.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.llm import LLMError, OpenAICompatibleLLM


def _ok_payload(text: str = '{"ok": true}') -> dict:
    return {
        "choices": [{"message": {"content": text}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


class _Sequence:
    """Replays a scripted list of responses, recording the calls made."""

    def __init__(self, *statuses: int):
        self.statuses = list(statuses)
        self.calls = 0

    def __call__(self, url, **kwargs):
        status = self.statuses[min(self.calls, len(self.statuses) - 1)]
        self.calls += 1
        return httpx.Response(
            status_code=status,
            json=_ok_payload() if status == 200 else {"error": {"message": "busy"}},
            request=httpx.Request("POST", url),
        )


@pytest.fixture()
def provider():
    return OpenAICompatibleLLM(
        api_key="k", model="m", base_url="https://example.invalid/v1"
    )


def _call(provider):
    return provider.complete(agent="observation", tier="cheap", system="s", user="u")


# ── transient: retry ────────────────────────────────────────────────────────


@pytest.mark.parametrize("status", [500, 502, 503, 504])
def test_transient_status_is_retried_and_succeeds(monkeypatch, provider, status):
    seq = _Sequence(status, 200)
    monkeypatch.setattr(httpx, "post", seq)
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    assert _call(provider) == '{"ok": true}'
    assert seq.calls == 2, f"HTTP {status} should have been retried once"


def test_a_network_error_is_retried_too(monkeypatch, provider):
    """`httpx.HTTPError` covers a dropped connection — the same transient
    class as a 503, and previously also fatal on the first hop."""
    calls = {"n": 0}

    def flaky(url, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("connection reset")
        return httpx.Response(200, json=_ok_payload(), request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", flaky)
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    assert _call(provider) == '{"ok": true}'
    assert calls["n"] == 2


def test_retries_are_bounded_and_then_fail_closed(monkeypatch, provider):
    """A provider that is down stays down: retry cannot become a hang.

    Three attempts, then LLMError — which the endpoint turns into a clean
    502. Unbounded retry against a 90s-timeout call would leave the
    caretaker staring at a spinner for minutes.
    """
    seq = _Sequence(503)
    monkeypatch.setattr(httpx, "post", seq)
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    with pytest.raises(LLMError):
        _call(provider)
    assert seq.calls == 3


def test_backoff_grows_between_attempts(monkeypatch, provider):
    """Immediate retries hammer a provider that is already overloaded."""
    slept: list[float] = []
    monkeypatch.setattr(httpx, "post", _Sequence(503))
    monkeypatch.setattr("app.services.llm.time.sleep", slept.append)

    with pytest.raises(LLMError):
        _call(provider)
    assert slept == sorted(slept) and len(slept) == 2, slept
    assert slept[0] > 0


# ── terminal: do NOT retry ──────────────────────────────────────────────────


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422, 429])
def test_terminal_status_fails_immediately(monkeypatch, provider, status):
    """A wrong key or a model name that does not exist is a configuration
    error. Retrying it three times makes an operator wait to be told
    something the first response already said."""
    seq = _Sequence(status)
    monkeypatch.setattr(httpx, "post", seq)
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    with pytest.raises(LLMError):
        _call(provider)
    assert seq.calls == 1, f"HTTP {status} must not be retried"


def test_the_status_code_still_reaches_the_error_message(monkeypatch, provider):
    """The operator-facing log has to say WHICH failure it was; 401 and 503
    call for opposite actions."""
    monkeypatch.setattr(httpx, "post", _Sequence(401))
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    with pytest.raises(LLMError, match="401"):
        _call(provider)


def test_a_successful_first_call_makes_exactly_one_request(monkeypatch, provider):
    """Retry must not change the happy path: one turn, one billed call."""
    seq = _Sequence(200)
    monkeypatch.setattr(httpx, "post", seq)
    assert _call(provider) == '{"ok": true}'
    assert seq.calls == 1


def test_quota_exhaustion_says_the_credential_is_fine(monkeypatch, provider):
    """429 and 401 need opposite responses from an operator. "rejected the
    call (HTTP 429)" sent one to check a key that was never the problem."""
    monkeypatch.setattr(httpx, "post", _Sequence(429))
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    with pytest.raises(LLMError, match="quota exhausted"):
        _call(provider)


def test_a_bad_key_and_a_bad_model_name_are_told_apart(monkeypatch, provider):
    monkeypatch.setattr("app.services.llm.time.sleep", lambda _: None)

    monkeypatch.setattr(httpx, "post", _Sequence(401))
    with pytest.raises(LLMError, match="credential"):
        _call(provider)

    monkeypatch.setattr(httpx, "post", _Sequence(404))
    with pytest.raises(LLMError, match="model"):
        _call(provider)
