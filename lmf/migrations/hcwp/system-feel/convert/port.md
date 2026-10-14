# Task 2 — isolated .NET port

No validator findings were supplied. Inspected the working tree before starting; preserved unrelated changes. Task remains unchecked. No application or approved input was edited.

## Source and adaptations

`src/Converted.csproj` targets modern .NET 10 with no packages or application/reference project dependencies. Converted C# is physically separate, not linked to or generated at runtime from the reference. The approved extracted rules already compile on modern .NET; translation therefore deliberately retains their bodies instead of rewriting them.

| Converted file | Approved origin and scope |
| --- | --- |
| `src/PatientSummaryAndResults.cs` | `characterise/reference/Legacy.cs`: C005 name, C008 address, C012 age, C017 Organisation, C015 school, C027 physical values, C010 missing-text branch, C018 ShowAlert, C021 selected-patient all-KDP query, C022 complete date-descending delegate. |
| `src/Compatibility.cs` | `characterise/reference/Compatibility.cs`: approved DTO/navigation graph, symbolic resources/constants, LINQ repository and clock doubles. |
| `src/ObservationAdapter.cs` | `characterise/reference/Program.cs`: approved selected-ID single-row summary mapping, status/gender/resource requests, alert condition observations, mixed-history graph reconstruction and explicit KD03 restriction after all-KDP retrieval. Approved physical/facet observations are retained as an adapter, not a persisted aggregate status or filter implementation. |

Only header comments and an isolating `Hcwp.SystemFeel.Converted` namespace change the first two files. Observation adapter additionally changes Main's signature and inserts a prerequisite subprocess before reading requests. No scenario expectations or fixtures are embedded. `check-port.py` mechanically confirms all remaining source text is identical (3 checks, zero failures/skips); exact input/output hashes are in `evidence/task-2-build/port-preservation.json`. This preservation check is NOT executable parity.

All previous Characterise adaptations remain as disclosed in `characterise/reference/README.md`: controlled clock, synthetic navigation/authority repositories, missing resources represented as identities/arguments, symbolic status/centre constants, explicit mapping instead of AutoMapper, no-op excluded access dependency, and saved-row identity mapping. Nulls, missing-value branches, trailing separators, month arithmetic, literal status `7`, first-centre selection, SingleOrDefault failures, both date-descending sorts and unspecified equal-date order remain untouched. Other saved metadata survives JsonExtensionData; no new recording/repeat/measurement logic is introduced.

No routes, UI, bilingual copy, NHSW assets, filters, paging or recorded-date/ID tie-breaks were added. Organisation is not renamed Health board. LINQ's incidental tie stability is not a legacy guarantee.

## Commands and retained evidence

From `lmf/migrations/hcwp`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/check-prerequisites.py --evidence-prefix task-2-prestart
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/build.py --evidence-prefix task-2-build
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/check-port.py
dotnet system-feel/convert/src/bin/Release/net10.0/Converted.dll
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/check-prerequisites.py --evidence-prefix task-2-final
```

Prestart, build prerequisite and final read-only packet gates passed; all approved baseline/input identities remain unchanged. Approval revision remains `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655`. Gate evidence is in the corresponding exclusive-created directories under `evidence/`. Build passed with SDK 10.0.401, zero warnings/errors; `task-2-build/build.json` binds source/binary hashes and timestamps, with exact output in `build.log`. Bare DLL execution deliberately returned 2 before reading requests (`runtime-gate.json`). `git diff --check -- system-feel/convert` passed.

Build reruns need a fresh prefix. Runtime protocol: `dotnet system-feel/convert/src/bin/Release/net10.0/Converted.dll --evidence-prefix <fresh-prefix>` verifies approval before consuming JSON-line requests. This entry point is a local observation adapter, not a hosted product. Use the documented Release output layout so the gate can resolve its location. Direct C# method invocation by another host is not an approval gate; future integration must own that boundary. `check-port.py` is a one-shot Task-2 structural evidence check, not a reusable parity entry point.

## Handoff and limits

Next task must execute the exact approved fixtures/scenarios and compare every converted observation to the reference, including source-ordering evidence. No scenario execution, positive scenario count, reference rerun or Convert parity is claimed here. Neither task nor stage is marked complete.

Evidence is extracted logic plus approved adapters, not original Windows/Oracle/EF6 execution. Synthetic data, missing clinical prose/numeric constants, local demo, draft Welsh, existing EF InMemory target, unverified PostgreSQL/production and deferred load testing limitations remain. Iteration-001 sources/scenarios/approval/reports and current application were not built, rewritten or rebaselined.
