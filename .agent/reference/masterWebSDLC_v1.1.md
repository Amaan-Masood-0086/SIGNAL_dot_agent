---
description: masterWebSDLC — Comprehensive web application security & architecture guide. Browser threat model, OWASP ASVS, CSP/CSRF/CORS, secure sessions, Next.js/React patterns, SSR/SSG caching safety.
---

# masterWebSDLC: Web Application Security & Architecture Guide

## Purpose

This document is the **web-specific deep-dive reference** that extends:

- **masterSDLC.md** = General security processes (OWASP, threat modeling, compliance, CI/CD security)
- **A-SDLC.md** = AI orchestration, tech selection, coding contracts, execution gates
- **masterWebSDLC.md** = Web-specific security, browser hardening, frontend/backend integration patterns (this document)

Use all companion documents together for complete, security-first web development.

---

## Document Information

| Field | Value |
|------|-------|
| **Version** | 1.1 |
| **Companion Documents** | masterSDLC.md, A-SDLC.md • (optional) NotionProjectOS.md |
| **Created** | 2026-02-20 |
| **Last Updated** | 2026-02-20 |
| **Target Web Stack** | React 18+ / Next.js (App Router) / Node 20+ / FastAPI/NestJS |
| **Scope** | Universal — SSR/SSG/SPA web apps + APIs |

---

## Table of Contents

