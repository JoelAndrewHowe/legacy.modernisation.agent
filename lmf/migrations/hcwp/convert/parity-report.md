# HCWP KD03 Convert parity report

## Result and scope

Fresh execution of `convert/run-approved-scenarios` exited **0**: reference **40/40 passed**, conversion **40/40 passed**, **0 failures, 0 skips, 0 omitted approved scenarios**, and **40 exact observation matches**. Every fresh reference observation also matches the approved Characterise observations. This establishes **parity with extracted legacy logic**, not parity with the original Windows/Oracle application or the full save service.

The final baseline-confirmation task was executed again; see `baseline-confirmation.md` for its mechanical evidence. The external plan remains unchanged and unchecked; this is not an agent declaration that Convert is complete. No approved source, scenarios, fixtures, reference files or operator approval were amended. No Refactor work was introduced.

## Revisions and evidence identities

Paths below are relative to `lmf/migrations/hcwp`. Repository HEAD at the latest execution: `71d72cf14d3ca056783024f25659ecbb85a5d4fd`; content hashes, not HEAD alone, identify working-tree evidence.

| Input or artifact | SHA-256 |
| --- | --- |
| Approved `characterise/review-files.sha256` revision | `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` |
| Repository-root source bundle `example-code/HCWP Core (pseudonymised) - single file.txt` | `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2` |
| `characterise/fixtures.json` | `ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3` |
| `characterise/scenarios.json` | `409f6d6d8615d0bc851810feed5343e10954750ac52a7d463301ffdd385bad3b` |
| `convert/source-provenance.json` | `597495a804e535601b0e0b1fd2ff6ec46c381f0115914f9727d206213f1a7e0c` |
| `convert/run-approved-scenarios` | `f3314276a29bd60a367b0fd80e9484c0cbbf4c4c9cd8259298654159afaf9ca5` |
| `convert/verify` | `5208dda9d94c61636e2be42bb7de7530206a9008aa43f9df3916f550fde3b2e9` |
| `convert/audit-port` | `aeaa16a949c6cdd6eea179f630b6f69b49837bfb6c653206c371cafd67c7e03f` |
| Fresh `convert/evidence/reference-results.json`, `convert/evidence/results.json`, and approved `characterise/reference/evidence/results.json` (each) | `7a507fabf93a11a11cf088ec0858a9e04c08386e89a6538321f131029b1f42cc` |
| Fresh `convert/evidence/reference-full-suite.jsonl` and `convert/evidence/full-suite.jsonl` (each) | `62df3e65384fcec406458037b81934ad97f483e6497f89bda8c7dfca53c09666` |

Operator-owned `approvals/characterise-approved.md` covers the current packet. The verification checked its approved state/revision, every reviewed file hash and pinned source/vision/iteration inputs before execution. A post-execution inventory check also passed. `source-provenance.json` identifies every compiled local file; `evidence/execution-port-audit.json` records the audit. `evidence/scenario-comparison.json` records copied reference file hashes, evidence hashes and per-ID matches.

## Repeatable verification

Prerequisites: Linux bash, Python 3 and .NET SDK 10 (observed **10.0.401**). From the repository root:

```sh
lmf/migrations/hcwp/convert/run-approved-scenarios
```

Equivalent command from `lmf/migrations/hcwp`: `convert/run-approved-scenarios`. Do not pass a scenario filter for parity verification. Observed summary:

```json
{"total":40,"passed":40,"failed":0,"skipped":0,"omitted":[],"exactObservationMatches":40,"v01Checked":["KD03-004","KD03-005","KD03-006","KD03-007","KD03-008","KD03-009","KD03-010","KD03-011","KD03-014","KD03-015","KD03-032"]}
```

The command runs the provenance audit and `convert/verify`, which builds `convert/src/Converted.csproj` and executes `Converted.dll` with the approved Characterise inputs and Convert evidence output. It copies the approved reference and identical fixtures/scenarios byte-for-byte to disposable `convert/.reference-run/`, verifies copied hashes, builds `Reference.csproj`, and executes its unmodified runner. This avoids writing reference build logs/results into the approved packet. Conversion is separately compiled and never delegates business work to the reference.

Both runners use `verify` mode with null scenario selection and identical source/fixture/scenario hashes. Each checks the same approved expected projections. The dual command additionally requires the complete ordered unique required-ID set, positive passes, nonempty observations, no differences/failures/skips, exact full observation equality between executions, and equality to the approved baseline. An assertion/build/execution failure returns nonzero, with diagnostics retained.

Evidence under `convert/evidence/`:

- `results.json` / `reference-results.json`: full per-scenario observations, statuses and expected-projection differences.
- `full-suite.jsonl` / `reference-full-suite.jsonl`: executable stdout for every scenario.
- `scenario-comparison.json`: per-ID exact and approved-baseline comparison outcomes, no omitted IDs and hashes.
- `build.log` / `reference-build.log`: build diagnostics.
- `execution-port-audit.json`, `approval-check.log`, `execution-post-approval-check.log`: provenance and current packet checks.

## Per-scenario results

Every row below has **reference pass, conversion pass, exact full observation match, approved-baseline match**. Observations themselves are retained in the two complete result reports, indexed by these identifiers; no scenario is represented solely by this table.

