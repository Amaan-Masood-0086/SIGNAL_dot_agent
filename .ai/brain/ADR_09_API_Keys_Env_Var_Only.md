# ADR-09: API Keys Stay Environment-Variable-Only — Admin Panel Shows Status, Not a Key-Entry Form

**Status:** Accepted
**Date:** 2026-08-31
**Decided by:** NextaSol (Akasha Azhar), flagged during Admin Panel / RBAC scoping

## Context

Building an admin panel surfaced a request to let an admin add/update the Azure Speech key and LLM provider key(s) through a web form. Doing this properly requires: encryption at rest, a key-management/rotation story, masked display (never show the full key again after save), and audit logging of every key change — a meaningfully complex secure subsystem in its own right, not a quick CRUD form. Building it hastily under hackathon time pressure is a worse outcome than not building it.

The current mechanism (`AZURE_SPEECH_KEY`, `AZURE_SPEECH_REGION`, `STT_PROVIDER` as environment variables, per FEAT-03) already works and requires no new security surface.

## Decision

API keys (Azure Speech, LLM providers) remain environment-variable/deployment-time configuration only. They are never entered, stored, or editable through the application UI or database in Phase 1.

The admin panel instead provides:
1. **Status display** — for each configured provider (STT, LLM), show configured / not configured, based on whether the relevant env vars are present at startup. Never display the key value itself, not even masked.
2. **Test-connection action** — an admin-only endpoint that fires a minimal real call to the configured provider (e.g., a 1-second silent-audio STT call, or a trivial LLM ping) and reports success/failure. Confirms credentials work without ever surfacing them.

## Consequences

- **Positive:** Zero new secrets-storage surface. No encryption-key-management problem to get right under time pressure. Matches the existing, already-working STT configuration pattern exactly.
- **Negative / accepted trade-off:** Rotating a key requires redeploying with a new environment variable, not a self-service UI action. Acceptable for Phase 1's single-demo-instance scale; revisit for Track B if a proper secrets manager (cloud KMS, Vault) is introduced.
- **Scope boundary:** This ADR governs provider credentials specifically. It does not affect staff authentication (JWT/passwords), which is a separate, already-designed system.
