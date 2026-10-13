# KD03 refactor architecture task

Implemented the next unchecked architecture task only. The external plan remains
unchanged; this document is not a completion attestation. The supplied browser
evidence finding is recorded and addressed in `validator-findings.md`. No upstream
inputs, scenarios, reference, conversion evidence or human approval were changed.

## Boundaries

- `src/Domain/`: approved transfer contracts, validators, calculation/choice
  utilities and compatibility resource identities. `Kd03Scope` encapsulates the
  add-only, selected-patient, KD03-only boundary. These guards are migration scope,
  not newly attributed legacy rules.
- `src/Application/Kd03Recording.cs`: narrow add/read use case. It obtains current
  patient context, invokes the reviewed save rules and reads the saved result
  through a separately created unit of work. It never returns the submitted DTO.
- `src/Persistence/`: EF Core 10.0.0 in-memory database, scalar entity model,
  reviewed mapping and save/measurement/repeat services, deterministic synthetic
  seeding. Each unit of work owns/disposes its own `RecordingContext`; inserted
  rows and changed repeat flags are tracked and saved by EF, not committed to a
  cloned dictionary. Separate contexts share one application-lifetime database.
- `src/Presentation/`: circuit-scoped preview form state and preserved field-rule
  delegates. `src/Components/` supplies server-interactive Razor presentation.
  Rendering and form state are separate from save validation and persistence.
- `checks/`: separately executable approved-scenario adapter and architecture
  checks. Expected observations are not provided to application/domain code.
  It references the application assembly, not the conversion/reference assembly.

The retained rules use their original namespaces to keep source correspondence
inspectable. Refactoring is focused on the useful persistence/application/browser
boundaries; wholesale renaming or rewriting already-characterised calculations
is not necessary to introduce those boundaries. The inherited compatibility
message/lookup helpers currently remain beside the storage adapter; the preview
does not use them as browser interaction substitutes.

## EF mapping decision

All fourteen included row types are real EF entities with scalar properties and
synthetic generated shadow `StorageId` keys. Navigation properties are ignored by
EF and assembled using the approved `Store.Link` mapping after rows are loaded.
The repository compatibility boundary uses LINQ-to-objects over EF-tracked rows;
it does **not** claim SQL translation or relational behaviour. This deliberately
preserves the approved fixture ordering, ties, nulls and lookup mapping instead
of inventing unavailable Oracle keys/constraints. `Tables` is a loaded working
set/inspection view, not the durable save mechanism. Fresh read contexts load
from EF. `Store.Clone` is retained compatibility utility, no longer used by unit
of work construction or commit.

`RecordingDatabase` isolates scenario stores and supplies a shared root within
one running application. Synthetic sequence allocation is locked. There is no
claim of concurrent-user transaction correctness; EF in-memory supplies neither
Oracle transactions nor relational constraints. This is bounded local synthetic
storage, not PostgreSQL verification or a production persistence design.

## Executed evidence

Run from `lmf/migrations/hcwp`:

```sh
refactor/verify-architecture
```

Final exit **0** with .NET SDK **10.0.401**:

- Current approved inventory and accepted Convert provenance/evidence check pass.
- Build: **zero warnings, zero errors** (`evidence/build.log`).
- All **40/40** approved scenarios execute against the new application assembly
  and EF-backed unit of work; **zero failures, zero skips**. Full observations
  exactly match both retained approved reference and accepted conversion results
  (`evidence/results.json`, `architecture-scenarios.jsonl`,
  `architecture-comparison.json`). The comparison records source file hashes.
- **4/4** architecture checks pass, **zero failures/skips**
  (`evidence/persistence.json`): full-field fresh-context read-back, no storage
  change for rejected input, KD03/patient/add-only boundary, and fresh presentation
  model loading existing application data. DTO mutation after save does not
  change persisted values; entities loaded by two EF contexts are distinct.
- `refactor/verify-preview` executes real Chromium Save and Reload interaction:
  **3/3 passes, zero failures/skips or browser runtime errors**. A newly saved
  patient-101 result survives unsaved draft changes and Reload, then loads in a
  new browser context/server circuit and survives another Reload. Live Blazor
  WebSocket traffic, rendered HTML, screenshots, traces and source/artifact
  hashes are retained in `evidence/browser-preview/`; `http-preview.json` now
  links that executed evidence. Fresh EF context mechanics are additionally
  verified by the four persistence checks above, not inferred from a screenshot.
  This is bounded preview verification, not the comprehensive browser gate.

The architecture suite uses unchanged approved fixtures/expectations; it does not
run either upstream implementation afresh. It is not the later three-way parity
gate or the Refactor completion gate. Initial compile failures (missing entry
point while scaffolding, missing routing import and internal repeat-helper test
access) were repaired; the final retained build and executions pass.

## Behaviour carried forward

All approved outcomes remain exercised, including field/save head-range
contradiction, counted-result omissions, all five physical assessments,
declined-value clearing on both transitions, aggregate errors, actual inner and
parent save prompts, warnings/confirmations, synthetic BMI/centile calculations,
patient-specific saved values and repeat recalculation/isolation/ties.
Historical V01 is covered by exact full observations for KD03-004–011,
KD03-014–015 and KD03-032: `ValidationErrorsPrompt`, actual parent
`NonFatalErrorEncountered` / `KdpResultsTitle` / `ExamResultsErrorSavingPrompt`,
false saved outcome and unchanged storage. No expectation was weakened. The new
browser-evidence repair adds executed checks without changing approved rules or
the preview controls; see `validator-findings.md`.

## Remaining plan tasks (not claimed here)

The current page is explicitly labelled **architecture preview**: date and heart
entry plus persisted read-back. It does not yet expose the complete recording
field inventory, field-validation/warning/confirmation flow or full saved-value
presentation. Those belong to the next full-flow task. Do not treat its direct
save preview as evidence of field-path or confirmation UX equivalence.

Official pinned NHSW assets/licence/provenance, NHSW accessible Razor markup,
complete browser flow, fresh three-way parity/report, configured style checks,
and comprehensive real browser responsive/focus/labels/error-link/contrast/
presentation checks remain required. No missing browser prerequisite is treated as success. No
Refactor gate or task checkbox has been marked complete.

Synthetic patients, clock, sequences, lookups, schedule ages, centile bands and
BMI limits come byte-for-byte from the approved fixtures and are not clinical
policy. Data survives page/circuit reloads during one process, but resets on
restart. Original Windows/Oracle execution and actual PostgreSQL/Azure behaviour
remain unverified. Search, edit/delete, other contacts, scheduled results,
appointment/recall behaviour, database migration, production authentication and
deployment are excluded. Evidence is **parity with extracted legacy logic**, not
with the original application or full save service.
