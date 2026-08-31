---
description: masterDataSDLC — Data/DB deep-dive module. Postgres/Redis security, RLS, migrations governance, PII retention, encryption, key rotation, backups, performance.
---

# masterDataSDLC: Data, Database Security & Governance Guide

## Purpose

This document is the **data + database security deep-dive module** that extends:

- `masterSDLC.md` — security foundation
- `A-SDLC.md` — AI orchestration (phase gates, automation)
- `masterBackendSDLC.md` — API/authZ patterns (IDOR, rate limiting)
- `masterCloudSDLC.md` — infra hardening (network, secrets, backups)

Use this file whenever the project stores data (PostgreSQL/MySQL/Mongo/Redis/etc.).  
It focuses on **PostgreSQL + Redis** as default, but the governance patterns apply everywhere.

---

## Document Information

| Field | Value |
|---|---|
| Version | 1.0 |
| Created | 2026-02-20 |
| Last Updated | 2026-02-20 |
| Scope | Universal (OLTP + caches + queues + analytics-lite) |
| Primary Standards | Privacy-by-design principles, secure DB operations patterns |
| Companion Docs | masterSDLC.md • A-SDLC.md • masterBackendSDLC.md • masterCloudSDLC.md |

---

## Table of Contents

1. [Data Classification & Governance](#1-data-classification--governance)
2. [PostgreSQL Security Baseline](#2-postgresql-security-baseline)
3. [Row-Level Security & Multi-Tenancy](#3-row-level-security--multi-tenancy)
4. [Schema & Migration Governance](#4-schema--migration-governance)
5. [PII Retention, Deletion, and Privacy](#5-pii-retention-deletion-and-privacy)
6. [Encryption, Keys, and Rotation](#6-encryption-keys-and-rotation)
7. [Redis Security & Caching Rules](#7-redis-security--caching-rules)
8. [Backups, Restore Drills, and PITR](#8-backups-restore-drills-and-pitr)
9. [Performance: Indexing, Query Tuning, Partitioning](#9-performance-indexing-query-tuning-partitioning)
10. [Non-Prod Data Safety (Masking & Synthetic Data)](#10-non-prod-data-safety-masking--synthetic-data)
11. [Monitoring & Alerting](#11-monitoring--alerting)
12. [Professional Documentation Outputs](#12-professional-documentation-outputs)
13. [Checklists](#13-checklists)

---

## 1. Data Classification & Governance

### 1.1 Data Classes (Baseline)

| Class | Examples | Rules |
|---|---|---|
| Public | marketing text | may be public |
| Internal | feature flags, configs | internal only |
| Confidential | business metrics, contracts | strict access + audit |
| Restricted (PII/PHI/Finance) | names, emails, CNIC, card data | encryption + audit + retention |

### 1.2 Data Ownership & Access (MUST)

- every table has an owner (service/team)
- access is role-based and least privilege
- production DB access is time-bound and logged

---

## 2. PostgreSQL Security Baseline

### 2.1 Connection Security

- TLS enforced
- no public internet access to DB (see masterCloudSDLC)
- use connection pooling (PgBouncer) if needed

### 2.2 Roles & Permissions

Recommended roles:
- `app_reader` (SELECT only)
- `app_writer` (INSERT/UPDATE/DELETE on specific tables)
- `migration_role` (DDL only, time-bound)
- `analytics_reader` (read replicas only)

**MUST:**
- no superuser in app code
- no shared credentials between environments

### 2.3 Auditing (Recommended)

- enable audit logging for sensitive tables/actions
- store audit logs with retention policy

---

## 3. Row-Level Security & Multi-Tenancy

### 3.1 When to Use RLS

Use RLS if:
- multi-tenant SaaS
- strict tenant isolation required
- risk of IDOR is high

### 3.2 RLS Pattern (Concept)

- every tenant-scoped table includes `tenant_id`
- set `app.tenant_id` on connection (or use `SET LOCAL`)
- RLS policy enforces `tenant_id = current_setting('app.tenant_id')::uuid`

**Rule:** RLS complements (does NOT replace) application-level authZ.

### 3.3 Migration Governance for RLS

- add `tenant_id` with NOT NULL + index
- backfill carefully with batch jobs
- enable RLS and policies
- verify with cross-tenant tests

---

## 4. Schema & Migration Governance

### 4.1 Non‑Negotiable Rules

- schema changes only via migrations
- migrations must be reviewed like code
- backward-compatible migrations preferred (zero downtime)

### 4.2 Zero‑Downtime Migration Pattern

- add new nullable column
- deploy app writing both old+new
- backfill data
- switch reads to new
- remove old later in a new release

### 4.3 Migration CI Gate

CI MUST:
- run migration on empty DB
- run migration on populated fixture DB
- run downgrade (if supported) or validate rollback plan

---

## 5. PII Retention, Deletion, and Privacy

### 5.1 Retention Policy (MUST)

Create `docs/DATA_RETENTION.md` containing:
- what data is collected
- why it is collected
- how long it is kept
- how it is deleted
- who can access it

### 5.2 Deletion Rules

- account deletion triggers:
  - delete PII fields OR anonymize (policy)
  - revoke tokens/sessions
  - delete files from storage
  - delete push tokens
- handle backups: define policy for backup purge (or legal hold exceptions)

### 5.3 Data Export

- provide a safe export format (JSON/CSV)
- verify request identity (step-up auth)
- log export event in audit logs

---

## 6. Encryption, Keys, and Rotation

### 6.1 Encryption at Rest

- use managed DB encryption where possible
- for highly sensitive fields: application-level encryption (pgcrypto or app crypto)

### 6.2 Encryption in Transit

- TLS for DB connections
- TLS for Redis connections (if outside same trusted network)

### 6.3 Key Rotation (MUST)

- define rotation cadence (see masterCloudSDLC)
- implement envelope encryption where needed
- store keys only in KMS/Secret Manager/Vault

---

## 7. Redis Security & Caching Rules

### 7.1 Redis as Cache vs Source of Truth

Redis is:
- cache
- session store
- rate limiting store
- lightweight queue (streams)

Redis is NOT:
- primary database for durable business data (unless explicitly designed)

### 7.2 Redis Security Baseline

- bind to private network only
- require AUTH (ACL users)
- enable TLS if needed
- disable dangerous commands where feasible
- set maxmemory + eviction policy intentionally

### 7.3 Caching Rules (MUST)

- never cache secrets
- never cache PII unless encrypted and policy-approved
- TTL required for all keys (no infinite cache)
- provide cache invalidation strategy (TTL/event/version)

---

## 8. Backups, Restore Drills, and PITR

### 8.1 Backup Baseline

- daily snapshots
- point-in-time recovery (PITR) for production
- encrypted backups
- access to backups is restricted

### 8.2 Restore Drills (MUST)

- monthly restore drill in staging
- document steps + timings (RTO measurement)
- verify data integrity post-restore

---

## 9. Performance: Indexing, Query Tuning, Partitioning

### 9.1 Indexing Rules

- index foreign keys
- use composite indexes for frequent filters
- avoid over-indexing (write penalty)
- periodically review unused indexes

### 9.2 Query Tuning Workflow

- capture slow queries
- run `EXPLAIN (ANALYZE, BUFFERS)`
- add indexes or rewrite query
- consider caching if appropriate

### 9.3 Partitioning

Partition if:
- table is huge (100M+ rows)
- queries are by time range or tenant

---

## 10. Non-Prod Data Safety (Masking & Synthetic Data)

### 10.1 Golden Rule

**Never use real production PII in dev/staging** unless explicitly approved and protected.

### 10.2 Masking Pattern

- replace emails/phones with deterministic masked values
- preserve referential integrity
- remove tokens/secrets

### 10.3 Synthetic Data

- generate synthetic datasets that mimic shape, not real identities
- keep dataset generation scripts in repo (non-sensitive)

---

## 11. Monitoring & Alerting

Minimum DB alerts:
- replication lag
- disk usage > 80%
- connections > 80%
- slow queries count spike
- deadlocks count spike

Redis alerts:
- memory > 80%
- evictions > 0
- CPU > 70%
- connected clients near max

---

## 12. Professional Documentation Outputs

Data work MUST produce:

- `docs/DATA_MODEL.md` (ERD description + key tables + ownership)
- `docs/MIGRATIONS.md` (rules + how to run + rollback plan)
- `docs/DATA_RETENTION.md` (policy)
- `docs/DB_RUNBOOK.md` (restore steps, emergency actions)
- `docs/SECURITY_DATA_CONTROLS.md` (RLS/encryption/audit)

---

## 13. Checklists

### 13.1 DB Change PR Checklist

- [ ] migration added and reviewed
- [ ] backward compatible (or downtime plan)
- [ ] indexes considered
- [ ] RLS policies updated (if multi-tenant)
- [ ] no PII leaked in logs/tests/fixtures
- [ ] restore/rollback plan updated

### 13.2 Pre-Prod Data Checklist

- [ ] staging uses masked or synthetic data
- [ ] backup retention configured
- [ ] PITR enabled (prod)
- [ ] access audited
