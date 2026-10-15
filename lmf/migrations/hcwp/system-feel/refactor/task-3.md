# Task 3 — shared shell, patient banner and routes (not marked done)

Validator finding addressed: `PatientBannerValues.cs` labelled the organisation value “Organisation”, `ShellChecks.cs` rejected “Health board”, and `verify-task-3` required unchanged generic organisation fixtures, contradicting approved decision 1. The target now uses the approved **Health board** label and a separately adapted Welsh-health-board fixture. The plan is unchanged and this task remains unchecked.

## Current accessibility validator findings and repair

The validator found that the five smoke groups in `task-3-health-board-verified/browser/results.json` did not measure current-shell contrast or visible navigation/link focus, and that the alert fixture had only HtmlRenderer markup evidence. That packet is historical and is not current accessibility certification.

Added executable English route checks to `refactor/browser/shell.mjs`, reusing `contrast.mjs`. Chromium measures rendered text, controls, link focus backgrounds and contrasting underline portions, including NHSW navigation's focused child span and `.nhsw-link::after`. Real Tab traversal reaches every link on patient summary, populated results, saved details, safe missing details and recording routes at 320/1280px. Each focused link has a screenshot, a `:focus-visible` assertion and computed-style/contrast observations. The checks exposed unstyled route links and the brand link's low-contrast browser-default focus: route/error/save links now use pinned `nhsw-link`; the redundant clickable brand is now non-interactive identity markup (navigation remains explicit). No bespoke CSS or vendor changes were introduced.

`ShellChecks --shell-browser-fixture` exports a test-only document containing the **real PatientBanner component**, using the existing approved alert graph through `PatientSummaryQuery`, fixed demonstration clock and local pinned CSS. Chromium intercepts only a test-document URL; there is no product endpoint, patient switching or alternative banner implementation. It checks the accessible alert role and exact name **Important: Patient alert — synthetic demonstration**, both complete synthetic alert texts, visibility, responsive overflow and rendered contrast. Retained Chromium accessibility snapshots exclude the decorative icon and contain the named alert and both paragraphs. This proves browser presentation/accessibility-tree semantics, not an assistive-technology live-announcement timing audit. The normal no-alert fixture is checked for absence of alert containers on every route.

Executed from the target root:

```sh
system-feel/refactor/verify-task-3 --evidence-dir system-feel/refactor/evidence/task-3-accessibility-passing
```

The revision-bound packet retains source hashes, exact commands, versions, timestamps, screenshots, renderer HTML and accessibility snapshots. Passed: immutable-input/current approval checks; unchanged historical Convert parity **53/53**; shared comparisons **34/34**; iteration-001 **40/40**; query **43/43**; persistence **4/4**; recording **4/4**; banner **4/4**; Chromium **7/7**, with **986 contrast observations** and **42 keyboard-focused links**. Zero failures/skips. The verifier requires positive browser counts, passing applicable contrast thresholds, visible keyboard focus and both alert layouts. `task-3-accessibility-verified` retains the initial focus failure; `task-3-accessibility-final` retains a harness clock namespace build error, repaired before the passing run. Intermediate browser development runs under `/tmp` are not acceptance evidence. No old evidence was rewritten. Later bilingual/filter work remains out of scope; the plan checkbox is unchanged.

## Scope and provenance

Completed the existing partial implementation in `refactor/src`, preserving unrelated working-tree changes. `MainLayout.razor` shares the shell and selected-patient banner across `/results`, `/results/{ResultId}`, `/record` and `/patient-summary`. `/` remains a recording alias for existing local links; it is not a second recording implementation. The patient-summary navigation destination is a context-only view, not patient search/switching. Results and detail components use `Kd03ResultsQuery`, never the persistence store. Existing recording controls, validation, clearing, warnings, confirmation and application service are retained. Saving offers a saved-detail link and history link; read-back uses human descriptions rather than technical identifiers. Complete detail grouping and URL-backed list state belong to task 4.

`DemoPatientSummaryRepository` is a replaceable synthetic graph adapter. `patient-summary-fixtures.json` copies `patients.selected` and `patients.alert` from approved `system-feel/characterise/fixtures.json`. Under human-approved decision 1, the target-only `SYNORG1` authority name is **Cardiff and Vale University Health Board**, a Welsh health board. This public organisation name is real; its association with the entirely synthetic patient is invented for demonstration, not an actual record or service relationship. All other graph values, including the nonauthority sentinel, remain identical. `verify-task-3` mechanically permits exactly this name substitution and rejects other graph drift. Characterise inputs and Convert lookup/formatting are untouched: the target retains the converted `SYNORG1, <name>` formatting while deliberately labelling the value **Health board**. This is an approved presentation/fixture adaptation, not legacy wording or a claim that arbitrary organisations are boards.

Patient names, addresses, non-validating NHS-number strings, schools and alerts retain the approved packet's synthetic provenance. The normal patient has no alert; component tests execute both alert and no-alert fixtures and require the board label/name without generic organisation wording. Chromium checks require the same mapping across routes. Other/unavailable patient requests fail closed. The fixed clock is 15 March 2025, matching recording and approved summary calculations. Internal client identifiers are not displayed. Missing legacy school-format/status prose remains honestly unavailable, not fabricated.

