# KD03 literal runtime/dependency port

## Baseline and ownership

Approved revision: `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` (SHA-256 of `characterise/review-files.sha256`). Source bundle SHA-256: `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`. The operator approval was checked before construction; every reviewed inventory entry still matches afterward.

`src/` is a literal, separately compiled copy of the approved extracted C# slice. The reference already executes on .NET 10; consequently this conversion does not need further changes to business method bodies. Copying retained logic is intentional, not delegation: `Converted.csproj` compiles only its own C# files, with no project/package/reference-assembly links, reference invocation or dynamic loading. Shared JSON inputs/expectations are read from Characterise; reference executable code is not used at runtime. Original banner identities and normalized originals remain independently inspectable in the approved extraction manifest and original snapshots. `source-provenance.json` records copied-file hashes and local changes.

No Blazor, EF Core, object-model cleanup, persistence redesign, new business rules or clinical policy was introduced. Legacy namespaces, names and control flow remain, including the locally owned `ReferenceClock` identifier (it is not a reference-program dependency). The only C# changes relative to the extracted baseline are runner argument handling and writing reports exclusively under Convert.

## Runtime and dependency substitutions retained

These are inherited from the accepted extraction, not newly proven equivalence with the unavailable dependencies:

| Original dependency / adaptation | Convert implementation and boundary |
| --- | --- |
| .NET Framework 4.5.1 / Windows | `src/Converted.csproj`: supported `net10.0` console program, checked with SDK 10.0.401 on Linux. No Windows presentation or WCF host. |
| WinForms/Janus control delivery | `src/ScenarioAdapter.cs` explicitly drives the approved draft/record/save/field/decline/repeat/unsupported paths in their approved order. No event-order/visibility parity claim. |
| Current clock / Oracle sequences | Local `ReferenceClock` in `Compatibility.cs` supplies fixture Now/Today for parent, validator and active filter; `UnitOfWork.GetNextId` in `Infrastructure.cs` uses fixture counters. Timezone-free DateTime and decimal calculations retained. |
| Missing WCF faults and message bases | `Compatibility.cs` shells retain exception inheritance and Detail.Title; retained message classes and `Messenger` record real notifications and consume explicit responses, failing missing/unused responses. |
| Missing resources / display helpers | `Resources.cs` returns original identifiers; formatting call sites retained. `GetDisplayName` returns enum identity. Original prose/localisation/control rendering unverified. |
| AbstractTO / notification annotations / WSX type | `Compatibility.cs` supplies dictionary defaults/change-list shell, stable lock placeholder and absent namespace/model/interface shells. Retained ViewModelBase event logic; unavailable notification annotation removed. Inline validation/optimistic concurrency excluded. |
| Bundle compilation defects | Retained extraction removed region directives (including unmatched region), added measurement TO import, and bound five undeclared hidden-field clearing setters directly to their TO members. No KD03 applicability or validation rules added. |
| AutoMapper / TO persistence extensions | Local `Mapping.cs` uses explicit scalar assignments recovered from file 44 configuration and naming convention, Y/N repeat and nullable reason conversion. Navigation safe access, measurement FK null-to-zero and origin null-to-zero are inherited substitutes; absent-navigation edge cases are not AutoMapper proof. |
| EF6 / Oracle repository and contexts | `Infrastructure.cs`: LINQ-to-objects queries, hydrated relationships, no-op Include, Local working rows. Scalar-cloned working context commits to separate entity storage; saved read-back opens another context and returns a new TO, not the draft. No provider, schema constraint, precision, collation, trigger or concurrency proof. |
| Lookup services / stored procedures / cache | `LookupDouble` reads labelled synthetic operational records plus source-backed reason/location choices. No unavailable service, endpoint or production-value evidence. |
| Centile/BMI options / schedule | Synthetic raw bands/options/schedule supplied to retained algorithms. Missing ActiveDateRange implementation uses inclusive null/open bounds; fixtures avoid endpoint ambiguity. Preserve first matching schedule row, reversed range aggregation and decimal midpoint-to-even arithmetic. |
| Full service / appointment / recall infrastructure | `legacy/KdpExaminationService.cs` retains bounded read, save, insert, schedule and key-allocation methods. Outstanding appointments empty; retained CRUD appointment-status/recall boundary calls are no-ops. Edit/delete throw unsupported. Not full save-service parity. |
| Observations and comparison | Input-only adapter receives no expected outcome. Local runner resolves expected projections after execution. BMI message copies deduplicated in first-occurrence order; other messages ordered. Locks excluded, platform error-line endings trimmed. No stored values/errors/warnings/refusal/repeats normalized away. |

## Preserved rules and findings

Q01–Q13 and the inconsistent declined setters remain as approved: field head limit 100 versus save limit 1000, counted-result omissions, no invented gender/category whitelist, date/day duplicate distinction, exact-code/patient/full-timestamp repeat grouping and earliest ties, permissive null lookup lists and disclosed display/event-order quirks. KD03-only rejection is the scope adapter, not a newly attributed legacy rule. Zero-height rejected raw-save observations avoid the BMI getter; arbitrary setter ordering remains unverified.

No new validator findings were supplied in this invocation. Historical V01 remains addressed by local `ObservedService` observing/rethrowing the actual inner validation fault and the retained parent catching it and emitting the actual outer notification. Construction checks KD03-004 and KD03-011 observe distinct `ValidationErrorsPrompt` / `ExamResultsErrorSavingPrompt`, ordered errors and unchanged committed storage. No reference, fixture or expectation was amended.

## Construction checks, not a stage gate

From `lmf/migrations/hcwp`:

```sh
convert/verify KD03-002
convert/verify KD03-004
convert/verify KD03-011
convert/verify KD03-026
convert/verify KD03-029
convert/verify KD03-038
convert/verify KD03-040
```

Each exited 0 with 1 pass, 0 failures, 0 skips. Build succeeded with 0 warnings/errors. Reports and stdout are under `convert/evidence/`; these are seven filtered construction checks only. No fresh reference suite was run; approved reference evidence was left untouched. Complete same-input dual execution and `parity-report.md` remain later plan tasks. Neither Convert completion nor full-suite parity is claimed. The plan remains unchecked.

Only **parity with extracted legacy logic** can eventually be claimed. Original Windows/Oracle execution, EF6/AutoMapper semantics, appointment/recall processing, unsupported workflows, PostgreSQL and production deployment remain excluded or unverified.
