# Validator findings

## Current NHSW task

### Finding: missing current-interface AA contrast evidence

The validator reported that `browser/nhsw.mjs` asserted button colour and focus
styling but measured no foreground/background contrast, and provenance deferred
contrast to the later full-flow task. This is a deficiency in the **current
NHSW integration**, not a request to implement the remaining full flow.

Added `browser/contrast.mjs` and integrated executed measurements into the real
Chromium NHSW check. The report records rendered text, headings, hints, labels,
input/select values, select SVG arrow, both buttons, hover and focus states,
control boundaries, persisted summary values and the existing generic error
including programmatic summary focus. Responsive text/control measurements
also execute at 320/768/1280px. No business rules, upstream files, vendored CSS,
human approvals or plan checkboxes changed.

Executed `refactor/verify-nhsw`: current approval/Convert prerequisites and
asset checksums pass; application builds with zero warnings/errors; Chromium
156.0.8078.4 executes six passing check groups, zero failures/skips.
`evidence/nhsw-browser/results.json` contains **146 measured colour pairs**,
**141 passing applicable AA assertions** (SC 1.4.3 and 1.4.11) and five diagnostic
pairs. Yellow/page contrast is 1.103:1 and is not itself claimed to meet 3:1;
the official dark or red adjacent focus portions pass. `nhsw-provenance.md`
now documents actual ratios, thresholds, measurement method and boundaries
rather than deferring current contrast. Screenshots and server/build logs are
retained beside the report; it includes timestamps and tested-source hashes.

Initial test failures are retained in
`evidence/nhsw-browser-contrast-initial-failure.json` (flat-background guard
rejected the reviewed right-aligned select SVG) and
`evidence/nhsw-browser-contrast-outline-expectation-failure.json` (computed
outline shorthand colour/style/width order differed from the assertion).
The guard now explicitly handles that reviewed SVG and measures its fill;
unknown images/opacity still fail. The shorthand assertion now checks actual
style and width without assuming order. The final executed report passes.

Full-flow/error-link implementation, fresh three-way parity and the complete
Refactor gate remain pending. These measurements are not a full accessibility
certification, native OS popup audit or AAA focus-area claim. No plan item is
marked done.

# Historical finding: executed architecture-preview browser evidence

## Finding supplied

`evidence/http-preview.json` recorded `browserExecuted=false` despite
`src/Components/Pages/Recording.razor` introducing server-interactive Save and
Reload controls. HTTP prerendering and direct model checks did not demonstrate
browser-circuit interaction or permit inspection of the current interaction.
The requested repair is preview-only, not early implementation of the later
full-flow, NHSW or comprehensive browser-check tasks.

## Repair and executed evidence

Added pinned Playwright tooling in `browser/` and `verify-preview`. No change to
the page or approved business rules was necessary. The test launches a freshly
seeded real app, uses real headless Chromium and requires live `_blazor`
WebSocket traffic. It does not mock requests, events, storage or the circuit.

Executed from `lmf/migrations/hcwp`:

```sh
refactor/verify-architecture
npm ci --prefix refactor/browser
(cd refactor/browser && npx playwright install chromium)
refactor/verify-preview > refactor/evidence/browser-preview-run.log 2>&1
```

- Prerequisites: current approved inventory and accepted Convert evidence pass.
- Architecture: 40/40 approved scenario observation matches, four persistence
  checks pass; zero failures/skips. Build has zero warnings/errors.
- Preview browser: **three passes, zero failures, zero skips**, no browser
  runtime errors. Chromium 156.0.8078.4 / Playwright 1.64.0.
- Save through the circuit records result 9001 for synthetic patient 101,
  date 2025-02-20, heart 1 and repeat false.
- Editing the draft to 2025-02-21 / heart 2 without saving and clicking Reload
  preserves the saved 2025-02-20 / heart 1, not the unsaved inputs.
- A separate browser context creates a new server circuit/form model. Its draft
  returns to the default date and blank heart while persisted values remain.
  Clicking Reload there retains the same patient-specific result.
- Fresh EF read-context mechanics are established by the existing executed
  persistence checks and inspected `RecordingPageModel.Reload` →
  `Kd03Recording.ReadPatient` → service unit-of-work factory, not by assuming a
  new browser context alone proves a new EF context.

`evidence/browser-preview/results.json` retains assertions, saved values,
WebSocket observations and source/artifact SHA-256 identities.
`evidence/http-preview.json` now records executed browser evidence and links it.
PNG screenshots and rendered HTML show initial, saved, unsaved-draft reload and
fresh-circuit reload states. Both Playwright traces contain interaction snapshots
for inspection; the application log is adjacent. The unsaved-draft screenshot
was also inspected directly and shows the draft differs from persisted values.

The first run failed because Playwright's matching browser executable was
missing. That real failure is retained in
`evidence/browser-preview-prerequisite-failure.log`; installing Chromium repaired
the prerequisite (`evidence/browser-install.log`). No missing prerequisite was
converted into a pass or skip. The final run is successful.

## Scope left unchanged

All work is confined to `refactor/`; the external plan is unchanged and no task
is marked done. Full field/error/warning/confirmation browser flow, NHSW assets
and presentation, responsive/focus/label/error-link/contrast checks, fresh
three-way parity and the complete Refactor gate remain later tasks. This report
addresses the supplied evidence deficiency, not validator approval or original
Windows/Oracle/PostgreSQL verification.
