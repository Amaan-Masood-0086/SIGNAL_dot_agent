"""Fixed-window rate limiter (FEAT-03 hardening).

TRD §4 / THREAT_MODEL Cost-DoS: 30 req/min per staff member on the per-turn
capture surface. Keyed by the JWT's staff identity — never anything client
can spoof (IP is ignored: multiple staff legitimately share NAT egress IPs,
and X-Forwarded-For is untrusted here).

In-process fixed window: correct for a single instance. TRD §1 already locks
Redis as the cache/rate-limit layer for the multi-instance architecture; swap
this module's storage then, the call sites stay unchanged.
"""

from __future__ import annotations

import threading
import time


class FixedWindowRateLimiter:
    """Allows `limit` calls per `window_seconds` per key."""

    def __init__(self, *, limit: int, window_seconds: float):
        self.limit = limit
        self.window_seconds = window_seconds
        # Injectable clock so tests can advance time without sleeping.
        self._now = time.monotonic
        self._lock = threading.Lock()
        # key -> (window_start, count); sync endpoints run on a threadpool.
        self._windows: dict[str, tuple[float, int]] = {}

    def allow(self, key: str) -> bool:
        now = self._now()
        with self._lock:
            window_start, count = self._windows.get(key, (0.0, 0))
            if now - window_start >= self.window_seconds:
                window_start, count = now, 0
            if count >= self.limit:
                self._windows[key] = (window_start, count)
                return False
            self._windows[key] = (window_start, count + 1)
            return True
