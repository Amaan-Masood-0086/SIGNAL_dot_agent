"""Synthetic-data enforcement gate — TEST_PLAN_SIGNAL.md §2, business rule #7.

`ENVIRONMENT=synthetic_only` is the single most important Phase 1 control
(RISK_REGISTER R8). These tests prove the gate rejects non-synthetic writes
at the application layer and can never be silently bypassed.
"""

from __future__ import annotations

import pytest


def test_environment_is_required_not_silently_defaulted(monkeypatch):
    """`ENVIRONMENT` is explicitly set — never defaults silently (pre-deploy checklist)."""
    from pydantic import ValidationError

    from app.core.config import Settings

    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_synthetic_write_rejected_when_not_synthetic():
    """Write with is_synthetic=false under synthetic_only → hard rejection."""
    from app.core.synthetic_gate import SyntheticDataViolation, assert_synthetic_write

    with pytest.raises(SyntheticDataViolation):
        assert_synthetic_write(is_synthetic=False, environment="synthetic_only")


def test_synthetic_write_allowed_when_synthetic():
    from app.core.synthetic_gate import assert_synthetic_write

    assert_synthetic_write(is_synthetic=True, environment="synthetic_only")  # no raise


def test_app_boot_refuses_missing_environment(monkeypatch):
    """The app must not start if ENVIRONMENT is unset — fail secure, not fail open.

    Dotenv is excluded so a developer's local backend/.env can't mask the
    failure; the gate must hold on OS environment alone.
    """
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    from app.core import config as config_module

    original_settings = config_module.Settings

    def no_dotenv_settings():
        return original_settings(_env_file=None)

    config_module.get_settings.cache_clear()
    monkeypatch.setattr(config_module, "Settings", no_dotenv_settings)
    with pytest.raises(Exception):
        config_module.get_settings()
