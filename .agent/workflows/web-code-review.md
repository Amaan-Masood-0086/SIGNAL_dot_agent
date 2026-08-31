---
description: CTO-level web code review checklist for SIGNAL. Run before any PR merge or deployment.
---

# Web Code Review Checklist — SIGNAL

Run through ALL sections before merging or deploying.

## 🔒 Security

### Auth & Session
- [ ] Session token in HttpOnly + Secure + SameSite cookie (not localStorage)
- [ ] CSRF protection on all state-changing (POST/PUT/PATCH/DELETE) routes
- [ ] Auth check in `middleware.ts` covers all protected routes and is institution-scoped
- [ ] Session invalidated on logout

### Access Control
- [ ] Every API route handler checks authentication (never trust middleware alone)
- [ ] Every resource fetch checks institution ownership before rendering
- [ ] No resource IDs accepted from client to determine ownership (IDOR)
- [ ] A caretaker's UI never renders another institution's child data even transiently (e.g. in dev tools/network tab during a race condition)

### Input & Output
- [ ] All inputs validated server-side with Pydantic (client-side Zod is UX only, not the real control)
- [ ] No `dangerouslySetInnerHTML` without DOMPurify sanitization
- [ ] No user-controlled redirects without allowlist validation
- [ ] No secrets or internal errors returned to client

### Voice/Microphone (SIGNAL-specific — do not skip)
- [ ] Microphone permission requested explicitly and visibly, never silently
- [ ] `Permissions-Policy` correctly scoped to `microphone=(self)` — **not** the generic-template `microphone=()` block
- [ ] Recording indicator is visually unambiguous while active
- [ ] Media stream is released immediately after each turn ends
- [ ] Text-input fallback has full feature parity — verify by testing the flow with microphone permission denied

### Browser Hardening
- [ ] Security headers set: HSTS, CSP, X-Content-Type-Options, Referrer-Policy, corrected Permissions-Policy
- [ ] No third-party scripts without CSP allowlist entry

## ♿ Accessibility & Usability

- [ ] Microphone button and all interactive elements have `aria-label`s
- [ ] Loading/error/empty states present on every data page
- [ ] Flag + reasoning-trail display is legible in plain language, not raw JSON/technical text
- [ ] WCAG 2.1 AA target met (caretakers may have varying literacy/tech comfort — this is a real usability requirement, not a checkbox)

## Before Deployment

- [ ] `NEXT_PUBLIC_` vars contain no secrets
- [ ] `npm audit --audit-level=high` clean
- [ ] Source maps not served publicly in production
- [ ] E2E test for the core flow (speak/type → follow-up → flag → referral) passing
