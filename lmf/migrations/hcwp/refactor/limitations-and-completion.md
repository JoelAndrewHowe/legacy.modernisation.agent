# KD03 Refactor limitations and completion assessment

## Assessment boundary

The required bounded Refactor outcomes have positive executed evidence, with
zero failures and zero skips. This is an evidence-based assessment for validator /
runner review, **not an agent approval or a change to stage state**. The external
plan remains unchanged and its final task remains unchecked. Optional visual
polish and speculative architecture work are not completion blockers.

The claim is **parity with extracted legacy logic** for KD03 add-and-read-back,
not parity with the original Windows/Oracle application, full save service,
other contacts, or a production clinical system. This application alone does not
certify the whole LMF orchestration iteration.

## Synthetic fixtures and origins

`src/demo-fixtures.json` is byte-identical to approved
`characterise/fixtures.json` (SHA-256
`ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3`).
Its `provenance` and `sourceReferences` distinguish recovered choices from
invented demonstration inputs. `src/Persistence/DemoData.cs` seeds the local
store from these inputs; no production patient data is loaded.

- Patients 101 (selected), 202 (isolation), 303 (no consent) and 404 (deceased)
  have invented demographics, dates and consent. The browser fixes patient 101;
  the suite uses the others to exercise approved rules.
- Existing-result histories, drafts and expected saved projections are synthetic.
  Equal-date histories exercise repeat recalculation; they are not evidence that
  the same-day duplicate insertion rule permits those records to be added.
  KD04 is a grouping/scope sentinel, not a supported recording contact.
- The clock is fixed at 15 March 2025, noon; generated examination/measurement
  IDs start at 9001/8001. Scenario runs reset fixtures and sequences. These are
  reproducibility substitutions, not Oracle sequence or wall-clock verification.
- Physical-assessment and categorical choice values come from the supplied
  lookup utility; not-examined reasons and location types come from supplied SQL
  seeds. Operational examiner/location rows (`SYN001`, `SYN002`, `SYNLOC`), staff
  type `SYN` and descriptions are invented. Category 18 is source-offered.
- The 6/8-week schedule row, BMI limits 10/20 and age/gender centile bands are
  invented warning fixtures, **not clinical recommendations**. No exact age
  window is imposed merely from the contact name. The absent-schedule fixture
  preserves the approved absence of an invented age rule.
- Original resources/localisation are unavailable. Resource identities and
  compatibility messages preserve approved observations, not original prose.

Source-backed quirks in approved `characterise/gaps.md` Q01–Q13 remain bounded
limitations, not silently corrected rules. Examples include field head limit
below 100 versus direct-save below 1000, clearing measurements on declined
transitions in either direction, counted-result omissions, no invented
sex-specific testes rejection, schedule ordering and raw centile-bound semantics.
The UI explanations do not authorise clinical policy changes.

## Persistence and infrastructure limitations

EF Core InMemory 10.0.0 provides actual temporary persistence in this process.
Reload and saved display use `ReadPatient` and a fresh EF unit of work/context,
not form-value echo. The executed persistence checks prove fresh context/entity
isolation, saved-field read-back, mutation isolation and rejected-save/patient
boundaries. New browser circuits can read the same process store; restarting
resets it. This is not durable storage, backup or database migration.

InMemory is not a relational database. These checks do not establish relational
FK/length/precision enforcement, transactions and rollback, provider SQL
translation/collation, Oracle empty-string/null behaviour, triggers, sequences,
concurrent-user correctness or production concurrency handling. Reconstructed
source schema and copied entity names do not establish database compatibility.
No original Windows Forms/.NET Framework/EF6/Oracle application was built or run;
original binding/event order, controls and modal rendering remain unverified.
**No PostgreSQL connection, persistence or compatibility verification occurred**;
Azure Database for PostgreSQL is an eventual destination, not this demonstration.

Excluded: patient search; editing/deleting saved results; other contacts;
scheduled entry and appointment-prefill flow; appointment-status changes,
recall clearing/processing and next-due calculations; existing database migration;
Oracle connectivity; Azure deployment; production authentication, authorisation,
security hardening and operational infrastructure. Ordinary unscheduled add does
not prove scheduled consent withdrawal or full save-service parity. Sentinel
entities and empty appointment fixtures do not imply these services execute.

## Positive executed evidence required for review

Run from `lmf/migrations/hcwp`: `refactor/verify-gate`.
`verification.md` describes prerequisites and configured style boundaries;
`evidence/gate-results.json` records execution times, commands and SHA-256
inventories. `evidence/completion-assessment.json` records the final independent
inspection of the gate, parity and retained identities for this task.

| Required outcome | Executed evidence |
| --- | --- |
| Current human Characterise approval and matching accepted Convert evidence | `evidence/gate-prerequisites-before.log`, `gate-prerequisites-after.log`; approved revision `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` |
| All approved scenarios unchanged, matching reference/conversion/refactor | `parity-report.md`, `evidence/parity/comparison.json` and all three per-scenario reports: 40/40 each, 40 exact approved-baseline matches, no omissions/failures/skips |
| Modern .NET build and configured style | `evidence/full-flow-build.log` (zero warnings/errors), `gate-style.log`, completed format logs |
| Full model and independent persistence read-back | `evidence/full-flow-model.json`, `full-flow-persistence.json`: four passes each, no failures/skips |
| Real browser valid/invalid save, warnings, confirmation and reload | `evidence/full-flow-browser/results.json`: six real Chromium groups, live Blazor circuit, no failures/skips/runtime errors |
| NHSW presentation and applicable accessibility/responsive inspection | Same browser report and screenshots/HTML: labels, error links, keyboard focus/confirmation, measured contrast and six states at 320/768/1280px; `nhsw-provenance.md` pins official local assets, licence and checksums |

Browser inspection is bounded Chromium component evidence, not full WCAG
certification, assistive-technology certification, native OS popup inspection or
all-browser coverage. Missing browser prerequisites fail the gate; historical
failed attempts remain retained, not relabelled as passes. Historical preview
reports cannot substitute for current full-flow evidence. Configured style is
whitespace plus specified syntax/assets checks, not every possible analyser or
a separate Razor/HTML/CSS linter. These accurately documented non-blocking
boundaries do not require optional polish or new speculative tests.

No validator findings were supplied with this invocation. No approval record,
upstream scenario, behaviour, fixture or plan checkbox was changed.
