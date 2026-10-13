# Refactor input reading and prerequisite verification

Performed only the first unfinished task in `factory/runs/hcwp-refactor/plan.md`.
The external plan remains unchanged and unchecked. No application implementation,
upstream artifact change or human approval creation was performed.

## Inputs reviewed

Read the Refactor seed and plan, `lmf/docs/vision.md`,
`lmf/iterations/001-characterise-and-migrate-hcwp.md`, and the Characterise
behaviour, dependency, gaps, migration-plan, execution and review documents,
fixtures, all 40 scenario definitions and reference adaptation README. Read the
Convert input-reading, approval-verification, PORT, execution,
baseline-confirmation and parity-report documents and verification commands.
Mechanically inspected retained per-scenario results, stdout, comparison identities
and conversion provenance. Historical awaiting-approval/task-pending statements
in upstream documents do not override the current operator-owned approval or
later executed evidence.

## Prerequisite result

From `lmf/migrations/hcwp`:

```sh
python3 refactor/check-prerequisites.py > refactor/evidence/prerequisites.json
```

Exit **0**. This read-only check runs the reviewed inventory check and existing
conversion provenance audit, checks pinned source/vision/iteration identities,
and inspects retained evidence without rebuilding either upstream stage.

- Human approval is current at revision
  `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`;
  all **120** reviewed files match.
- All **46** conversion provenance entries match; only the documented
  runner-output change in `convert/src/Program.cs` differs from the reference.
- Retained reference and conversion executions each cover all **40** required
  IDs, with **40 passes, zero failures and zero skips**, unfiltered verify mode,
  matching source/fixture/scenario hashes and nonempty observations.
- **40 exact full-observation matches** between approved baseline, executed
  reference and conversion. Comparison evidence hashes and copied-reference
  identities match current files. Retained stdout matches the result reports;
  both retained build logs show zero warnings/errors.

`evidence/prerequisites.json` records input/evidence SHA-256 identities and
mechanical results. These are checks of accepted retained execution evidence,
**not fresh scenario execution or a Refactor parity gate**. No prerequisite
blocker was found. Later implementation may proceed under the approved contract;
this task does not claim that Refactor is complete.

## Constraints carried forward

- KD03 only, selected synthetic patient, add and persistence read-back. Preserve
  defaults, all five physical assessments, validation, warnings, confirmations,
  calculations, saved values and patient-isolated repeat recalculation.
- Preserve field/save head-limit differences, counted-results omissions,
  declined-value clearing and Q01–Q13. UX review must explicitly consider the
  declined-value inconsistency; do not silently correct approved behaviour or
  weaken scenarios. No new human decision authorising a behavioural change is
  present.
- Modern .NET, server-interactive Blazor and EF Core in-memory persistence belong
  to the next implementation task. Reload saved data through a fresh EF context,
  not form echo. Separate domain, presentation and persistence responsibilities.
- Vendor official NHSW compiled CSS at a reviewed release/pinned commit, retain
  MIT licence and record checksum/provenance; accessible Razor component markup,
  minimal token-based bespoke styling, only required behaviour scripts, no CDN.
- Later verification must execute the same approved scenarios on all three
  implementations and provide Refactor parity evidence, build/style/persistence
  checks and real browser checks (including responsiveness, keyboard focus,
  labels, error-summary links, contrast and NHSW presentation). Missing browser
  prerequisites fail the gate; require zero failures/skips, not mocked success.
- Evidence is parity with extracted legacy logic, not the original Windows/Oracle
  application or full save service. Synthetic schedule/BMI/centile/lookup inputs
  are not clinical policy. In-memory storage is temporary and does not prove
  relational constraints, transactions or PostgreSQL compatibility. Search,
  edits/deletes, appointment/recall processing, other contacts, production
  infrastructure, Azure and database migration remain excluded/unverified.
- Repeat evidence stays bounded to the approved isolation, exact-code grouping,
  ordering, ties and idempotence cases; no speculative coverage expansion.

## Validator findings

No findings were supplied after the user's findings heading, so no new validator
repair was possible or necessary. Historical **V01** was rechecked in all three
retained reports for KD03-004–011, KD03-014–015 and KD03-032: distinct inner
`ValidationErrorsPrompt` and parent `ExamResultsErrorSavingPrompt`, actual
`NonFatalErrorEncountered`/`KdpResultsTitle` notification, false saved outcome and
unchanged storage remain intact. Their full observations, including ordered
errors, match the approved baseline. No expectations or reference were changed.
This records evidence, not validator approval.
