# Convert input reading

Performed only the first unfinished task in `factory/runs/hcwp-convert/plan.md`: read the required vision, iteration and Characterise handoff. The plan remains unchanged and unchecked. No implementation, approval creation/amendment, or parity claim was made. Approval verification is the next separate task and must precede implementation.

Repository HEAD at inspection: `74036c48e399c22b7301621bcc5c20937884e242`. Paths below are repository-root relative unless prefixed `characterise/`.

## Inputs reviewed

Read `lmf/docs/vision.md`, `lmf/iterations/001-characterise-and-migrate-hcwp.md`, the Convert seed and run plan, and the target's Characterise documents: `behaviour.md`, `dependencies.md`, `gaps.md`, `migration-plan.md`, `input-reading.md`, `execution.md`, `review.md`, `fixtures.json`, `scenarios.json`, `reference/README.md`, `reference/extraction-manifest.json` and `verify`. Checked the full reviewed-file hash inventory, including retained reference source and executable evidence. This is handoff/input inspection, not an implementation source audit or a fresh scenario run.

| Input | SHA-256 |
| --- | --- |
| `lmf/docs/vision.md` | `a5280da556de24f8d6d9254df5b1bdd22ace59c7fc0a5ac64b9485dd71483444` |
| `lmf/iterations/001-characterise-and-migrate-hcwp.md` | `73c53da335f85625dd0ce180d69eec64a21431f9ab8247a58520e0dfbd3addcd` |
| `characterise/review-files.sha256` | `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` |
| `characterise/review.md` | `a897980fd9d66f3342b307296de5036c7efaad47b4ad9a36ca99e0a584817f27` |
| `characterise/fixtures.json` | `ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3` |
| `characterise/scenarios.json` | `409f6d6d8615d0bc851810feed5343e10954750ac52a7d463301ffdd385bad3b` |
| `characterise/reference/evidence/results.json` | `7a507fabf93a11a11cf088ec0858a9e04c08386e89a6538321f131029b1f42cc` |

## Constraints retained

- Operator-owned approval must cover the current reviewed revision, scenarios and reference artifacts. Do not create or amend approval; absent/stale approval requires a human-owned blocker and no implementation.
- Scope is KD03 add and fresh persistence read-back for an already-selected synthetic patient, including validation, warnings, physical fields and bounded repeat recalculation. Preserve control flow and legacy structure.
- This is a C# runtime/dependency port to modern .NET, not a language rewrite. Work only under `convert/`; document substitutions in `PORT.md`. No Blazor, EF Core persistence redesign, business-rule fixes or Refactor work.
- Preserve field head range 0–100 versus save range 0–1000 (exclusive), counted-results omissions, decline clearing, nullable fields, schedule-derived warning behaviour and lack of an invented gender-specific testes restriction.
- Repeat evidence remains bounded to patient isolation, exact-code grouping, timestamp ordering, earliest ties and idempotence. Do not expand speculative cases.
- Retain all required KD03-001–040 identifiers, inputs and expected projections. A converted implementation must not execute/delegate to reference code. Later evidence must compare both executions and disclose normalisation.
- Evidence can establish only parity with extracted legacy logic, not the original Windows/Oracle application or full save service. Appointment/recall processing, Windows event delivery, original provider behaviour and PostgreSQL remain excluded/unverified. Operational and clinical fixture values are synthetic.

## Checks at this step

From `lmf/migrations/hcwp`, `sha256sum --check characterise/review-files.sha256` exited 0: every inventoried file matches. Read-only JSON inspection confirmed the retained report has all 40 ordered required scenario IDs, nonempty observations and zero differences. These inspect existing Characterise evidence; no reference rebuild or scenario execution occurred and no Convert gate passed. Characterise inputs/evidence were not modified.

## Validator findings

No findings were supplied after the user's findings heading, so no new validator defect could be addressed. Existing V01 is documented as addressed by Characterise: inner `ValidationErrorsPrompt` and outer parent `ExamResultsErrorSavingPrompt` remain distinct, with the actual parent notification and no-save storage assertions. Preserve that contract in subsequent conversion; no scenario or reference repair was necessary during input reading. This note does not claim validator approval.