| ID | Approved observation area |
| --- | --- |
| KD03-001 | Draft defaults |
| KD03-002 | Full recording and fresh read-back, including all physical assessments |
| KD03-003 | Heart-only save without mandatory measurements/consent |
| KD03-004 | Ordered aggregate invalid-input errors |
| KD03-005 | Future-date no-save |
| KD03-006 | Before-birth no-save |
| KD03-007 | After-death timestamp no-save |
| KD03-008 | Empty-result no-save |
| KD03-009 | General-only counted-result omission |
| KD03-010 | Consent/core counted-result omission |
| KD03-011 | Decline setter transitions, clearing and no-save |
| KD03-012 | Recorded N counts as a result |
| KD03-013 | Reason/reschedule/general save |
| KD03-014 | Reason/heart conflict no-save |
| KD03-015 | Reschedule without reason no-save |
| KD03-016 | Head 150 field rejection |
| KD03-017 | Head 150 direct-save acceptance and read-back |
| KD03-018 | Head zero field error |
| KD03-019 | Head 100 field endpoint rejection |
| KD03-020 | Exclusive height/weight bounds |
| KD03-021 | Weight 1000 field rejection |
| KD03-022 | Consent warning and female testes acceptance |
| KD03-023 | Below-schedule age warning with save |
| KD03-024 | Above-schedule age warning with save |
| KD03-025 | Absent schedule, no invented age rule |
| KD03-026 | Reversed centile bounds and endpoint warning |
| KD03-027 | BMI warning and measurement read-back |
| KD03-028 | Duplicate-code confirmation declined, no-save |
| KD03-029 | Duplicate confirmation accepted, later repeat, patient isolation |
| KD03-030 | Earlier insertion recalculates repeats, patient isolation |
| KD03-031 | Same-day field duplicate rejection |
| KD03-032 | Same-day direct-save duplicate rejection |
| KD03-033 | Repeat chronological ordering/exact-code grouping/isolation |
| KD03-034 | Earliest timestamp ties remain non-repeat |
| KD03-035 | Repeat recalculation idempotence |
| KD03-036 | KD03-only scope offer/rejection |
| KD03-037 | Unknown code field rejection |
| KD03-038 | Unknown location field rejection |
| KD03-039 | Unused examiner field rejection |
| KD03-040 | Missing location type error with permissive null-list return |

## Comparison and normalisation

The approved runners compare named expected projections; unspecified observations are outside that scenario's expected assertions. The dual command compares **entire emitted observation objects**, not only those projections. Parsed JSON equality ignores object property order/formatting; arrays and scalar values remain exact. In this run the complete result files and stdout also match byte-for-byte, as their hashes show.

Inherited approved adapter treatment remains unchanged: deterministic synthetic clock and sequences; timezone-free dates and decimal arithmetic; resource/message identifiers instead of unavailable original prose; semantic BMI notification copies deduplicated in first-occurrence order; other messages ordered; ephemeral locks excluded and platform error-line formatting trimmed. The expected unchanged-patient subset assertion is retained. No saved values, errors, warnings, refusal outcomes or repeat flags are removed to obtain parity. Full details of runtime/dependency substitutions are in `convert/PORT.md`.

## Validator findings

No new findings were supplied after the user's findings heading. Historical **V01** was addressed in the approved baseline and rechecked on both fresh executions for KD03-004–011, KD03-014–015 and KD03-032 (11 scenarios). The actual inner fault yields `ValidationErrorsPrompt`; the retained parent emits `NonFatalErrorEncountered` with `KdpResultsTitle` and outer `ExamResultsErrorSavingPrompt`. All affected scenarios preserve ordered errors, return false for saved, and leave committed storage unchanged. Executable comparisons passed; no additional repair or weakening of expectations was necessary. This records findings/evidence, not validator approval.

## Limitations and exclusions

- This is an independently compiled literal modern-.NET copy of approved extracted C# logic. The reference was already adapted to .NET 10. Shared inherited compatibility doubles limit independence from extraction assumptions; passing both does not establish correctness of missing original infrastructure.
- Windows control binding/event delivery/visibility/modal behaviour and exact resource prose remain unverified. The explicit adapter operation order is not proof of original UI event ordering.
- Local mapping, LINQ-to-objects repositories and cloned committed storage stand in for AutoMapper/EF6/Oracle. Fresh read-back uses a new context/TO, not echoed input, but provider semantics, constraints, precision, collation, empty strings, triggers, transactional failures and concurrency are unverified.
- Patients, operational lookups, schedule, centile bands and BMI limits are labelled synthetic fixtures, not clinical policy or recovered production values.
- Approved Q01–Q13 and declined-value quirks remain preserved, including field/save head-limit disagreement, counted-result omissions, permissive null lookup lists, schedule/range quirks and date/day repeat/duplicate distinctions. Arbitrary setter ordering, zero-height UI reachability, corrupt historical data and display-mapping edge cases remain unverified.
- Appointment statuses, recalls/prefill, scheduled save, editing/deletion, search, other contact workflows and historical database migration are excluded. KD03-only rejection is migration scope enforcement, not a rule attributed to the legacy validator.
- No Blazor/EF Core redesign, PostgreSQL/Azure compatibility, production deployment/security or original Windows/Oracle execution is claimed. Browser delivery belongs to Refactor.

Fresh executable evidence confirms parity with the current approved Characterise baseline; `baseline-confirmation.md` records the final task's checks. The external plan checkbox remains untouched, and completion is left to the validator/runner.
