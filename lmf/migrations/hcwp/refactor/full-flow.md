# KD03 full-flow implementation

Historical implementation-task report below. Current six-group browser and
three-way parity/gate evidence supersedes its earlier counts and pending-task
statements: see `verification.md`, `parity-report.md` and
`limitations-and-completion.md` for the final bounded assessment.

Implemented the next unfinished task only; the external plan remains unchanged.
Supplied presentation/evidence validator findings are recorded and addressed in
`validator-findings.md`. Current human approval and complete
matching retained Convert evidence passed the prerequisite check before work.
All changes are within `refactor/`.

## Flow and boundaries

- Circuit-owned draft offers KD03 only and the common fields plus all five physical
  assessments. Patient 101 is fixed; patient identity, existing IDs and other
  contacts are rejected at the application scope boundary.
- Recording uses the approved result/parent delegates and validation rather than
  browser reimplementations of clinical policy. Synthetic lookups resolve names.
  The ordinary save path retains its consent-withdrawal limitation.
- Invalid field/save input displays resource identities in a focused NHSW error
  summary with links focusing applicable controls, associated inline NHSW errors,
  invalid control/form-group styling and ARIA invalid/error associations. Original localised prose is
  unavailable. Aggregated save faults remain intact, including numbered errors.
- Applicable consent, schedule, deviation and BMI warnings are presented without
  converting them into save mandates. BMI is calculated, not persisted.
- Different-day duplicate code requires an explicit yes/no response. The first
  attempt stops before persistence; yes reruns against current saved data, no
  saves nothing. Same-day duplicate is an error, not an overridable confirmation.
- Declined toggles in **either direction** clear their measurement; the UI explains
  this retained inconsistency. Field head limit remains below 100; direct service
  save remains below 1000. General-only/counting omissions are unchanged.
- Save disables the saved draft to prevent accidental double insertion. Start new
  result creates a new draft; Reload is independent of draft input. Saved values,
  generated IDs, lookup names, entry timestamp and patient-specific repeat flags
  are displayed from `ReadPatient`, opening a fresh EF unit of work/context, not
  submitted form values. Unscheduled add has no appointment/recall actions.

## Executed checks

From `lmf/migrations/hcwp`: `refactor/verify-flow` (exit 0).

| Evidence | Executed result |
| --- | --- |
| `evidence/full-flow-prerequisites.json` | Current approval and accepted Convert prerequisites pass |
| `evidence/full-flow-build.log` | Build, zero warnings/errors |
| `evidence/full-flow-model.json` | 4 passes, zero failures/skips: full fixture saved projections, rejected storage invariance, no/yes confirmation and same-day error, warnings/declined clearing |
| `evidence/full-flow-persistence.json` | 4 passes, zero failures/skips: fresh EF contexts, invalid storage unchanged, scope/patient isolation, new model reload |
| `evidence/full-flow-regression/results.json` | All 40 approved scenarios pass against refactor, zero failures/skips |
| `evidence/full-flow-browser/results.json` | Real Chromium 156.0.8078.4, 5 passes, zero failures/skips, zero page runtime errors |

Browser checks exercise the live Blazor WebSocket circuit: no-results rejection,
summary and link focus, all physical fields and measurements persisted, explicit
confirmation refusal/acceptance, repeat and age warning, and a fresh browser
circuit reading the existing patient's data. Keyboard summary links and both
confirmation choices execute with measured visible focus. Input/select errors,
confirmation and official warning-callout markup are inspected at 320/768/1280px:
no overflow; twelve full-page screenshots and HTML snapshots are retained.
The report records 83 rendered contrast measurements, with 78 applicable AA
assertions passing and five explicitly diagnostic yellow/page comparisons.
Saved and repeat-warning screenshots and the server log are adjacent. Missing Chromium or server prerequisites fail the
runner. Retained initial failures and repairs are in `validator-findings.md`.
`evidence/full-flow-source.sha256` identifies tested source and browser tooling.

This is an implementation smoke/regression run, **not fresh three-way parity** or
the complete Refactor gate. The later tasks still require a parity report and
configured style/comprehensive browser checks for the expanded interface.
The changed warning/error and confirmation states now have their own executed
responsive, keyboard, contrast and NHSW evidence; this does not certify every
field or the entire final gate. Historical preview/NHSW evidence
covers the old smaller interface and must not certify the new interface.

Fixtures are synthetic (`src/demo-fixtures.json` copied from the approved fixture
inputs). Schedule, BMI, centile and lookup values are demonstration values, not
clinical policy. EF InMemory is process-lifetime temporary persistence, not proof
of relational constraints, transactions or PostgreSQL compatibility. Original
Windows/Oracle, PostgreSQL, Azure, production authentication/authorisation,
patient search, editing/deletion, other contacts and appointment/recall
infrastructure remain excluded or unverified. Parity claims remain bounded to
extracted legacy logic.
