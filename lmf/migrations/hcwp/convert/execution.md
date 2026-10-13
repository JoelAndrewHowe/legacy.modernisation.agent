# Approved dual scenario execution

Performed the next unfinished plan task: execute identical approved scenarios on the reference and conversion and capture per-scenario observations. The external plan was not changed or marked done. This is execution evidence, not a declaration that Convert is complete; `parity-report.md` and the remaining gate tasks are still pending.

## Command and observed outcome

From `lmf/migrations/hcwp`:

```sh
convert/run-approved-scenarios
```

Exit **0**. Both independently built executables ran all **40** required IDs, KD03-001 through KD03-040, in `verify` mode without a filter: **40 passed, 0 failed, 0 skipped**, no omitted IDs. The complete observation objects match each other exactly and match the approved Characterise report for every ID. The source, fixtures, expectations and retained implementation were not changed to obtain passes.

The command first checks provenance/current approval and executes `convert/verify`. Because the approved reference runner writes evidence relative to its input directory, the command copies reference files and shared JSON inputs byte-for-byte into disposable `convert/.reference-run/`, verifies every copied hash, builds that independent reference project and runs its unmodified runner. This prevents a rebuild from altering the approved packet's build logs or results. The conversion never delegates to that reference executable. All new execution artifacts are within `convert/`.

Evidence:

- `evidence/results.json` and `full-suite.jsonl`: conversion per-scenario executable observations and expected-projection comparisons.
- `evidence/reference-results.json` and `reference-full-suite.jsonl`: fresh reference observations and comparisons against the identical expectations.
- `evidence/scenario-comparison.json`: ordered ID coverage, per-scenario exact observation comparisons, approved-baseline comparisons, copied-reference hashes and evidence hashes.
- `evidence/build.log`, `reference-build.log`: actual build diagnostics.
- `evidence/execution-port-audit.json`, `approval-check.log`, `execution-post-approval-check.log`: provenance and approval inventory checks before/after execution.

Approved revision remains `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`; every reviewed file still matches. Runtime prerequisites remain Python 3, bash and .NET SDK 10. No added comparison normalisation: parsed JSON object equality ignores formatting/property order only; arrays and scalar values are exact. The approved adapter's existing message/lock/platform-formatting treatment is unchanged and documented in `PORT.md`.

## Validator findings

No findings were supplied after the user's findings heading. Historical **V01** was rechecked on both fresh executions for KD03-004–011, KD03-014–015 and KD03-032 (11 scenarios). Each retained the inner `ValidationErrorsPrompt`, outer `ExamResultsErrorSavingPrompt`, actual parent notification with `KdpResultsTitle`, false saved outcome and unchanged committed storage. Their ordered errors and other approved expectations passed. No repair was necessary; this does not assert validator approval.

## Limitations

Evidence establishes only **parity with extracted legacy logic**, not the original Windows/Oracle system or full save service. Synthetic operational/clinical values, head-limit contradictions, declined-value quirks, mapping/persistence doubles and all approved Q01–Q13 limitations remain unchanged. Windows event delivery, real resource prose, AutoMapper/EF6/Oracle provider behaviour, constraints/triggers/concurrency, appointment/recall processing, excluded contact workflows and PostgreSQL/production deployment remain excluded or unverified. This task does not introduce Refactor work or amend operator approval.
