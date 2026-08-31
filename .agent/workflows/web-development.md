---
description: Web frontend development workflow — build order, coding contracts, and patterns for SIGNAL's Next.js frontend.
---

# Web Development Workflow — SIGNAL

## Tech Stack (Locked)

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | Next.js (App Router) | SSR/SSG/ISR |
| Language | TypeScript (strict) | No `any` allowed |
| Styling | Tailwind CSS | |
| State (server) | TanStack Query v5 | All API data |
| State (client) | Zustand | UI-only state (e.g. active session/turn state) |
| Forms | react-hook-form + Zod | Always paired |
| HTTP | fetch | Server Components use fetch |
| Auth | Server-side session, HttpOnly cookies | |
| Voice | Browser MediaRecorder API → backend STT endpoint | See Voice/Microphone section below |
| Testing | Jest + Testing Library + Playwright | Unit + E2E |

## Build Order (STRICT — Never Skip Steps)

```
Step 1: Foundation
  → layout.tsx, globals.css, lib/fonts.ts
  → commit: "chore: project foundation + design tokens"

Step 2: Design System
  → components/ui/ (Button, Input, Card, Badge, Modal)
  → commit: "feat(ui): design system components"

Step 3: Auth
  → server-side session, middleware.ts (route protection, institution-scoped)
  → app/(auth)/ group (login)
  → commit: "feat(auth): authentication + protected routes"

Step 4: API Layer
  → lib/api/ (typed fetch wrappers)
  → TanStack Query setup
  → Zod schemas for all API responses (children, sessions, flags, referrals)
  → commit: "feat(api): typed API layer + query hooks"

Step 5: Core Interaction — Voice + Text Chat (FEAT-03)
  → Microphone permission flow (explicit, visible consent — see below)
  → Voice recording component + text-box fallback (fallback MUST always work
    even if mic permission is denied)
  → commit: "feat(input): voice + text caretaker input"

Step 6: Feature Pages (one at a time, matches FEATURE_BACKLOG_SIGNAL.md order)
  → child profile/intake (FEAT-02), flag display + reasoning trail (FEAT-09),
    referral record (FEAT-10), session resume (FEAT-08)
  → Loading + error + empty states on every page
  → commit: "feat(feature-name): description"

Step 7: Polish
  → Accessibility audit (axe, keyboard nav) — important given caretakers
    may have varying literacy/tech comfort
  → commit: "feat(ux): accessibility + performance"

Step 8: Testing
  → Unit tests for utilities and hooks
  → Integration tests for API hooks
  → E2E tests for the core flow: speak → follow-up → flag → referral
  → commit: "test: unit + integration + E2E coverage"
```

## Voice / Microphone — SIGNAL-Specific (read before Step 5)

This is the one area where SIGNAL's frontend genuinely differs from a standard business-app template:

