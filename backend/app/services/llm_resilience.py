"""LLM resilience — fallback provider + circuit breaker.

ai-agent-development.md's production gate: "Fallback provider + circuit
breaker required." Behaviour:

- primary call raises LLMError → the fallback (a second OpenAI-compatible
  endpoint from env config) serves the same call immediately;
- N consecutive primary failures OPEN the breaker — while open the primary
  is skipped entirely (no wasted paid calls, no latency pile-up); after the
  cooldown ONE probe decides close (recovered) vs reopen (still failing);
- no fallback configured → LLMError propagates (clean 502 at the endpoint).
  The deterministic synthetic engine is NEVER a resilience fallback for a
  configured model — silently substituting rules for reasoning would
  misrepresent the product.
"""

from __future__ import annotations

import time
from typing import Callable, Protocol


class _Completer(Protocol):
    last_call_cost: object

    def complete(self, *, agent: str, tier: str, system: str, user: str) -> str: ...


class CircuitBreaker:
    """Fixed-threshold breaker with cooldown + single half-open probe."""

    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        recovery_seconds: float = 60.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self._threshold = failure_threshold
        self._recovery_seconds = recovery_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None
        self._probe_in_flight = False

    @property
    def is_open(self) -> bool:
        return self._opened_at is not None

    def allow_primary(self) -> bool:
        """Closed → always allow. Open → allow exactly one probe once the
        cooldown has elapsed; deny while the probe is in flight."""
        if self._opened_at is None:
            return True
        if self._clock() - self._opened_at < self._recovery_seconds:
            return False
        if self._probe_in_flight:
            return False
        self._probe_in_flight = True
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._probe_in_flight = False

    def record_failure(self) -> None:
        if self._probe_in_flight:
            # Probe failed — stay open, restart the cooldown.
            self._opened_at = self._clock()
            self._probe_in_flight = False
            return
        self._failures += 1
        if self._failures >= self._threshold:
            self._opened_at = self._clock()


class ResilientLLM:
    """Primary + optional fallback behind a circuit breaker.

    `last_call_cost` mirrors whichever provider served the last call so the
    usage ledger keeps a best-effort estimate across failovers.
    """

    def __init__(
        self,
        primary: _Completer,
        *,
        fallback: _Completer | None = None,
        breaker: CircuitBreaker | None = None,
    ):
        self._primary = primary
        self._fallback = fallback
        self._breaker = breaker or CircuitBreaker()
        self.last_call_cost = None

    def complete(self, *, agent: str, tier: str, system: str, user: str) -> str:
        from app.services.llm import LLMError

        kwargs = dict(agent=agent, tier=tier, system=system, user=user)
        if self._breaker.allow_primary():
            try:
                result = self._primary.complete(**kwargs)
            except LLMError:
                self._breaker.record_failure()
                if self._fallback is None:
                    raise
            else:
                self._breaker.record_success()
                self.last_call_cost = getattr(self._primary, "last_call_cost", None)
                return result
        elif self._fallback is None:
            raise LLMError("LLM circuit breaker is open and no fallback is configured")

        result = self._fallback.complete(**kwargs)  # may raise — propagates
        self.last_call_cost = getattr(self._fallback, "last_call_cost", None)
        return result
