"""Regressions for three PR-review findings on the audit remediation.

Each of these guards a property that was already TRUE in intent and quietly
untrue in code, which is the same shape as the original audit findings.
"""

from __future__ import annotations

import decimal

import pytest

from app.api.deps import _verified_tenant_engine
from app.core.config import Settings
from app.schemas.admin import UsageTotals, cost_or_none
from app.services import pipeline_agents
from app.services.pipeline_agents import AgentContractError, _parse_agent_json


# ── Tenant session must fail closed, not fall back (review comment 3) ────────


def _settings(**over) -> Settings:
    base = dict(
        ENVIRONMENT="test",
        DATABASE_URL="postgresql+psycopg://signal:x@localhost:5432/signal_dev",
        SECRET_KEY="x" * 40,
        CREDENTIAL_ENCRYPTION_KEY="MeogHhAdoVZ279u9hf3BlSQxH3rqq89e538bAoC8tQg=",
    )
    base.update(over)
    return Settings(**base)


def test_missing_tenant_url_refuses_instead_of_using_the_privileged_one():
    """The old fallback made forgetting one setting revert the whole F1 fix.

    A privileged connection cannot be told apart from a working one by
    looking at responses, so this has to raise rather than degrade.
    """
    with pytest.raises(RuntimeError) as exc:
        _verified_tenant_engine(_settings(TENANT_DATABASE_URL=None))
    message = str(exc.value)
    assert "TENANT_DATABASE_URL" in message
    # The error has to name the fix, not just the symptom.
    assert "signal_app" in message


def test_error_never_leaks_the_connection_string():
    """A DB URL carries a password; the refusal must not become the leak."""
    secret = "postgresql+psycopg://signal:sup3rs3cret@localhost:5432/signal_dev"
    with pytest.raises(RuntimeError) as exc:
        _verified_tenant_engine(_settings(TENANT_DATABASE_URL=None, DATABASE_URL=secret))
    assert "sup3rs3cret" not in str(exc.value)


# ── Agent parse failures must not log model output (review comment 2) ────────


def _captured_log_call(monkeypatch) -> list:
    """Record what `_parse_agent_json` hands the logger, verbatim.

    Deliberately NOT `caplog`: something later in the suite reconfigures
    logging and the records never reach the fixture, so a caplog assertion
    passes alone and fails in a full run — which is the least useful kind of
    test. Intercepting the call captures the format string AND the arguments
    before any handler is involved, which is also the exact place PHI would
    enter if it ever came back.
    """
    calls: list = []
    monkeypatch.setattr(
        pipeline_agents._log, "error", lambda *args, **kw: calls.append(args)
    )
    return calls


def test_parse_failure_logs_shape_not_content(monkeypatch):
    """Agent output is caretaker text and clinical detail — PHI in a log.

    The diagnostic value that mattered (empty vs prose) survives as a
    classification; the content itself never reaches the logger.
    """
    calls = _captured_log_call(monkeypatch)
    phi = 'The child Ayesha has not spoken since her mother died. {"grade":'

    with pytest.raises(AgentContractError):
        _parse_agent_json(phi)

    assert len(calls) == 1
    rendered = calls[0][0] % calls[0][1:]
    assert "shape=prose" in rendered
    # Nothing the model wrote may appear, in the message or the arguments.
    for secret in ("Ayesha", "mother", "spoken"):
        assert secret not in rendered
        assert not any(secret in str(arg) for arg in calls[0])


def test_empty_output_is_still_distinguishable(monkeypatch):
    """The bug this logging was added for: a model that returns nothing.

    An empty reply and prose need OPPOSITE fixes (raise the token budget vs
    fix the prompt), so dropping the raw prefix must not cost that answer.
    """
    calls = _captured_log_call(monkeypatch)

    with pytest.raises(AgentContractError):
        _parse_agent_json("")

    rendered = calls[0][0] % calls[0][1:]
    assert "shape=empty" in rendered
    assert "len=0" in rendered


def test_shape_classifier_covers_the_contract_failures():
    assert pipeline_agents._output_shape("") == "empty"
    assert pipeline_agents._output_shape('{"grade"') == "json-object-truncated"
    assert pipeline_agents._output_shape('[{"a": 1}]') == "json-array"
    assert pipeline_agents._output_shape("Sure! Here you go") == "prose"


# ── Cost must tell "free" from "not recorded" (review comment 4) ─────────────


def test_no_calls_is_a_real_zero():
    assert cost_or_none(0, None) == 0.0


def test_calls_with_no_recorded_cost_is_unknown_not_zero():
    """An LLM test connection is a real billed call priced at NULL.

    Reporting it as $0.00 under-reports a figure an operator reconciles
    against a vendor invoice.
    """
    assert cost_or_none(3, None) is None


def test_a_genuine_zero_survives():
    """The STT provider test hits a free endpoint and records Decimal("0").

    The previous `float(x) if x else 0.0` sent this down the fallback branch
    too, so a free provider and an unpriced one were already indistinguishable
    before NULLs were considered.
    """
    assert cost_or_none(2, decimal.Decimal("0")) == 0.0


def test_partial_pricing_is_declared_rather_than_hidden():
    """SUM skips NULLs, so a partial total otherwise reads as complete."""
    totals = UsageTotals.from_counts(13, 10, decimal.Decimal("0.42"))
    assert totals.calls == 13
    assert totals.estimated_cost == pytest.approx(0.42)
    assert totals.unpriced_calls == 3


def test_fully_priced_reports_nothing_outstanding():
    totals = UsageTotals.from_counts(4, 4, decimal.Decimal("1.25"))
    assert totals.unpriced_calls == 0
    assert totals.estimated_cost == pytest.approx(1.25)
