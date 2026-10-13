# Executed verification task

Run `refactor/verify-gate` from the HCWP target directory. Requires .NET 10,
Python 3, Node.js and installed pinned Playwright Chromium/system libraries.
Missing prerequisites, nonzero commands, empty/failed/skipped reports or browser
runtime errors fail the command; no mock browser or skip fallback exists.

Positive executed evidence: `evidence/gate-results.json` and `gate-*.log`.
Application build: zero warnings/errors. Configured style checks pass. Four model
checks, four fresh-context persistence checks, 40 approved refactor scenarios and
six real Chromium browser groups pass, each with zero failures/skips. Three-way
parity was rerun after formatting; each stage passes 40/40 with exact matching
observations. Approval and accepted Convert prerequisites pass before and after.
The runner retains execution timestamps and source/evidence SHA-256 inventories.

## Current rerun

Reran the gate for the still-unchecked verification task. No validator findings
were supplied. Independent checksum inspection exposed the active caller-log
inventory defect recorded in `evidence/gate-transcript-checksum-failure.json`.
The runner now excludes only its still-open `gate-run.log` transcript, alongside
its own result file; completed check logs and artifacts remain inventoried.
After repair, reran the complete gate and independently checked every retained
source/evidence hash. Build/style, four model checks, four persistence checks,
six real browser groups and all 40 scenarios on each of three implementations
pass with zero failures/skips. No plan checkbox or upstream file was changed.

## Configured style boundary

`refactor/.editorconfig` and `verify-style` configure .NET whitespace verification
for modern authored application/presentation, EF context/seeding, startup and
check-runner/model/persistence C#. Extracted rules, compatibility shells, mappings
and scenario adapter are intentionally not reformatted, retaining inspectability.
This is a configured whitespace check, not an assertion of all possible analyser
rules. JS module, Python runner and shell syntax checks execute; vendored NHSW CSS
and MIT licence must match pinned checksums. Razor is compiled by the app build;
no separate Razor/HTML/CSS linter is configured. Vendored CSS is never reformatted.

## Current browser evidence

`evidence/full-flow-browser/results.json` records Chromium version, six groups,
source identities, live Blazor circuit and zero runtime errors. Executed checks:
all form controls have visible associated labels and official NHSW classes;
assets are local; baseline/error/confirmation/warning/saved states fit
320/768/1280px; keyboard focus has measured visible styling; error summary links
focus invalid input/select; confirmation can be declined/accepted by keyboard;
valid values save and explicitly reload; a fresh browser circuit sees persisted
patient-specific values while its draft remains blank. Four persistence checks
independently prove fresh EF context/entity isolation, full-field read-back,
mutation isolation and rejected-save/patient boundaries.

Screenshots and HTML snapshots retain all six responsive states. Contrast is
computed from rendered colours using SC 1.4.3/1.4.11 thresholds. Official focus
includes qualifying dark/red portions; yellow/page diagnostic pairs are not
claimed to meet 3:1. Disabled Save is inactive and exempt, not treated as a
flat opaque colour. This is bounded component inspection, not WCAG certification,
OS-native popup inspection or original Windows event-delivery verification.

## Findings and disposition

No validator findings were supplied in this invocation. Execution exposed three
runner defects, retained rather than hidden: `gate-style-initial-failure.log`
(applied bash syntax parsing to a Python runner),
`gate-browser-inactive-contrast-failure.json` (attempted flat-colour measurement
on disabled Save opacity), and `gate-browser-retained-focus-failure.json`
(inspected focused Reload as an unfocused boundary). Repairs select the correct
syntax parser, exclude the contrast-exempt inactive control, and blur Reload
before normal-state inspection. Explicit focus contrast checks remain required;
no approved behaviour, scenario, upstream file or library asset was changed.

Only this verification task is addressed. The external plan remains unchanged
and unchecked. Final limitations documentation/completion assessment is the next
unfinished task; this report does not declare Refactor complete. Evidence remains
parity with extracted legacy logic, using synthetic fixtures and temporary EF
InMemory, not original Windows/Oracle or PostgreSQL verification.
