"""Application settings.

`ENVIRONMENT` has NO default on purpose: the pre-deploy checklist requires
it to be explicitly set, never silently defaulted (sdlc-security.md). A
missing ENVIRONMENT must fail the boot, not fail open.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required — fail secure if absent. Phase 1 value: "synthetic_only".
    ENVIRONMENT: str

    # Required (ADR-10) — Fernet master key for provider_credentials
    # encryption at rest. No default on purpose: the credential surface must
    # fail secure, not fail open. Same protection rigor as the JWT keys —
    # never committed, never logged. Generate: python -m
    # cryptography.fernet  (or Fernet.generate_key()).
    CREDENTIAL_ENCRYPTION_KEY: str

    # Postgres connection — PRIVILEGED path.
    #
    # Two paths exist on purpose (audit F1). This one is used where the work
    # legitimately spans institutions and therefore cannot run under RLS:
    #   - /auth/token, which finds a staff row by email BEFORE any
    #     institution is known
    #   - the admin console's documented cross-institution reads
    DATABASE_URL: str = (
        "postgresql+psycopg://signal_app:signal_app@localhost:5432/signal_dev"
    )

    # Postgres connection — TENANT path. Connects as the unprivileged
    # `signal_app` role (no superuser, no BYPASSRLS) so the RLS policies
    # created in migration 0001 actually bind. Every caretaker-facing
    # endpoint runs here, and the isolation no longer depends on a handler
    # remembering its WHERE clause. Falls back to DATABASE_URL when unset so
    # existing single-URL setups keep working.
    TENANT_DATABASE_URL: str | None = None

    # JWT (RS256 per sdlc-security.md OWASP A02). Keys are PEM strings from
    # environment variables — secrets never live in code.
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    JWT_ISSUER: str = "signal-api"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # Speech-to-text seam (FEAT-03). "none" = voice transcription disabled;
    # the text fallback never depends on this (FEAT-03 acceptance).
    # "azure" | "knowlez" | "none" — decides which adapter wraps whichever
    # key is active (env or ADR-10 stored credential); it does not itself
    # carry a key.
    STT_PROVIDER: str = "none"
    STT_LANGUAGE: str = "ur-PK"
    # Azure Speech credentials — environment-only, never code (MUST #6).
    AZURE_SPEECH_KEY: str | None = None
    AZURE_SPEECH_REGION: str | None = None
    # Info Inlet "Knowlez" Speech-to-Text (api-stt.knowlez.com) — a second
    # OWASP-equivalent env-only credential path, added 2026-09-01. No region
    # concept: one key is the whole credential.
    KNOWLEZ_STT_API_KEY: str | None = None

    # LLM provider seam (consumed by FEAT-05's reasoning pipeline). Per
    # ADR-09 the keys stay environment-only: the admin panel shows status +
    # test-connection, never a key-entry form. "none" = not configured.
    LLM_PROVIDER: str = "none"
    LLM_API_KEY: str | None = None
    LLM_MODEL: str | None = None
    # OpenAI-compatible base URL; defaults to OpenAI's own API.
    LLM_BASE_URL: str | None = None
    # Resilience (ai-agent-development.md production gate): an optional
    # second endpoint used when the primary fails / its circuit opens.
    LLM_FALLBACK_API_KEY: str | None = None
    LLM_FALLBACK_MODEL: str | None = None
    LLM_FALLBACK_BASE_URL: str | None = None
    # Best-effort cost model for usage_log.estimated_cost ($ per 1M tokens);
    # defaults bracket gpt-4o-mini, override per real contract.
    LLM_COST_PER_MILLION_INPUT: float = 0.15
    LLM_COST_PER_MILLION_OUTPUT: float = 0.60


@lru_cache
def get_settings() -> Settings:
    return Settings()
