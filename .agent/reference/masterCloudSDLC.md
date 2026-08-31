---
description: masterCloudSDLC — Cloud/IaC deep-dive module. Terraform/K8s hardening, IAM least privilege, network segmentation, WAF/CDN, secrets, CI/CD, DR.
---

# masterCloudSDLC: Cloud, Infrastructure-as-Code & DevSecOps Guide

## Purpose

This document is the **cloud + infrastructure deep-dive module** that extends:

- `masterSDLC.md` — Security foundation (processes, threat modeling, secure coding)
- `A-SDLC.md` — AI orchestration (roles, gates, automation)
- `masterBackendSDLC.md` — API security patterns
- `masterDataSDLC.md` — data/DB security patterns

Use this file whenever the project has:
- CI/CD pipelines
- containers (Docker)
- Kubernetes
- Terraform/Pulumi/IaC
- cloud resources (AWS/GCP/Azure)
- secrets management and runtime hardening requirements

---

## Document Information

| Field | Value |
|---|---|
| Version | 1.0 |
| Created | 2026-02-20 |
| Last Updated | 2026-02-20 |
| Scope | Universal (AWS/GCP/Azure + PaaS) |
| Primary Standards | CIS Benchmarks (conceptual), OWASP DevSecOps guidance, NIST principles (conceptual) |
| Companion Docs | masterSDLC.md • A-SDLC.md • masterBackendSDLC.md • masterDataSDLC.md |

---

## Table of Contents

