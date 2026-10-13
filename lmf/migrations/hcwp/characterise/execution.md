# Required scenario execution

Performed the next unfinished task only; the external plan was not edited or marked done. Final `review.md` is the separate remaining task. No approval or Convert/Refactor work was performed.

## Command and results

From `lmf/migrations/hcwp`:

```sh
characterise/verify > characterise/reference/evidence/full-suite.jsonl 2>&1
```

Exit: **0**. Build: **0 warnings, 0 errors**. Required scenarios KD03-001 through KD03-040: **40 passed, 0 failed, 0 skipped**. No reference logic, fixtures or expectations were changed to obtain this result.

Evidence:

- `reference/evidence/build.log`: actual build diagnostics.
- `reference/evidence/full-suite.jsonl`: per-scenario observations/comparisons and final summary.
- `reference/evidence/results.json`: machine-readable full report, mode `verify`, no scenario filter; every result has nonempty observations and an empty differences array.

An independent JSON coverage check compared the ordered required IDs from `scenarios.json` with the report IDs, checked uniqueness and all 40 observations, and verified the summary counts. All checks passed. Observations include saved read-back projections, storage changes/no-save snapshots, validation errors and warning/confirmation keys, and repeat flags. Comparison remains the documented projection contract, not exhaustive equality of every original-system detail.

## Validator findings

No new findings were supplied after the user's findings heading. Previously recorded **V01** was checked across KD03-004–010, KD03-011, KD03-014–015 and KD03-032: all 11 passed. Each observed `ValidationErrorsPrompt` at the inner validator boundary and `ExamResultsErrorSavingPrompt` at the retained parent's `NonFatalErrorEncountered` boundary, with title `KdpResultsTitle`, no saved result and unchanged storage. No new repair was necessary. This records execution, not validator or human approval.

## Evidence identity

Repository HEAD at execution: `c91c1bb1f80b3eb709a7753f0ede5d106ab204b8` (working tree evidence identified separately below).

| File | SHA-256 |
| --- | --- |
| Original source bundle | `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2` |
| `fixtures.json` | `ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3` |
| `scenarios.json` | `409f6d6d8615d0bc851810feed5343e10954750ac52a7d463301ffdd385bad3b` |
| `reference/evidence/results.json` | `7a507fabf93a11a11cf088ec0858a9e04c08386e89a6538321f131029b1f42cc` |

## Remaining limitations

No required scenario is blocked or has an indeterminate expected outcome. `gaps.md` Q01–Q13 and `reference/README.md` retain their classifications and adaptations. In particular:

- Evidence is **parity with extracted legacy logic**, not the original Windows/Oracle system or full save service.
- Windows controls, bindings/event delivery, resource prose, Oracle/EF6/AutoMapper provider behaviour, constraints/triggers and concurrency remain unverified, non-blocking evidence limitations for these determinate scenarios.
- Appointment/recall processing, other contact workflows, edit/delete, PostgreSQL and production deployment remain intentional exclusions. KD03-only rejection is a scope adapter rule.
- Patient/lookups/schedule/centile/BMI values are explicitly labelled synthetic inputs, not established clinical truth.
- Contradictory head limits and other source quirks are preserved for human review, not harmonised. The accepted repeat categories passed; no speculative cases were added.

Final review must still record the exact reviewed artifacts/revision and pending human decisions before the operator-owned approval gate. Passing this task does not constitute that review or approval.
