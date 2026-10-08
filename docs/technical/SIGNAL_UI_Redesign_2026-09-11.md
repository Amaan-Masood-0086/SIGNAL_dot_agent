# SIGNAL workspace redesign

## What changed

The existing Next.js application now uses a consistent pine-green and cool-neutral workspace design. The redesign keeps the existing brand fonts and components, while improving page hierarchy, spacing, action placement, navigation and mobile behaviour. UI Master and redesign-existing-projects informed the audit, interaction-state checks and browser review. Marketing-page animation rules were not applied to operational care screens.

### Caretaker

- Care overview with actual institution totals, age-information counts and archived-record totals. Page-limited counts are labelled.
- Searchable child directory with name/intake sorting and active, confirmed-DOB, estimated-age and archive filters. Search stays in the browser.
- Child profile with prominent text/voice entry points, separate age context and readable screening history.
- Archived children cannot start a new session from the profile. Failed history retrieval is shown as an error rather than “no results”.
- Registration has clearer age choices. Changing age mode clears incompatible hidden inputs so validation does not reject the new choice.
- Session view separates the conversation from guidance. Urdu/mixed-direction observations use automatic direction, and language preference loads after hydration.
- Completing a session is disabled while an unsaved draft remains. Closing/reloading the browser with a draft raises the browser’s unsaved-change prompt; this does not persist the draft or intercept every internal navigation.
- Workspace guide explains registration, observations and result review.

### System administrator

- Separate administration navigation, overview and system-wide context.
- Consistent shared design for staff, child oversight, provider configuration, audit and usage pages.
- Missing cost remains “Not recorded”; unpriced calls are identified as a partial estimate.
- Clearer page descriptions, keyboard-scrollable data regions and native confirmation dialogs with focus containment and restoration.
- Direct visits to caretaker registration/profile pages redirect administrators to child oversight.

The current application has two authenticated roles: caretaker and system administrator. The project overview defines clinicians as downstream referral recipients, not logged-in users. This update does not invent clinician credentials or expand backend access rights.

## Shared UI

- Desktop sidebar and native mobile navigation dialog; Escape closes it and returns focus to the trigger.
- Skip-to-content link, visible focus styling, restrained interaction transitions and reduced-motion support.
- Shared page headings, metric tiles, buttons, badges and data-table styling.
- Redesigned login, workspace loading/error states and unavailable-page view.
- Clear synthetic-data workspace label. Existing light theme is retained.

## Verification

Verified on 2026-09-11: lint and production build passed, 25 unit tests passed, and all 5 browser tests passed. The final browser-run report records `status: passed` with no failed tests.

From `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run test
npm.cmd run build
npm.cmd run test:ui
```

Browser tests use Chrome, the actual Next.js pages and BFF routes, and a separate in-memory fixture server. They do not verify PostgreSQL policies, production authentication, provider accuracy or real clinical workflows. The fixture is only started by the test runner and is not imported by application code.

Test ports: frontend `3015`, fixture API `18119`. Both must be free. Test Next output is isolated in `.next-ui-test/`; browser screenshots and traces are in ignored `test-results/`. If sandbox restrictions prevent Windows test-server cleanup, run the browser test command with the appropriate process permissions.

Scenarios cover caretaker search/profile/session save and reload, mobile navigation and access refusal, switching age modes during registration, administrator screens and confirmation focus, and sign-in/guide layouts on a small phone.

## Boundaries and remaining product work

### Sidebar follow-up

Widened the sidebar to 272px, increased navigation text to 14px, replaced the promotional help block with a compact guide link, and added short-height spacing. Navigation no longer shrinks into its own scroll area. The whole sidebar remains scrollable only when the viewport is too short to fit its contents. Regression checks passed at laptop heights of 650, 768 and 900px, a 450px-height fallback, and a 390px-wide mobile drawer. Both targeted browser tests and lint passed.

- UI polish does not complete the broader product roadmap or enable knowledge base v3.
- The current roster still loads up to 100 active and 100 archived children; search and sorting operate on loaded records. Profile history similarly shows the fetched page, with totals disclosed when incomplete.
- The broader referral-management UI and a clinician portal were not implemented in this redesign. Existing backend referral creation/read/update endpoints do not currently provide a list endpoint for a complete work queue.
- Existing saved-result restoration limitations and safeguarding workflow limitations are not resolved by the conversation layout change.
- The authentication stub, consent/retention decisions and clinical review gates remain as documented in the project audit.
- No migration, clinical grading change, production deployment, commit or push was performed as part of this UI change.

For visual review, generated screenshots include `caretaker-desktop.png`, `caretaker-mobile.png`, `child-profile.png`, `session-desktop.png`, `intake.png`, `admin-desktop.png`, individual admin panels, and desktop/mobile sign-in.
