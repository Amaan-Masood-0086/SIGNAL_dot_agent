---
description: masterBackendSDLC — Backend/API deep-dive module. OWASP API Top 10, authZ/IDOR prevention, rate limiting, queues, versioning, observability.
---

# masterBackendSDLC: Backend & API Security + Architecture Guide

## Purpose

This document is the **backend/API-specific deep-dive module** that extends:

- `masterSDLC.md` — Security foundation (OWASP, STRIDE, compliance, secure coding)
- `A-SDLC.md` — AI orchestration (roles, gates, deterministic stack selection, coding contracts)

Use this file whenever the project has **any backend** (REST/GraphQL/WebSockets/jobs).  
It is designed so an AI agent can produce **professional, production-grade backend systems** with security, quality, and observability baked in.

---

## Document Information

| Field | Value |
|---|---|
| Version | 1.0 |
| Created | 2026-02-20 |
| Last Updated | 2026-02-20 |
| Scope | Universal (monolith, microservices, serverless) |
| Primary Standards | OWASP API Security Top 10, OWASP ASVS (relevant controls), STRIDE |
| Companion Docs | masterSDLC.md • A-SDLC.md • masterCloudSDLC.md • masterDataSDLC.md |

---

## Table of Contents

1. [Backend Security Model](#1-backend-security-model)
2. [API Design Standards](#2-api-design-standards)
3. [Authentication Patterns](#3-authentication-patterns)
4. [Authorization Patterns & IDOR Prevention](#4-authorization-patterns--idor-prevention)
5. [Rate Limiting & Abuse Prevention](#5-rate-limiting--abuse-prevention)
6. [Input Validation, Output Safety, and Error Handling](#6-input-validation-output-safety-and-error-handling)
7. [Webhooks, Files, Realtime, and GraphQL Safety](#7-webhooks-files-realtime-and-graphql-safety)
8. [Background Jobs & Queue Security](#8-background-jobs--queue-security)
9. [API Versioning & Deprecation](#9-api-versioning--deprecation)
10. [Logging, Auditing, Observability](#10-logging-auditing-observability)
11. [Security Testing & IDOR Test Suite Templates](#11-security-testing--idor-test-suite-templates)
12. [Performance & Reliability Baselines](#12-performance--reliability-baselines)
13. [Professional Documentation Outputs](#13-professional-documentation-outputs)
14. [Checklists](#14-checklists)

---

## 1. Backend Security Model

### 1.1 Non‑Negotiable Rules (MUST)

- **All state-changing endpoints MUST require auth + authZ** (unless explicitly public).
- **All inputs MUST be validated** (schema-based; whitelist; length limits).
- **All sensitive actions MUST be audited** (who/what/when/where/result).
- **No secret in code. Ever.** (also no secrets in logs, errors, or client-visible responses).
- **Least privilege everywhere** (service accounts, DB roles, queue permissions).
- **Safe defaults:** deny-by-default authZ; strict CORS; secure headers; conservative rate limits.

### 1.2 Threat Model Cheat Sheet (Backend)

Typical threats to explicitly model (STRIDE + API threats):

- **Broken Object Level Authorization (BOLA / IDOR)**: user accesses someone else’s resource by guessing an ID.
- **Broken Function Level Authorization (BFLA)**: user accesses admin/privileged operations.
- **Mass assignment**: user sets fields they should not control.
- **Injection**: SQL/NoSQL/command/template injection.
- **SSR/SSRF**: backend fetches attacker-controlled URLs.
- **DoS & abuse**: brute force, credential stuffing, endpoint flooding.
- **Sensitive data exposure**: logs, error messages, backups, debug endpoints.

---

## 2. API Design Standards

### 2.1 Canonical API Response Envelope (RECOMMENDED)

Use a consistent response shape for all services:

```json
{
  "success": true,
  "data": { },
  "meta": {
    "request_id": "req_...",
    "timestamp": "2026-02-20T12:00:00Z",
    "version": "v1"
  }
}
```

Error:

```json
{
  "success": false,
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this resource"
  },
  "meta": {
    "request_id": "req_...",
    "timestamp": "2026-02-20T12:00:00Z"
  }
}
```

**Rule:** In production, never return stack traces, internal IDs, SQL errors, or “user exists” style info.

### 2.2 Endpoint Conventions

- REST: `/v1/resources/{id}`
- Collection queries MUST support:
  - pagination (`cursor` preferred) + `limit` caps
  - filtering (explicit allowlist)
  - sorting (explicit allowlist)
- Idempotent operations MUST be idempotent (see 2.4).

### 2.3 Pagination (Cursor Preferred)

**MUST:**
- cap `limit` (e.g., 100)
- return `next_cursor`
- stable ordering (usually by `created_at` + `id`)

### 2.4 Idempotency Keys (Payments / Orders / Mutations)

For endpoints that create resources or trigger side effects:

- Accept header: `Idempotency-Key: <uuid>`
- Persist key + request hash + response
- Key TTL: 24h (configurable)
- If same key reused with different payload → 409

---

## 3. Authentication Patterns

### 3.1 Recommended Baseline

- **Access token:** 15 minutes
- **Refresh token:** 7 days (or shorter for high security)
- **Cookies (web):** HttpOnly + Secure + SameSite
- **Mobile:** refresh token in secure storage (see masterMobileSDLC), access token in memory

### 3.2 Password Handling (MUST)

- Use **bcrypt** (cost 12+) or **argon2id**
- Never log passwords
- Enforce password policy (length 12+; breached password check optional)
- Lockout / throttling for failed logins

### 3.3 MFA & Step‑Up Auth

Require MFA or step-up auth for:
- admin actions
- password/email change
- payout/billing changes
- exporting personal data
- deleting data

### 3.4 Service-to-Service Auth

- **mTLS** for internal services (critical systems)
- OR signed JWT between services (short TTL, audience-bound)
- API Gateway should verify upstream identity

---

## 4. Authorization Patterns & IDOR Prevention

### 4.1 Golden Rule: AuthN ≠ AuthZ

Passing authentication is not enough. Every request must check:

- **Who** is calling (user/service identity)
- **What** resource is requested
- **Which** action is allowed on that resource
- **Why** (policy decision reason)

### 4.2 Object-Level Authorization (BOLA / IDOR Defense)

**MUST implement at least one of:**
1. Resource ownership check:
   - `resource.owner_id == current_user.id`
2. Tenant isolation:
   - `resource.tenant_id == current_user.tenant_id`
3. Policy engine (RBAC/ABAC):
   - `can(user, "resource:read", resource)`

**Never** trust client-provided IDs like `userId`, `tenantId`, `role`.

### 4.3 IDOR Test Suite Template (Drop‑in)

For each resource endpoint `/v1/X/{id}` generate tests:

- **T1:** User A can access own resource
- **T2:** User A cannot access User B resource (403, not 404 unless policy)
- **T3:** User A cannot enumerate IDs (rate limits + consistent errors)
- **T4:** Admin can access within admin scope only
- **T5:** Cross-tenant access denied (if multi-tenant)

**CI Gate:** these tests MUST run in Gate 6 (Validate).

### 4.4 Mass Assignment Defense

- Use allowlist DTOs / schemas
- Never bind request body directly to ORM models
- Mark server-controlled fields as read-only:
  - `role`, `is_admin`, `tenant_id`, `balance`, `status`, `created_at`

---

## 5. Rate Limiting & Abuse Prevention

### 5.1 Rate Limiting Strategy (Layered)

Layer 1: **Edge / WAF / CDN**
- block known bad bots
- basic DDoS protection

Layer 2: **API Gateway**
- global rate limits
- per-IP throttling

Layer 3: **Application**
- per-user limits
- per-endpoint limits
- special protection on auth endpoints

### 5.2 Recommended Defaults

| Category | Authenticated | Unauthenticated | Window |
|---|---:|---:|---|
| Login | 5 | 3 | 5 min |
| Register | 5 | 3 | 15 min |
| Password reset | 3 | 2 | 15 min |
| Read APIs | 120 | 30 | 1 min |
| Write APIs | 30 | N/A | 1 min |
| Admin APIs | 60 | N/A | 1 min |

**MUST:** return `429` with `Retry-After`.

### 5.3 Token Bucket Pattern (Redis)

- key: `rl:{scope}:{user_or_ip}:{endpoint}`
- store: tokens + last_refill timestamp
- use atomic Lua script or Redis INCR+EXPIRE pattern (careful)

---

## 6. Input Validation, Output Safety, and Error Handling

### 6.1 Validation (MUST)

- schema-based validation (Zod/Pydantic/Joi/etc.)
- length limits
- numeric bounds
- regex allowlists for identifiers
- file: mime/type, size, extension, content sniffing

### 6.2 Content Safety

- sanitize rich text input if stored/rendered
- never reflect raw user input in HTML emails without escaping
- safe template rendering (no template injection)

### 6.3 Error Handling

- internal logs keep details, user gets generic message
- consistent error codes
- correlation IDs (`request_id`), propagated end-to-end

---

## 7. Webhooks, Files, Realtime, and GraphQL Safety

### 7.1 Webhook Verification (MUST)

- verify signature (HMAC or asymmetric)
- timestamp tolerance (e.g., 5 minutes)
- idempotency: webhook event IDs stored to avoid replay
- only accept from allowlisted IPs when possible

### 7.2 File Upload Safety

- store outside web root
- random filenames (no user-controlled paths)
- virus scan (if feasible)
- size limits
- content-type validation + magic bytes sniffing
- presigned upload preferred (S3/GCS) + server-side metadata validation

### 7.3 Realtime (WebSockets/SSE)

- auth at connection time
- per-message authZ checks for sensitive channels
- message size limits
- rate limits per connection
- drop idle connections

### 7.4 GraphQL Security (If used)

- disable introspection in prod (or protect it)
- depth/complexity limits
- persisted queries
- field-level authZ checks
- per-operation rate limits

---

## 8. Background Jobs & Queue Security

### 8.1 Job Data Handling

- never put secrets in job payload
- encrypt payload if it contains PII (or store only IDs)
- idempotency: jobs MUST be safe to retry
- enforce max retries + dead-letter queue

### 8.2 Queue Permissions (MUST)

- producer and consumer permissions separated
- separate queues per environment (dev/staging/prod)
- audit job execution and failures
- sanitize logs (payload redaction)

### 8.3 Job Safety Contracts

A job handler MUST:
- validate inputs
- check authZ if triggered by user action
- enforce timeouts
- produce structured logs + metrics
- be idempotent

---

## 9. API Versioning & Deprecation

### 9.1 Versioning Options

Preferred: URL versioning  
- `/v1/...`

Acceptable: header-based  
- `Accept: application/vnd.company.v1+json`

**MUST:** choose one and document in TRD + README.

### 9.2 Backwards-Compatible Change Rules

Allowed without bump:
- adding optional fields
- adding new endpoints
- adding new enum values only if client is resilient

Requires bump:
- removing fields
- changing field meaning
- changing validation rules more strict
- changing auth requirements (unless tightening security; still document)

### 9.3 Deprecation Policy (Template)

- announce: T0
- warn headers: `Deprecation`, `Sunset`
- remove: T0 + 90 days (default)

---

## 10. Logging, Auditing, Observability

### 10.1 Structured Logging (MUST)

Every request log includes:
- request_id
- user_id (hashed or internal ID)
- tenant_id (if applicable)
- route + method
- status_code
- latency_ms
- ip (may be sensitive depending on policy)
- user_agent (optional)

### 10.2 Audit Logs (MUST for security-sensitive actions)

Audit events for:
- login/logout
- password reset
- permission changes
- data exports
- admin actions
- payment actions
- account deletion

**Audit logs must be append-only** and stored with retention policy (see masterDataSDLC).

### 10.3 Metrics & Tracing

Minimum metrics:
- request rate, error rate (4xx/5xx), latency p50/p95/p99
- queue depth + job failures
- DB slow queries count
- rate limit blocks count

Tracing:
- propagate `traceparent` + request_id
- instrument outgoing calls (db, redis, http)

---

## 11. Security Testing & IDOR Test Suite Templates

### 11.1 Mandatory Test Types

- Unit tests for services/policies/validators
- Integration tests for endpoints
- AuthZ tests (IDOR/BOLA/BFLA) for every resource type
- Negative tests:
  - invalid input
  - missing auth
  - expired tokens
  - forbidden actions
  - rate limit exceeded

### 11.2 Fuzz / Property Tests (Optional but recommended)

- fuzz parsers and validators
- fuzz file upload validator
- fuzz webhook signature verifier

### 11.3 DAST in Staging (Recommended)

- run OWASP ZAP baseline against staging
- ensure test credentials exist with minimal roles

---

## 12. Performance & Reliability Baselines

### 12.1 Baseline Targets (Starter)

- API p95 latency: < 500ms (excluding heavy jobs)
- error rate: < 1%
- DB p95 query: < 100ms for hot paths
- queue processing: within SLA

### 12.2 Reliability Patterns

- timeouts on all outbound requests
- retries with backoff (only for safe/idempotent ops)
- circuit breakers for dependencies
- graceful degradation

---

## 13. Professional Documentation Outputs

At minimum, backend work MUST produce:

- `docs/API_SPEC.md` (endpoints + schemas + auth + errors)
- `docs/SECURITY_MODEL.md` (authN/authZ, rate limits, threat model summary)
- `docs/OBSERVABILITY.md` (logs/metrics/traces + dashboards)
- `docs/RUNBOOK.md` (deploy, rollback, incident actions)
- `docs/ADR/` for major decisions

---

## 14. Checklists

### 14.1 Backend PR Checklist

- [ ] Input validation added/updated
- [ ] AuthZ checks implemented at object level
- [ ] IDOR tests added for new resource endpoints
- [ ] Rate limits enforced for new endpoints
- [ ] No PII in logs
- [ ] Error messages are generic in production
- [ ] Tests pass + coverage threshold met
- [ ] Security scans clean (no High/Critical)

### 14.2 Release Checklist (Backend)

- [ ] All migrations are backward compatible (or documented downtime)
- [ ] Feature flags in place for risky changes
- [ ] Observability dashboards updated
- [ ] Alerts configured for new endpoints/queues
- [ ] Rollback plan documented and tested
