# ADR-10: Admin-UI Editable Provider Credentials — Supersedes ADR-09's "Env-Var Only" Rule

**Status:** Accepted
**Date:** 2026-09-01
**Supersedes:** ADR-09 (env-var-only, status-display panel)
**Decided by:** Akasha Azhar, explicit reversal after reviewing ADR-09's original trade-off

## Context

ADR-09 deliberately avoided building a key-entry UI, reasoning that a hastily-built secrets-storage subsystem is a worse outcome than none. That concern is still valid — this ADR does not dismiss it, it answers it with specific controls, because the practical need (rotate/set keys without redeploying, let a non-technical team member configure a provider) now outweighs the deferral.

## Decision

Add a real, admin-only, write-only credential management surface. Specifically:

1. **New table `provider_credentials`** (system-level, not institution-scoped, same tier as `audit_log`): `id`, `provider` (`stt` | `llm`), `encrypted_value`, `masked_suffix` (last 4 chars, stored separately, unencrypted — display only), `is_active`, `created_by_staff_id`, `created_at`, `updated_at`.

2. **Encryption at rest** — symmetric encryption (Fernet) using a new required env var `CREDENTIAL_ENCRYPTION_KEY` (the app's master secret for this purpose). **This means one env var still exists** — the master key, never the provider keys themselves. Losing/leaking `CREDENTIAL_ENCRYPTION_KEY` compromises all stored credentials, so it must be protected with at least the same rigor as `JWT_SECRET_KEY` (never committed, never logged, rotated via redeploy if ever suspected leaked).

3. **Write-only API contract**: `PUT /admin/credentials/{provider}` accepts and stores a new value. **No endpoint, no response body, no log line, ever returns the decrypted value.** `GET /admin/credentials` returns `{provider, is_active, masked_suffix, updated_at}` only — enough to confirm "yes, something ending in ...ab12 is configured, set on this date," never the value.

4. **Precedence rule**: an active DB-stored credential for a provider takes priority over the equivalent environment variable. If no active DB row exists, the system falls back to the environment variable (preserves the current `.env` path as a valid bootstrap/CI mechanism — nothing from ADR-03/04/05/09's earlier work breaks).

5. **Controls carried over from ADR-09, unchanged**: admin-only (`get_current_admin_staff`), every save/delete is audit-logged (actor, provider, timestamp — never the value), rate-limited, and the existing "Test Connection" status-check endpoint continues to work against whichever source (DB or env) is currently active.

## Consequences

- **Positive:** Keys can be rotated or set through the app without a redeploy; a non-technical admin can configure a provider; the existing env-var path still works for automation/CI, nothing is removed.
- **Negative / accepted trade-off:** Real new attack surface — a table that, if the encryption key and the database were both compromised, exposes provider credentials. This is a materially different risk profile than ADR-09's "nothing to steal" position. Accepted because the controls above (encryption, write-only contract, audit, admin-only, rate limit) are the standard mitigations for exactly this class of feature, not a shortcut version of them.
- **Operational requirement:** `CREDENTIAL_ENCRYPTION_KEY` must be set before this feature can be used at all; document this in deployment notes so it isn't missed and isn't casually regenerated (regenerating it makes all previously-stored credentials undecryptable — needs a documented rotation procedure, out of scope for Phase 1, flag as a Track B item).
- **ADR-09 is not deleted** — its reasoning stays valid history; this ADR documents why the trade-off moved.