## Pinned NHSW integration review

The existing CSS and licence pins are unchanged; see `refactor/nhsw-provenance.md`. The identity asset is copied byte-for-byte from the **same** commit, not from a moving branch:

- Repository: https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library
- Commit: `043d882318918e2a4e8847e16fc3bfe694973c08`
- Upstream: `preview/assets/nhsw-logo.svg`
- Local: `refactor/src/wwwroot/vendor/nhsw/nhsw-logo.svg`
- SHA-256: `41d8993c511627d36aea058c397b5a743ef9c17031a8dbba62fa826404cf4df7`
- Existing local `LICENSE` applies. This is reviewed local dependency reuse, not production branding approval.

Reviewed that commit's `preview/_includes/site-header.html`, `preview/_includes/site-footer.html`, `src/components/site-navigation/macro.njk` and `preview/examples/warning-callout-default.html`. Translated header, navigation/current-page semantics, main/width container, footer, summary lists and warning-callout structure into Razor. Decorative callout icons are hidden; alerts are named, prominent and non-dismissible. The footer contains local-demo limitations rather than invented policies or an unsupported content licence claim. Two static navigation links use the upstream always-visible overflow variant; no overflow menu/behaviour script is needed for this bounded English shell, checked at 320px. Welsh/zoom expansion remains a later gate. No bespoke colours, fonts, spacing, breakpoints or runtime CDN were added.

The skip link explicitly uses the current path/query plus `#maincontent`, because a bare fragment resolves against `<base href="/">` and can navigate to the recording alias. `tabindex="-1"` and Blazor focus handling make the target focusable, with a native current-path fragment fallback. This is an intentional lifecycle adaptation, not legacy behaviour.

## Validator correction verification

Before edits, `verify-task-2 --evidence-dir system-feel/refactor/evidence/task-3-health-board-prestart` passed current immutable-input/approval checks, unchanged complete historical Convert parity and application regressions. After edits:

```sh
system-feel/refactor/verify-task-3 --evidence-dir system-feel/refactor/evidence/task-3-health-board-verified
```

Passed: current immutable-input/approval gate; unchanged historical Convert parity **53/53**; shared reference/Convert/application **34/34**; iteration-001 comparisons **40/40**; query **43/43**; persistence **4/4**; recording flow **4/4**; banner **4/4**; Chromium **5/5**. No failures/skips in the final packet. Commands, hashes, versions and screenshots are retained there. The earlier `task-3-health-board` packet records a failed browser assertion that expected the board name without the converted code prefix. The assertion was corrected to require the unchanged converted formatting; application conversion behaviour was not changed. Historical evidence below remains historical. Final bilingual/slice gates are still later work.

## Earlier executed evidence and repairs

From `lmf/migrations/hcwp`:

```sh
system-feel/refactor/verify-task-3 --evidence-dir system-feel/refactor/evidence/task-3-reviewed
```

This runs the current approval/immutable-input gate, verified complete historical **53/53 Convert parity** with unchanged source identities, current shared SF reference/Convert/application comparisons (**34/34**), iteration-001 three-way comparisons (**40/40**), query checks (**43/43**), persistence (**4/4**), recording flow (**4/4**), patient-banner component checks (**4/4**) and real Chromium shell/route smoke groups (**5/5**). Required checks reject empty, failed or skipped evidence. Logs, exact commands, SDK/Node/browser versions, source hashes and screenshots are retained in that fresh packet. This is task-specific verification, not `system-feel/refactor/verify` or the final gate.

Earlier runs are retained under `evidence/task-3-shell/`: a skip-link assertion initially exposed the bare-fragment/base-URL navigation bug. An event-only repair was insufficient; the path-qualified href fixes the native fallback too. Follow-up smoke failures exposed test assumptions about FocusOnNavigate's initial h1 focus and asynchronous route rendering; the test now walks backwards by keyboard to the skip link and waits for the current route's rendered shell. These failed runs are historical, not counted as passes. An upstream API request returned HTTP 403; an immutable Git checkout supplied the reviewed source and exact matching logo bytes instead.

Browser assertions cover saved read-back after detail reload, history navigation, safe absent-result routes, active navigation, landmarks, keyboard skip focus, 320/1280px route layouts, local CSS/logo response hashes and zero external requests/runtime errors. The browser's `2201` route is **absent** in the empty-start app, not proof of a stored other-patient row. Actual stored-other-patient isolation is covered by the query/persistence/shared-scenario tests; browser isolation fixtures belong to task 4. The live app intentionally still starts without the 23-result history until that task.

## Boundary and limitations

No iteration-001 approved input/reference/parity artifact, Characterise approval, Convert source or plan checkbox was changed. Existing recording behaviour is covered by parity and flow checks; moving to human-readable read-back is an intentional presentation enhancement, not a claim of unchanged DOM. Historical browser scripts still expecting raw-ID read-back need the planned task-6 extension, not silent weakening of source scenarios. Filters/pagination controls, full grouped detail inventory, long histories, central bilingual strings, language/draft retention, bilingual accessibility/contrast and the final gates remain later tasks. This is an English local synthetic demonstration with EF InMemory, extracted-reference parity only, no Windows/Oracle/PostgreSQL or production assurance, and no professionally reviewed Welsh.