1. [Golden Cloud Architecture](#1-golden-cloud-architecture)
2. [Infrastructure-as-Code Standards](#2-infrastructure-as-code-standards)
3. [IAM Least Privilege Templates](#3-iam-least-privilege-templates)
4. [Network Segmentation & Zero Trust](#4-network-segmentation--zero-trust)
5. [Secrets Management & Key Rotation](#5-secrets-management--key-rotation)
6. [Container & Supply Chain Security](#6-container--supply-chain-security)
7. [Kubernetes Hardening](#7-kubernetes-hardening)
8. [CI/CD DevSecOps Pipeline](#8-cicd-devsecops-pipeline)
9. [Observability, SLOs, and Alerting](#9-observability-slos-and-alerting)
10. [Backups, Disaster Recovery, and Rollback](#10-backups-disaster-recovery-and-rollback)
11. [Cost Governance & FinOps](#11-cost-governance--finops)
12. [Professional Documentation Outputs](#12-professional-documentation-outputs)
13. [Checklists](#13-checklists)

---

## 1. Golden Cloud Architecture

### 1.1 Default Secure Topology (Reference)

```
Internet
  │
  ▼
CDN + WAF (TLS termination, bot protection, rate limits)
  │
  ▼
Load Balancer / API Gateway
  │
  ├─► Public Subnet (only LB)
  │
  ▼
Private Subnets (apps)
  │
  ├─► App containers / pods (no public IPs)
  │
  ├─► Internal services (queues, workers)
  │
  ▼
Private Data Subnets
  ├─► Database (no public access)
  └─► Cache (Redis) (private only)
```

**MUST:**
- DB and cache are never public.
- app workloads have no direct internet exposure (except via gateway/LB).
- outbound internet from private subnets uses NAT (or egress proxy).

### 1.2 HTTPS/TLS Baseline

- enforce TLS 1.2+ (TLS 1.3 preferred)
- HSTS for web
- rotate certs automatically (ACME/managed)
- pinning on mobile where appropriate (see masterMobileSDLC)

### 1.3 Environments

Minimum environments:
- `dev` (non-prod, isolated)
- `staging` (prod-like, DAST runs here)
- `prod` (production)

**Rule:** No shared databases between environments.

---

## 2. Infrastructure-as-Code Standards

### 2.1 IaC Must Be the Source of Truth

- No click-ops in production (exceptions require change record)
- all changes via PR
- plan → review → apply with approvals

### 2.2 Terraform Conventions (If Terraform Used)

Recommended layout:

```
infrastructure/
  modules/
    network/
    compute/
    database/
    observability/
  envs/
    dev/
    staging/
    prod/
```

Rules:
- remote state (S3/GCS/Azure Storage) + state locking
- version pinning for providers
- `terraform fmt` and `terraform validate` in CI
- drift detection weekly (plan-only)

### 2.3 Policy-as-Code

- validate IaC with at least one:
  - tfsec
  - checkov
  - trivy config scan
  - conftest/OPA policies (advanced)

**Gate Requirement:** IaC scans must run in Gate 6 (Validate) and block High/Critical.

---

## 3. IAM Least Privilege Templates

### 3.1 Role Separation Model

- **Human roles**:
  - ReadOnly
  - Developer (non-prod admin)
  - Ops (prod deploy only)
  - Security (audit + incident)
  - BreakGlass (manual emergency)

- **Service roles**:
  - App runtime role
  - CI/CD deploy role
  - Worker/queue consumer role
  - DB migration role (separate, time-bound)

### 3.2 Least Privilege Rules (MUST)

- deny by default
- scoped resources (by ARN/resource ID)
- time-bound elevated access
- no long-lived access keys; use OIDC/workload identity
- rotate secrets on schedule

### 3.3 Example IAM Policy Checklist (Provider-Agnostic)

- [ ] Only required actions allowed
- [ ] Only required resources allowed
- [ ] No wildcard `*` on actions unless justified
- [ ] No wildcard `*` on resources unless unavoidable
- [ ] Separate policy for read vs write
- [ ] Logging enabled for auth events

---

## 4. Network Segmentation & Zero Trust

### 4.1 Network Segmentation MUST

- separate subnets:
  - public edge
  - private app
  - private data
- security groups/firewalls restrict east-west traffic
- only allow:
  - app → db (port 5432)
  - app → cache (6379)
  - app → queue (provider specific)
- deny all other lateral movement

### 4.2 WAF/CDN Rules

Minimum WAF:
- SQLi/XSS rule sets
- bot filtering
- geo restrictions (optional)
- rate limits on auth routes
- IP allowlist for admin endpoints (if feasible)

---

## 5. Secrets Management & Key Rotation

### 5.1 Approved Secrets Stores

- AWS Secrets Manager / GCP Secret Manager / Azure Key Vault
- HashiCorp Vault (advanced)
- SOPS + KMS for GitOps (if needed)

**MUST NOT:**
- store secrets in repo
- store secrets in Docker images
- store secrets in client apps (web/mobile)

### 5.2 Rotation Policy (Baseline)

| Secret Type | Rotation |
|---|---|
| JWT signing keys | 90 days (or less) |
| DB credentials | 60–90 days |
| API keys | 60–90 days |
| OAuth client secrets | 90 days |
| TLS certs | auto-renew |

### 5.3 Key Management

- encrypt at rest with KMS-managed keys
- separate keys per environment
- restrict decrypt permissions to runtime roles only
- enable key rotation where supported

---

## 6. Container & Supply Chain Security

### 6.1 Docker Baselines

- minimal base images (distroless/alpine when appropriate)
- non-root user
- read-only filesystem where possible
- drop Linux capabilities
- multi-stage builds
- no build secrets baked into final image

### 6.2 SBOM & Dependency Audits

- generate SBOM (CycloneDX/SPDX) in CI when possible
- dependency scanning in CI (npm audit / pip-audit / osv-scanner)
- block high/critical CVEs (policy-defined)

### 6.3 Image Scanning

- scan container images with Trivy (or equivalent)
- block high/critical findings

---

## 7. Kubernetes Hardening

### 7.1 Baseline Controls (MUST)

- RBAC least privilege
- namespaces by environment/app
- network policies (deny by default)
- secrets via external secret store (avoid plain Kubernetes secrets where possible)
- pod security standards (restricted)
- admission controls (OPA Gatekeeper/Kyverno recommended)
- resource requests/limits (prevent noisy neighbor)
- liveness/readiness probes

### 7.2 Runtime Security (Recommended)

- eBPF runtime tools (Falco) or managed runtime security
- audit logs enabled
- node hardening + auto patching

---

## 8. CI/CD DevSecOps Pipeline

### 8.1 Pipeline Stages (Reference)

1. lint + format + typecheck
2. unit tests + coverage
3. SAST (semgrep/bandit/eslint security)
4. dependency scan (osv/snyk/pip-audit/npm audit)
5. secret scan (gitleaks)
6. IaC scan (tfsec/checkov/trivy config)
7. container scan (trivy image)
8. deploy to staging
9. DAST (ZAP) + smoke tests
10. approval gate
11. deploy to production
12. post-deploy verification + rollback ready

### 8.2 Deployment Controls

- staged rollouts (blue/green or canary)
- feature flags for risky features
- auto rollback on:
  - error rate spike
  - latency spike
  - failed health checks

---

## 9. Observability, SLOs, and Alerting

### 9.1 Required Signals

- logs (structured)
- metrics (RED/USE)
- tracing (distributed)

### 9.2 SLO Starter Pack

- availability: 99.9%
- latency: API p95 < 500ms
- error rate: 5xx < 1%

### 9.3 Alerting Rules

- alert on symptoms (latency, errors, saturation)
- avoid alert fatigue
- include runbook links in every alert

---

## 10. Backups, Disaster Recovery, and Rollback

### 10.1 RTO/RPO Definitions

- **RPO**: max tolerable data loss
- **RTO**: max tolerable downtime

### 10.2 Backup Baseline

- DB PITR (where supported)
- daily snapshots
- encrypted backups
- backup retention policy (see masterDataSDLC)
- monthly restore drill (MUST for serious systems)

### 10.3 Rollback Plan (MUST)

- immutable releases
- ability to rollback app version without DB loss
- migration rollback strategy documented

---

## 11. Cost Governance & FinOps

- budgets + alerts per environment
- tagging policy (owner, project, env, cost-center)
- autoscaling policies aligned with SLOs
- reserved capacity decisions documented (ADR)

---

## 12. Professional Documentation Outputs

Infrastructure work MUST produce:

- `docs/INFRA_OVERVIEW.md` (architecture, environments, diagrams reference)
- `docs/SECRETS_AND_KEYS.md` (where secrets live, rotation schedule)
- `docs/CI_CD.md` (pipeline stages + approvals)
- `docs/DR_PLAN.md` (RTO/RPO, backups, restore steps)
- `docs/ONCALL_RUNBOOK.md` (alerts, troubleshooting)

---

## 13. Checklists

### 13.1 IaC PR Checklist

- [ ] Terraform/Pulumi formatted and validated
- [ ] No public DB/cache
- [ ] IAM least privilege validated
- [ ] Secrets not exposed in state outputs
- [ ] Logging/audit enabled
- [ ] IaC scans pass (no High/Critical)
- [ ] DR/rollback considerations documented

### 13.2 Prod Deployment Checklist (DevOps)

- [ ] Staging healthy (smoke tests pass)
- [ ] DAST completed (if required)
- [ ] Observability dashboards ready
- [ ] Rollback tested / known good release available
- [ ] Human approval recorded (for prod)
