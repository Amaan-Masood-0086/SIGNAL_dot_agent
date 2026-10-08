# UI_SPEC: SIGNAL

Written 2026-10-08 from the running app. It records what exists; "gap" means a known shortfall, not a plan.

## Users and primary task
| User | Main task | Device reality |
|---|---|---|
| Caretaker (primary) | Describe what they noticed about one child and read a clear next step | Mid-shift, possibly a mid-range Android phone, limited reading comfort in English |
| Administrator | Onboard institutions, staff and children; review audit, usage, providers, knowledge review | Desktop |

Clinicians never sign in. They receive the referral and the reasoning trail.

## Routes and navigation
| Route | Role | Key CTA |
|---|---|---|
| `/login` | all | Sign in |
| `/dashboard` | caretaker | Register a child, open a child |
| `/dashboard/children/new` | caretaker | Register |
| `/dashboard/children/[id]` | caretaker | Start a text or voice observation session |
| `/dashboard/sessions/[id]` | caretaker | Send observation, answer the follow-up |
| `/dashboard/referrals`, `/new`, `/[id]` | caretaker | Confirm referral, save follow-up |
| `/dashboard/guide` | all | Read the guide |
| `/dashboard/admin` and `/staff`, `/children`, `/audit`, `/usage`, `/providers`, `/knowledge` | admin | Manage |

Role boundary: an admin who opens a caretaker-only route is redirected to `/dashboard/admin` (by design).

## Component inventory
Button, Input (label, hint, error with `aria-describedby`), Card, Badge, StatTile, DataTable, ConfirmDialog (focus trap, destructive confirms), Alert, PageHeader, SidebarNav (`aria-current`), skip-to-content link, GrowthCurve motif. Icons are inline SVG.

## Screens x States
| Screen | Loading | Empty | Error | Success | Disabled |
|---|---|---|---|---|---|
| Login | button pending | n/a | wrong details and 429 throttle messages | redirect | pending submit |
| Dashboard roster | `dashboard/loading.tsx` | "Start with your first child"; "No matching children" | `dashboard/error.tsx` | roster | n/a |
| Register a child | submit pending | n/a | inline field errors | redirect to profile | submit pending |
| Child profile | `children/[id]/loading.tsx` | "Start an observation above to create the first record" | `children/[id]/error.tsx` | history card | archive confirm |
| Session chat | "Thinking... Ns" indicator | first-prompt panel | `sessions/[id]/error.tsx` plus inline reasoning errors | graded result card | send disabled while thinking, draft-unsaved notice |
| Referrals | gap: relies on the dashboard boundary | empty list copy | gap: relies on the dashboard boundary | saved referral | submit gated by confirmation tick |
| Admin pages | pending states in panels | empty copy in staff, children, audit, usage | inline alerts | toasts and updated rows | pending buttons |
| 404 | n/a | n/a | `not-found.tsx` | n/a | n/a |

## Data behavior
- All reads and writes go through same-origin `/api/*` proxy routes; the session JWT lives in an HttpOnly cookie. Responses are validated with Zod.
- Server-validated forms; client validation is UX only.
- A session lasts 15 minutes; sign-in is throttled to 5 per 5 minutes per account.
- Reply language choice (Same as I write, Urdu, English) is remembered per device.

## Languages and direction
English UI, `lang="en"`, LTR. Urdu and Roman Urdu are accepted as input and answered in the caretaker's language. **Gap:** an Urdu reply renders in an LTR layout and the page language is not switched.

## Accessibility and quality status (measured 2026-10-08)
| Check | Result |
|---|---|
| axe-core (WCAG 2.0 to 2.2 AA tags), 13 pages x 4 widths (360, 768, 1024, 1440) | 0 violations after fixes |
| Horizontal overflow at the same widths | none |
| Keyboard-only: login, skip link, 19 dashboard focus stops, send an observation | works, focus ring on every stop |
| Lighthouse accessibility (mobile emulation, `/login` and `/dashboard`) | 100 and 100 |
| Lighthouse performance | 82 and 75. App JS is 153 KB over the wire (budget about 170 KB). On this machine an antivirus-injected script adds most of the render-blocking time. LCP is 3.5 to 4.7 s under simulated slow 4G, above the 2.5 s target. |
| Text smaller than 12 px | none |
| Form-control border contrast | 4.56:1 (needs 3:1) |

## Automated gates in the repo
| Gate | Where | Runs |
|---|---|---|
| Token contrast (text 4.5:1, control border 3:1), read from the real `globals.css` | `src/lib/design/contrast.test.ts` | `npm test` (CI) |
| axe-core WCAG 2.0 to 2.2 AA on caretaker and admin pages at 360 and 1440 px, plus no horizontal overflow | `e2e/a11y.spec.ts` | `npm run test:ui` |
| Viewport fit, focus trap, sidebar height, role refusal | `e2e/workspaces.spec.ts` | `npm run test:ui` |

Not automated yet: Lighthouse CI budgets and a keyboard-only end-to-end flow (both were checked by hand on 2026-10-08).

## Assumptions
- Mid-range Android and inconsistent connectivity are the baseline.
- The UI library is custom components on Tailwind 4 (no shadcn/MUI); this was an earlier decision and is kept.
- Light mode only.