- **MUST** request microphone permission explicitly and visibly — never silently record
- **MUST** provide a working text-input fallback that requires zero microphone permission, and make it equally prominent (not a hidden fallback link)
- **MUST NOT** set `Permissions-Policy: microphone=()` in security headers (a generic template default that would break the product) — instead scope it to `self` only: `microphone=(self)`
- **MUST** stop recording and release the media stream immediately after each turn — never keep the microphone open between turns
- **MUST** show a clear visual recording-in-progress indicator (institutional caretakers should never be uncertain whether they're being recorded)

## 20 MUST Rules

1. **MUST** use TypeScript strict mode — zero `any` tolerance
2. **MUST** set security headers on all HTML responses (HSTS, CSP, nosniff, referrer-policy, and the corrected `Permissions-Policy` above)
3. **MUST** use HttpOnly + Secure + SameSite cookies for session tokens — never localStorage
4. **MUST** implement CSRF protection for all state-changing routes
5. **MUST** validate all user inputs client-side (Zod) AND server-side (Pydantic)
6. **MUST** sanitize any user-generated text before display (DOMPurify or allowlist sanitizer) — caretaker free-text input included
7. **MUST** implement CORS allowlist — never wildcard `*` with credentials
8. **MUST** use Server Components for data fetching by default — Client Components for interactivity (voice recorder, chat turn) only
9. **MUST** add loading state, error state, and empty state on every data-fetching page
10. **MUST** use `next/image` for all images
11. **MUST** add `aria-label` or visible label to all interactive elements — including the microphone button and recording indicator
12. **MUST** set `rel="noopener noreferrer"` on all external links
13. **MUST** validate and allow-list all redirect URLs
14. **MUST** run `npm audit --audit-level=high` before release
15. **MUST** keep `NEXT_PUBLIC_` env vars non-secret
16. **MUST** validate API response shape with Zod on the client
17. **MUST** target WCAG 2.1 AA accessibility
18. **MUST** set `Cache-Control: private, no-store` on all SSR authenticated pages
19. **MUST** write E2E tests for the core caretaker flow (login → speak/type → follow-up → flag → referral)
20. **MUST** ensure the text-input fallback path has full feature parity with voice (no feature is voice-only)

## MUST-NOT Rules

1. **MUST NOT** use `dangerouslySetInnerHTML` without a DOMPurify sanitizer
2. **MUST NOT** store tokens in localStorage or sessionStorage
3. **MUST NOT** put secrets in `NEXT_PUBLIC_` env vars
4. **MUST NOT** use `Access-Control-Allow-Origin: *` with credentials
5. **MUST NOT** add third-party scripts without security review and CSP allowlist entry
6. **MUST NOT** serve source maps publicly in production
7. **MUST NOT** commit `.env` files or hardcoded secrets
8. **MUST NOT** cache authenticated HTML at CDN/edge
9. **MUST NOT** skip loading and error states
10. **MUST NOT** use `any` TypeScript type
11. **MUST NOT** make API calls in layout components
12. **MUST NOT** import server-only code into Client Components
13. **MUST NOT** use `window`/`document` directly in components (use hooks)
14. **MUST NOT** use `alert()`, `confirm()`, or `prompt()` — use modal components
15. **MUST NOT** allow open redirects
16. **MUST NOT** expose internal server error details to the client
17. **MUST NOT** ship unused CSS or JS
18. **MUST NOT** keep the microphone stream open outside an active recording turn
19. **MUST NOT** display a child's flag or reasoning trail to a caretaker outside their own institution (client-side check is a UX nicety only — server-side institution-scoping is the real control, per `sdlc-security.md`)
20. **MUST NOT** treat voice as the only path to any feature — text fallback is permanent, not a launch-day stopgap

## File Structure

```
app/
  (auth)/login/
  (dashboard)/
    layout.tsx              ← auth guard + institution scope here
    children/[id]/          ← child profile, session history
    sessions/[id]/          ← active voice/text chat
  api/                      ← Route handlers (server-side only)
  layout.tsx
  globals.css
  middleware.ts             ← Auth + security headers (incl. corrected Permissions-Policy)

src/
  components/
    ui/
    features/
      voice-recorder/       ← mic permission flow, recording indicator
      flag-display/         ← confidence grade + reasoning trail
      referral-record/
  hooks/
  lib/
    api/
    auth/
    utils/
  types/

__tests__/
e2e/
.ai/brain/
.agent/
```

## Pre-Approved Dependencies

| Category | Package |
|----------|---------|
| Framework | next, react, react-dom |
| Language | typescript |
| Styling | tailwindcss |
| Data | @tanstack/react-query, zustand, zod |
| Forms | react-hook-form, @hookform/resolvers |
| UI | @radix-ui/*, lucide-react, clsx, tailwind-merge |
| Testing | jest, @testing-library/react, playwright |

New dependencies require: justification + security check + approval.

## Security Headers (Add to next.config.ts)

```ts
const securityHeaders = [
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  // NOTE: microphone is explicitly needed for this product — do not use the
  // generic template's microphone=() blanket block.
  { key: 'Permissions-Policy', value: 'camera=(), microphone=(self), geolocation=()' },
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains; preload' },
];
```

## Reference

Full web security: `.agent/reference/masterWebSDLC_v1.1.md`
