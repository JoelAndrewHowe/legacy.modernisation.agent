# HCWP KD03 Refactor parity report

## Executed result

Fresh, separately compiled reference, conversion and refactor runs each pass
**40/40 approved scenarios, zero failures, zero skips and no omitted IDs**.
All 40 complete observation objects match each other and the approved baseline.
This is **parity with extracted legacy logic**, not the original Windows/Oracle
application or full save service. The external plan remains unchanged/unchecked.
This task does not certify the remaining style, persistence and browser gate.

Execution: 2026-10-15T16:28:50.509884+00:00 to 2026-10-15T16:29:01.787485+00:00.
Approved revision (SHA-256 of `characterise/review-files.sha256`):
`5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`.
Source bundle SHA-256: `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`.
Fixtures SHA-256: `ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3`.
Scenarios SHA-256: `409f6d6d8615d0bc851810feed5343e10954750ac52a7d463301ffdd385bad3b`.

## Reproduction and evidence

From `lmf/migrations/hcwp`, run `refactor/run-approved-scenarios`.
Requires Python 3 and .NET SDK 10; EF Core 10.0.0 restore may need NuGet.
`evidence/parity/dotnet-info.log` records the executed SDK/runtime environment.
The command checks current human approval and accepted Convert evidence before
and after execution. It makes byte-identical reference/conversion source copies
in disposable `refactor/.parity-run/`, then builds each independently. The
unmodified reference runs against identical copied inputs to accommodate its
fixed output path; conversion and refactor read the approved inputs directly.
No build or execution writes to Characterise, Convert or approvals.

Executed commands (absolute paths are supplied by the runner):

```sh
python3 refactor/check-prerequisites.py
dotnet build refactor/.parity-run/reference/Reference.csproj --nologo
dotnet refactor/.parity-run/reference/bin/Debug/net10.0/Reference.dll refactor/.parity-run
dotnet build refactor/.parity-run/conversion/Converted.csproj --nologo
dotnet refactor/.parity-run/conversion/bin/Debug/net10.0/Converted.dll characterise refactor/evidence/parity/conversion
dotnet build refactor/checks/Checks.csproj --nologo
dotnet refactor/checks/bin/Debug/net10.0/Checks.dll characterise refactor/evidence/parity/refactor
python3 refactor/check-prerequisites.py
```

All three builds have zero warnings/errors. Under `evidence/parity/`, each stage's
`results.json` retains full per-scenario observations and differences, and
`*-suite.jsonl` retains executed stdout. `*-build.log` retains build diagnostics.
`comparison.json` identifies all tested source files, input/output checksums,
runner checksum, execution timestamps and per-ID matches. The two prerequisite
reports establish unchanged reviewed inputs and accepted upstream evidence.
Exceptions, failed/empty/filtered runs, mismatches and skips fail the command;
no expectations or adapters are altered to achieve parity.

## Per-scenario observations

Full observations are indexed by ID in `evidence/parity/reference/results.json`,
`conversion/results.json` and `refactor/results.json`. Every row below denotes
three positive executed passes and exact full-observation/approved-baseline match.

