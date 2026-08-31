"""Synthetic-data enforcement gate.

TEST_PLAN_SIGNAL.md §2 business rule #7 / TRD §4 rule #7:
all data created outside the `ENVIRONMENT=synthetic_only` gate is rejected at
the application layer, not just the UI. This is Phase 1's single most
important control (RISK_REGISTER R8).

Every write path MUST call `assert_synthetic_write()` before persisting.
"""

from __future__ import annotations

from .config import get_settings


class SyntheticDataViolation(Exception):
    """A write attempted to persist non-synthetic data in a synthetic-only env."""


def assert_synthetic_write(is_synthetic: bool, environment: str | None = None) -> None:
    """Hard-reject a write whose record is not synthetic in a synthetic_only env.

    `environment` may be passed explicitly (tests); otherwise it is read from
    application settings. Fail-closed: anything not explicitly synthetic is
    treated as a violation.
    """
    env = environment if environment is not None else get_settings().ENVIRONMENT
    if env == "synthetic_only" and not is_synthetic:
        raise SyntheticDataViolation(
            "Non-synthetic data write rejected: ENVIRONMENT=synthetic_only is enforced "
            "at the application layer for all of Phase 1 (TRD business rule #7)."
        )