1. [Web Security Architecture](#1-web-security-architecture)
2. [OWASP ASVS Mapping](#2-owasp-asvs-mapping)
3. [Authentication & Session Management](#3-authentication--session-management)
4. [Authorization & Access Control](#4-authorization--access-control)
5. [Browser Hardening](#5-browser-hardening)
6. [Input Validation & Output Encoding](#6-input-validation--output-encoding)
7. [CORS, CSRF, and SameSite Strategy](#7-cors-csrf-and-samesite-strategy)
8. [File Uploads & Untrusted Content](#8-file-uploads--untrusted-content)
9. [Frontend Secrets & Configuration Safety](#9-frontend-secrets--configuration-safety)
10. [SSR/SSG/ISR Caching & Data Leakage Prevention](#10-ssrssgisr-caching--data-leakage-prevention)
11. [API Integration](#11-api-integration)
12. [WebSockets & Realtime Security](#12-websockets--realtime-security)
13. [Supply Chain & Build Security](#13-supply-chain--build-security)
14. [Testing Strategy for Web Apps](#14-testing-strategy-for-web-apps)
15. [Deployment & Edge Security](#15-deployment--edge-security)
16. [Operational Monitoring](#16-operational-monitoring)
17. [Quick Reference Checklists](#17-quick-reference-checklists)
18. [Implementation Snippets](#18-implementation-snippets)
19. [Responsive Design & Accessibility](#19-responsive-design--accessibility)
20. [Performance, SEO & Core Web Vitals](#20-performance-seo--core-web-vitals)
21. [Frontend Observability (RUM) & Error Monitoring](#21-frontend-observability-rum--error-monitoring)
22. [PWA / Service Worker Security](#22-pwa--service-worker-security)
23. [Third-Party Scripts & Supply-Chain Controls](#23-third-party-scripts--supply-chain-controls)
24. [CI Gate Commands (Web)](#24-ci-gate-commands-web)

---

## 1. Web Security Architecture

### 1.1 Web Threat Model (Browser-Centric)

Web apps are exposed to threats that do **not** exist in mobile/native in the same way:

- **XSS** (user-supplied content executing in browser)
- **CSRF** (browser auto-sends cookies)
- **Clickjacking** (UI framed / overlaid)
- **CORS misconfig** (cross-origin data exfil)
- **Supply-chain / third‑party script compromise** (analytics, chat widgets)
- **Session theft** (cookie misflags, token storage in localStorage)
- **Cache leakage** (SSR/edge cache serving another user's data)
- **Service worker abuse** (PWA caching sensitive responses)

### 1.2 Security Layer Model (Web)

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 0: DNS / TLS / CDN                                    │
│  • DNSSEC (where possible) • TLS 1.3 • HSTS • DDoS/WAF       │
├─────────────────────────────────────────────────────────────┤
│ LAYER 1: Browser Controls                                   │
│  • CSP • Trusted Types • Security headers • Cookie flags     │
├─────────────────────────────────────────────────────────────┤
│ LAYER 2: Frontend App                                       │
│  • No secrets in bundle • Safe rendering • Input validation  │
│  • Auth-safe routing • Safe redirects                        │
├─────────────────────────────────────────────────────────────┤
│ LAYER 3: API Gateway / Backend                              │
│  • AuthN/AuthZ • Rate limiting • Validation • Logging        │
│  • CSRF defense (if cookies) • SSRF protection               │
├─────────────────────────────────────────────────────────────┤
│ LAYER 4: Data                                                │
│  • Least privilege • Encryption at rest • Audit logs         │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 “One Sentence” Architecture Rule

**Never trust the browser.** The browser is a hostile environment: everything in JS bundle is public, every client request can be forged, and every UI state can be manipulated.

---

## 2. OWASP ASVS Mapping

### 2.1 Why ASVS

OWASP Top 10 is a **risk list**; OWASP ASVS is a **control standard** you can turn into:
- engineering requirements
- test cases
- release gates

### 2.2 Minimal ASVS Controls (Practical Baseline)

```yaml
asvs_minimum_controls:
  V1: "Architecture, design, and threat modeling"
  V2: "Authentication"
  V3: "Session management"
  V4: "Access control"
  V5: "Validation, sanitization and encoding"
  V7: "Error handling and logging"
  V8: "Data protection"
  V9: "Communications"
  V10: "Malicious code"
  V11: "Business logic"
  V12: "Files and resources"
  V13: "API and web service"
```

### 2.3 How to Use This in Your SDLC

- Put ASVS items into **Gate exit criteria** (A-SDLC Phase 6 Validate)
- Create **unit tests** for V2–V5 and **DAST** for V13
- Add **security header tests** for V9 and browser layer

---

## 3. Authentication & Session Management

### 3.1 Recommended Default: Cookie-Based Session (HttpOnly)

For browser apps, the safest default is:
- **Session cookie** (HttpOnly + Secure + SameSite)
- **CSRF protection** for state-changing requests
- Avoid storing auth tokens in localStorage/sessionStorage (XSS turns that into instant account takeover)

#### Cookie Rules

```yaml
cookie_rules:
  - "Use HttpOnly + Secure cookies for session tokens"
  - "Prefer __Host- prefix for session cookie"
  - "SameSite=Lax by default (use None only when required)"
  - "Rotate session on login and privilege change"
  - "Invalidate all sessions on password reset"
  - "Short idle timeout (e.g., 15 min) + absolute timeout (e.g., 7 days)"
```

**Good cookie example (session):**
```
Set-Cookie: __Host-session=...; Path=/; Secure; HttpOnly; SameSite=Lax; Max-Age=900
```

### 3.2 OAuth in Browser

- Use **Authorization Code + PKCE**
- Never use Implicit Flow
- Store tokens server-side when possible; if you must store client-side, use **in-memory only** and accept usability trade-offs

### 3.3 MFA and Passkeys (WebAuthn)

If you support MFA:
- Offer TOTP and/or passkeys
- Enforce MFA for admin roles
- Add step-up auth for sensitive actions (change email, payout settings, delete account)

---

## 4. Authorization & Access Control

### 4.1 Golden Rule

**All authorization happens server-side.** Frontend route guards are UX only.

### 4.2 Access Control Patterns

- RBAC for most SaaS (roles: user, manager, admin)
- ABAC for complex policies (attributes: tenant_id, region, plan)
- Object-level checks for every resource (`owner_id == current_user.id`)

### 4.3 IDOR Prevention Checklist

```yaml
idor_prevention:
  - "Never accept resource ownership from client (e.g., user_id in body)"
  - "Derive subject from session (current user)"
  - "Verify tenant boundary on every query (tenant_id filter)"
  - "Use UUIDs (not incremental IDs) for public identifiers"
```

---

## 5. Browser Hardening

### 5.1 Security Headers Baseline

**Minimum headers to set on ALL HTML responses:**

```yaml
security_headers_baseline:
  Strict-Transport-Security: "max-age=31536000; includeSubDomains; preload"
  X-Content-Type-Options: "nosniff"
  Referrer-Policy: "strict-origin-when-cross-origin"
  Permissions-Policy: "camera=(), microphone=(), geolocation=()"
  Content-Security-Policy: "see CSP section"
  Cross-Origin-Opener-Policy: "same-origin"
  Cross-Origin-Resource-Policy: "same-origin"
  X-Frame-Options: "DENY (or use CSP frame-ancestors)"
```

> Note: `X-Frame-Options` is legacy; prefer `frame-ancestors` in CSP. Keep XFO for older browsers if needed.

### 5.2 Content Security Policy (CSP)

A CSP should be **strict by default** and relaxed only when required.

#### CSP Principles

```yaml
csp_principles:
  - "Block inline scripts by default (use nonces/hashes)"
  - "Block third-party scripts unless explicitly allowlisted"
  - "Use frame-ancestors 'none' (or specific allowlist)"
  - "Disable object/embed entirely (object-src 'none')"
  - "Use report-to / report-uri for monitoring"
```

#### Example CSP (Nonce-based; SSR apps)

> Replace `NONCE` at runtime per request.

```
Content-Security-Policy:
  default-src 'none';
  base-uri 'none';
  object-src 'none';
  frame-ancestors 'none';
  img-src 'self' https: data:;
  font-src 'self' https: data:;
  style-src 'self' 'nonce-NONCE';
  script-src 'nonce-NONCE' 'strict-dynamic' https:;
  connect-src 'self' https:;
  form-action 'self';
  upgrade-insecure-requests;
```

### 5.3 Trusted Types (XSS Hardening Bonus)

If you can adopt it (modern browsers):
- Add `require-trusted-types-for 'script'`
- Use framework-safe DOM APIs
- Avoid direct DOM sinks (`innerHTML`)

### 5.4 Third-Party Script Safety

- Prefer server-side integrations (proxy) over injecting vendor JS
- If vendor JS must be used:
  - Put it behind allowlist in CSP
  - Use **Subresource Integrity (SRI)** where possible
  - Keep vendor list minimal and review quarterly

---

## 6. Input Validation & Output Encoding

### 6.1 Validation Model

- Client: validate for UX (Zod / react-hook-form)
- Server: validate for security (Pydantic/Zod/Joi)
- DB: constraints for integrity (unique, check constraints)

### 6.2 XSS Prevention Rules

```yaml
xss_rules:
  - "Default to framework auto-escaping (React/Next templates)"
  - "Never use dangerouslySetInnerHTML unless sanitized"
  - "Sanitize rich text with allowlist sanitizer (DOMPurify, etc.)"
  - "Encode output by context (HTML/JS/URL/CSS)"
  - "Disallow user-controlled HTML in critical surfaces (payments, settings)"
```

---

## 7. CORS, CSRF, and SameSite Strategy

### 7.1 CORS Rules

```yaml
cors_rules:
  - "Never use Access-Control-Allow-Origin: * in production when credentials are used"
  - "Allow only explicit origins"
  - "Allow only required methods/headers"
  - "Set Access-Control-Allow-Credentials only if needed"
  - "Do not reflect Origin header without validation"
```

### 7.2 CSRF Strategy Matrix

| Auth Style | CSRF Needed? | Recommended Defense |
|-----------|--------------|---------------------|
| Cookie-based session | ✅ Yes | SameSite=Lax + CSRF token on state changes |
| JWT in HttpOnly cookie | ✅ Yes | SameSite + CSRF token |
| Authorization header (Bearer) only | Usually ❌ | Still protect from XSS; consider CSRF for legacy flows |
| Cross-site embedded app (iframe) | ✅ Yes | SameSite=None + CSRF + additional checks |

### 7.3 CSRF Token Patterns

- **Synchronizer token**: server stores token in session, client sends in header.
- **Double-submit cookie**: token in readable cookie + header; server compares.

**Preferred for modern apps:** Synchronizer token (less footguns).

---

## 8. File Uploads & Untrusted Content

### 8.1 Upload Rules

```yaml
upload_rules:
  - "Validate file type by magic bytes (not filename extension)"
  - "Enforce size limits (request body + per-file)"
  - "Virus scan uploads (ClamAV or managed scanner)"
  - "Store in object storage with random filename (no user path)"
  - "Serve uploads from separate domain/subdomain"
  - "Set Content-Disposition: attachment for risky types"
  - "Never allow SVG uploads unless sanitized (SVG can contain scripts)"
```

### 8.2 Untrusted HTML / Markdown

- Markdown rendering must sanitize HTML
- Disallow raw HTML in Markdown unless you have a strong sanitizer policy
- For user-generated content, prefer **plaintext + limited formatting**

---

## 9. Frontend Secrets & Configuration Safety

### 9.1 Non-Negotiable Rule

**Anything shipped to the browser is public.** That includes:
- API keys (unless strictly public)
- OAuth client secrets (NEVER)
- private endpoints
- internal hostnames
- feature flags that reveal sensitive roadmap info

### 9.2 Next.js Environment Variable Rules

```yaml
nextjs_env_rules:
  - "Only variables prefixed with NEXT_PUBLIC_ are exposed to the client"
  - "Never put secrets in NEXT_PUBLIC_ variables"
  - "Prefer server-side calls for third-party APIs requiring secrets"
  - "Audit build output for leaked secrets"
```

### 9.3 Runtime Config Pattern

- Use server-rendered config endpoint (authenticated if needed)
- Cache public config at CDN edge
- Keep sensitive config server-only

---

## 10. SSR/SSG/ISR Caching & Data Leakage Prevention

### 10.1 The Classic Web Bug

SSR pages or edge caches accidentally serve **User A’s** data to **User B**.

### 10.2 Cache-Control Rules

```yaml
cache_rules:
  html_authenticated:
    header: "Cache-Control: private, no-store"
  api_sensitive:
    header: "Cache-Control: no-store"
  static_assets:
    header: "Cache-Control: public, max-age=31536000, immutable"
  public_pages:
    header: "Cache-Control: public, max-age=0, must-revalidate"
```

### 10.3 ISR/SSG Guardrails

- Never pre-render pages that include user-specific data unless segmented per user (rare)
- If you use ISR:
  - Keep user-specific data client-fetched after hydration
  - Ensure API responses are not cached publicly

---

## 11. API Integration

### 11.1 Request Authentication

- If browser app: cookie session preferred
- If API consumed by mobile + web: support both
  - Mobile: JWT bearer (stored in secure storage)
  - Web: session cookie (HttpOnly)

### 11.2 Rate Limiting

- Rate limit by IP + user + endpoint
- Add stricter limits for auth endpoints (login, reset password)

### 11.3 Error Handling

- Return generic errors to clients
- Log details server-side
- Do not leak stack traces or SQL errors

---

## 12. WebSockets & Realtime Security

### 12.1 WebSocket Rules

```yaml
websocket_security:
  - "Authenticate during handshake (cookie/session or token)"
  - "Re-check authorization per message type (do not trust client event name)"
  - "Validate message payload schema (Zod/Pydantic)"
  - "Apply rate limits per connection"
  - "Terminate idle connections"
  - "Do not send PII in broadcast events"
```

---

## 13. Supply Chain & Build Security

### 13.1 Dependency Rules (Node/Frontend)

- Use lockfiles (package-lock.json / pnpm-lock.yaml)
- Use `npm ci` / `pnpm install --frozen-lockfile` in CI
- Run dependency audit + SCA (Snyk, npm audit)
- Pin major versions of critical dependencies

### 13.2 Source Maps

- Do not serve source maps publicly for authenticated apps
- Upload to error tracking (Sentry) instead
- Treat source maps as sensitive (they reveal code structure)

---

## 14. Testing Strategy for Web Apps

### 14.1 Minimum Security Tests

```yaml
minimum_web_security_tests:
  - "Unit tests for auth/session expiration"
  - "Unit tests for access control (RBAC/object checks)"
  - "Header tests: CSP present, HSTS present, no sniff, referrer policy"
  - "CSRF tests (POST/PUT/DELETE require token)"
  - "XSS tests for any user-generated content rendering"
  - "DAST baseline scan in CI (OWASP ZAP)"
```

### 14.2 Security Header Tests (Example Approach)

- Integration test that fetches homepage HTML response and asserts required headers exist
- Fail build if missing in production config

---

## 15. Deployment & Edge Security

### 15.1 Edge Controls

- Use CDN + WAF (OWASP rules)
- Enable DDoS protections
- TLS 1.2 minimum (prefer 1.3)
- HSTS + redirects from HTTP → HTTPS

### 15.2 Separation of Domains

- `app.example.com` for main app
- `static.example.com` for assets
- `uploads.exampleusercontent.com` for user uploads (separate cookie scope)

---

## 16. Operational Monitoring

### 16.1 Web-Specific Signals

- CSP report endpoint (detect inline script attempts)
- Auth anomaly rates (login failures, password reset spikes)
- WAF blocks and top rules triggered
- Sudden increase in 403/401s or 5xx

### 16.2 Logging Hygiene

- Never log tokens or full cookies
- Redact authorization headers
- Hash or redact email/phone in logs where possible

---

## 17. Quick Reference Checklists

### 17.1 Web Release Security Checklist

```markdown
## Web Release Checklist (Security)

- [ ] HTTPS enforced, HSTS enabled
- [ ] Session cookie is HttpOnly + Secure + SameSite
- [ ] CSRF protection in place for state-changing routes
- [ ] CORS allowlist configured (no wildcard)
- [ ] CSP deployed and tested on production
- [ ] Security headers present (nosniff, referrer-policy, permissions-policy)
- [ ] No secrets in client bundle (audit build output)
- [ ] File uploads validated + scanned + stored safely
- [ ] Rate limiting for auth endpoints enabled
- [ ] DAST (ZAP baseline) run clean or issues accepted with risk
- [ ] Source maps not publicly accessible (if app is authenticated)
```

### 17.2 Frontend PR Checklist (Security)

```markdown
## Frontend PR Checklist

- [ ] No dangerouslySetInnerHTML without sanitizer
- [ ] No secrets in NEXT_PUBLIC_ env vars
- [ ] No new third-party script without approval
- [ ] User-generated content sanitized
- [ ] Redirects validated (no open redirect)
- [ ] Auth-protected pages do not leak data in HTML
```

---

## 18. Implementation Snippets

### 18.1 Express Security Headers (helmet)

```ts
import helmet from "helmet";
import express from "express";

const app = express();

app.use(helmet({
  // Most helmet defaults are good; customize CSP below.
  contentSecurityPolicy: false,
}));

app.use((req, res, next) => {
  res.setHeader("Referrer-Policy", "strict-origin-when-cross-origin");
  res.setHeader("X-Content-Type-Options", "nosniff");
  res.setHeader("Permissions-Policy", "camera=(), microphone=(), geolocation=()");
  next();
});
```

### 18.2 Nginx Security Headers (Baseline)

```nginx
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
add_header Cross-Origin-Opener-Policy "same-origin" always;
add_header Cross-Origin-Resource-Policy "same-origin" always;

# HSTS (only after HTTPS is correct):
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

### 18.3 Next.js: Cookie Session Reminder

- Never read session token from client JS
- Prefer server actions / route handlers for sensitive calls
- Always set cookies server-side with Secure/HttpOnly/SameSite

---



## 19. Responsive Design & Accessibility

### 19.1 Responsive Baseline (Web)

**Rule:** If it doesn’t work on small screens, it’s broken.

Minimum breakpoints to validate (manual + automated):

- 320px (small phones)
- 375px (modern phones)
- 768px (tablets)
- 1024px (small laptops)
- 1440px (desktop)

**Responsive checklist:**

```yaml
responsive_checks:
  - "No horizontal scroll at any breakpoint"
  - "Touch targets >= 44x44px"
  - "Forms usable on mobile (no tiny inputs, no overflow)"
  - "Keyboard focus visible (do not remove outline without replacement)"
  - "Sticky headers/footers do not cover content"
  - "Tables have mobile pattern (stacked rows / horizontal scroll within container)"
```

### 19.2 Accessibility Standard

Target: **WCAG 2.1 AA** (minimum).

Mandatory controls:

```yaml
a11y_must_have:
  - "Semantic HTML (button for actions, a for navigation)"
  - "Every input has a label"
  - "All images have alt (or empty alt for decorative)"
  - "Color is not the only signal (errors, status)"
  - "Keyboard navigation works for all features"
  - "ARIA only when needed (don’t over-ARIA)"
  - "Announce form errors (aria-live region)"
```

### 19.3 Automated A11y Tests

- Run `axe` checks in Playwright for key pages (login, dashboard, settings).
- Run Lighthouse accessibility score (CI), but treat it as **signal**, not full coverage.

---

## 20. Performance, SEO & Core Web Vitals

### 20.1 Performance Budgets (Practical)

Set budgets per project, but a good default baseline:

```yaml
performance_budgets:
  - metric: "LCP"
    target: "<= 2.5s (p75)"
  - metric: "INP"
    target: "<= 200ms (p75)"
  - metric: "CLS"
    target: "<= 0.1"
  - metric: "JS bundle (initial)"
    target: "keep minimal; avoid shipping admin libraries to public pages"
```

### 20.2 SSR/SSG Safety for Performance

- Prefer **SSG** for public marketing pages (no secrets, CDN cached).
- Prefer **SSR** for authenticated pages **only when** you can guarantee per-user isolation.
- Never cache authenticated HTML at CDN/edge unless cache varies by a safe key (e.g., session id) — usually **do not**.

### 20.3 SEO Rules (If SEO Matters)

```yaml
seo_rules:
  - "Unique title + meta description per page"
  - "Canonical URLs configured"
  - "Robots.txt + sitemap.xml"
  - "Noindex admin/internal routes"
  - "Structured data (JSON-LD) for product/article pages (when applicable)"
  - "Avoid blocking JS/CSS in robots unless intentional"
```

---

## 21. Frontend Observability (RUM) & Error Monitoring

### 21.1 What to Capture

- Frontend errors (uncaught exceptions, React errors)
- Performance signals (LCP/INP/CLS)
- API error rates by route
- User journey breadcrumbs for debugging (without PII)

### 21.2 Security Rules for RUM

```yaml
rum_security:
  - "Never send tokens, passwords, OTPs, or full PII to monitoring tools"
  - "Hash or redact user identifiers"
  - "Treat monitoring vendor as third-party data processor (compliance impact)"
  - "Disable session replay on sensitive pages (payments, auth, settings) unless strictly configured"
```

---

## 22. PWA / Service Worker Security

If you use a service worker:

```yaml
service_worker_rules:
  - "Never cache authenticated HTML pages"
  - "Never cache API responses containing PII to disk"
  - "Cache static assets only (immutable hashed files)"
  - "Implement cache versioning + cache purge on logout"
  - "Do not allow arbitrary runtime caching of third-party requests"
```

---

## 23. Third-Party Scripts & Supply-Chain Controls

Third‑party scripts are a top real-world web risk (analytics, chat widgets, A/B testing).

```yaml
third_party_controls:
  approval:
    - "Every new third-party script requires explicit approval (Security Officer)"
    - "Vendor risk review: data collected, regions, retention, breach history"
  technical:
    - "Prefer server-side integrations over client-side scripts"
    - "Use CSP to restrict script sources"
    - "Pin versions where possible"
    - "Use Subresource Integrity (SRI) for static CDN scripts"
    - "Load scripts lazily and only on pages that need them"
```

---

## 24. CI Gate Commands (Web)

Minimum CI gates for web repos:

```bash
# Lint + format
npm run lint
npm run format:check

# Type check
npm run typecheck

# Unit tests
npm test -- --ci

# E2E (critical flows)
npx playwright test

# Security
npm audit --audit-level=high
# + optional: semgrep, trivy (if containerized), gitleaks

# Performance/a11y (optional but recommended)
npx lighthouse-ci autorun
```

## End

This document is intentionally focused on web-specific controls. Use it with masterSDLC.md and A-SDLC.md for full coverage.