| ID | Approved scenario | Reference | Conversion | Refactor | Exact / approved match |
| --- | --- | --- | --- | --- | --- |
| KD03-001 | Given a selected patient, adding a draft supplies source defaults | Pass | Pass | Pass | Yes / Yes |
| KD03-002 | Given full KD03 input, record and freshly read common and all physical values | Pass | Pass | Pass | Yes / Yes |
| KD03-003 | Heart alone is a counted result; no measurements or affirmative consent are mandatory | Pass | Pass | Pass | Yes / Yes |
| KD03-004 | Missing code/date and invalid measurements produce ordered aggregate errors | Pass | Pass | Pass | Yes / Yes |
| KD03-005 | A future contact fails save without changing existing records | Pass | Pass | Pass | Yes / Yes |
| KD03-006 | A contact before birth fails save | Pass | Pass | Pass | Yes / Yes |
| KD03-007 | A timestamp after death fails save even on the same day | Pass | Pass | Pass | Yes / Yes |
| KD03-008 | An empty KD03 result is not recordable | Pass | Pass | Pass | Yes / Yes |
| KD03-009 | General assessment alone is omitted from counted results | Pass | Pass | Pass | Yes / Yes |
| KD03-010 | Consent and core component do not count as results | Pass | Pass | Pass | Yes / Yes |
| KD03-011 | Declined-only recording is insufficient and both boolean transitions clear measurements | Pass | Pass | Pass | Yes / Yes |
| KD03-012 | A recorded N shared result counts, without measurements | Pass | Pass | Pass | Yes / Yes |
| KD03-013 | Reason plus reschedule and general assessment saves, because general is not counted | Pass | Pass | Pass | Yes / Yes |
| KD03-014 | Reason plus heart conflicts and saves nothing | Pass | Pass | Pass | Yes / Yes |
| KD03-015 | Rescheduling without a reason fails even with a result | Pass | Pass | Pass | Yes / Yes |
| KD03-016 | Head 150 fails the field path | Pass | Pass | Pass | Yes / Yes |
| KD03-017 | The same head 150 passes direct save and reads back unchanged | Pass | Pass | Pass | Yes / Yes |
| KD03-018 | Head zero uses the distinct field minus-number error | Pass | Pass | Pass | Yes / Yes |
| KD03-019 | Head field's upper endpoint 100 is rejected | Pass | Pass | Pass | Yes / Yes |
| KD03-020 | Exclusive height and weight bounds reject invalid field input | Pass | Pass | Pass | Yes / Yes |
| KD03-021 | Weight upper endpoint 1000 fails field validation | Pass | Pass | Pass | Yes / Yes |
| KD03-022 | No preschool consent warns but does not prevent recording; female testes value is not rejected | Pass | Pass | Pass | Yes / Yes |
| KD03-023 | Age below synthetic schedule warns and still saves | Pass | Pass | Pass | Yes / Yes |
| KD03-024 | Age above synthetic schedule warns and still saves | Pass | Pass | Pass | Yes / Yes |
| KD03-025 | Absent schedule does not invent an age-window rule | Pass | Pass | Pass | Yes / Yes |
| KD03-026 | Raw centile aggregation retains reversed bound naming and endpoint warns without rejecting | Pass | Pass | Pass | Yes / Yes |
| KD03-027 | BMI outside synthetic prescribed limits warns, not rejects, and reads back measurements | Pass | Pass | Pass | Yes / Yes |
| KD03-028 | Declining duplicate-code confirmation retains unselected code and does not save | Pass | Pass | Pass | Yes / Yes |
| KD03-029 | Accept duplicate-code confirmation and save later KD03 as repeat with patient isolation | Pass | Pass | Pass | Yes / Yes |
| KD03-030 | Save earlier KD03 demotes existing earliest and leaves another patient unchanged | Pass | Pass | Pass | Yes / Yes |
| KD03-031 | Same calendar-day duplicate rejects before confirmation despite differing time | Pass | Pass | Pass | Yes / Yes |
| KD03-032 | Direct save also rejects same-day duplicates | Pass | Pass | Pass | Yes / Yes |
| KD03-033 | Existing KD03 flags use chronological order, exact-code grouping and patient isolation | Pass | Pass | Pass | Yes / Yes |
| KD03-034 | All exact earliest timestamp ties remain non-repeat | Pass | Pass | Pass | Yes / Yes |
| KD03-035 | Repeat recalculation is idempotent | Pass | Pass | Pass | Yes / Yes |
| KD03-036 | Demonstration offers only KD03 and rejects unsupported submission without legacy-rule attribution | Pass | Pass | Pass | Yes / Yes |
| KD03-037 | Unknown legacy lookup code fails field validation independently of the scope adapter | Pass | Pass | Pass | Yes / Yes |
| KD03-038 | Unknown location is a field error, not a fabricated save mandate | Pass | Pass | Pass | Yes / Yes |
| KD03-039 | Unused examiner is a field error | Pass | Pass | Pass | Yes / Yes |
| KD03-040 | Missing location type reports error yet null-list field path returns true | Pass | Pass | Pass | Yes / Yes |

## Comparison and findings

Comparison uses parsed JSON object equality: property order/whitespace is ignored;
arrays, scalar values and all emitted fields remain exact. Approved expected
projections execute independently on each stage, followed by full-observation
comparison. No new normalisation was introduced. Inherited adapters pin synthetic
clock/IDs, deduplicate semantic BMI notification copies, exclude ephemeral locks
and use resource keys instead of unavailable original prose; see
`characterise/reference/README.md`. Stored values, calculations, ordered errors,
warnings, confirmation/refusal outcomes and patient-specific repeats are retained.

No new validator findings were supplied in this request. Historical V01 was
rechecked on all three fresh runs for KD03-004–011, KD03-014–015 and KD03-032:
inner `ValidationErrorsPrompt`, outer `ExamResultsErrorSavingPrompt`, actual
`NonFatalErrorEncountered`/`KdpResultsTitle`, no save and unchanged storage match.
No behavioural repair or weakening of approved scenarios was necessary.

## Boundaries

The suite exercises the approved explicit adapter paths, not original Windows
control/event delivery or browser interactions. Refactor executes the real domain,
application and EF Core InMemory persistence; the same independently inspectable
extraction assumptions and compatibility shells still bound the evidence.
Synthetic patients/lookups/schedules/BMI/centile data are not clinical policy.
EF InMemory is temporary and does not prove relational constraints, transactions,
Oracle precision/triggers/concurrency or PostgreSQL compatibility. Original
Windows/Oracle execution and PostgreSQL verification remain absent.
KD03 only: search, edits/deletes, other contacts, scheduled consent withdrawal,
appointment/prefill/recall effects, database migration, Azure and production
security/deployment are excluded. No full save-service or clinical certification
is claimed. Remaining configured style, persistence and browser checks are
separate unfinished plan tasks; this report does not declare Refactor complete.
