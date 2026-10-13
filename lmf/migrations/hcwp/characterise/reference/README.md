# Extracted HCWP reference (Characterise only)

This is an independently inspectable **executable reference**, not Convert or
Refactor code. It can establish parity with extracted legacy logic, **not the
original Windows/Oracle system**, and not the full save service. No approval is
created. The external plan remains unchecked.

## Run

Prerequisites: Linux bash, .NET SDK 10 (build checked with 10.0.401). No NuGet
packages, Windows, Oracle or network service is needed. Python 3 is needed only
for optional regeneration.

From `lmf/migrations/hcwp`, run the complete shared suite:

```sh
characterise/verify
```

This builds the reference, reads the shared `fixtures.json`/`scenarios.json`,
executes every scenario separately, emits one JSON observation/result per ID
and a final summary, writes `reference/evidence/results.json`, and exits nonzero
on a build error, execution exception, missing observation, mismatch or empty
selection. Exceptions are failures, never skips. Build diagnostics are in
`reference/evidence/build.log`. A successful **full** result requires all 40
required IDs, positive passes, zero failures and zero skips. A filtered smoke
run is not that gate.

```sh
characterise/verify KD03-004                 # filtered smoke, not full evidence
characterise/verify --observe-only KD03-002  # observations without comparisons
```

Filtered reports use `results.<ID>.json`; observation-only reports use
`observations[.<ID>].json` and have no passes. Reports include selection/mode,
source, fixture and scenario SHA-256 values. No claim of original-system parity
is made by a passing report. Output is deterministic apart from build logs.

## Inspectable boundaries

- `original/*.txt`: normalized-LF original bundle file bodies (no adaptations).
  Original paths/file numbers and body hashes are in `extraction-manifest.json`.
- `legacy/*.cs`: retained C# parent/result delegates, validator, TOs, date/lookup
  utilities, entity models, measurements service and bounded service/CRUD
  methods. Original banner identities are recoverable from the manifest.
- `extract.py`: reproducible extraction/adaptation and mapping generation,
  pinned to source SHA-256
  `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`.
  Regenerate with `python3 characterise/reference/extract.py`. This overwrites
  generated files deliberately; verification does **not** regenerate them or
  weaken expectations. Review changes against `original/` before accepting them.
- `Mapping.cs`: explicit assignments generated from file 44
  `ConfigureMappings`, including convention-matched scalar properties. It does
  not read scenario expectations. The original mapping configuration is retained.
- `Compatibility.cs`/`Resources.cs`: unavailable framework/base-class shells and
  resource identifiers. `Infrastructure.cs`: committed entity store, separate
  unit-of-work snapshots, lookup/messenger doubles and an inner-fault observer.
- `ScenarioAdapter.cs`: input-only path driver implementing the documented
  shared operation contract. It never reads `expected`, `savedProjections` or
  `observationDefaults`. `Program.cs` resolves and compares expectations **after**
  execution. Object expectations are projections; arrays assert exact order and
  values, except `unchangedPatients`, which asserts requested patient snapshots
  are unchanged (not that every other patient must change).

## Actual adaptations (not business-rule corrections)

1. Use modern .NET only to execute the extracted reference. Keep legacy method
   bodies/names/branches; this is not the product runtime port. No Blazor or EF
   Core implementation is included.
2. Pin file 5's `DateTime.Now` and file 27's `DateTime.Today` to fixture time.
   Oracle sequence calls use deterministic counters from fixtures. Local
   timezone-free DateTime and decimal calculations are retained.
3. Remove region directives (file 24 has an unmatched region in the bundle) and
   unavailable ViewModelBase notification annotation; the actual property-change
   event logic remains. File 42 needs a `Orvex.TransferObjects` import because
   its supplied `ChildMeasurementsRange` import resolves to an absent type.
4. Trimmed result delegate references five undeclared/mismatched setter names
   in `ClearDataFromHiddenFields`: RskResponsiveParenting, RskEngagement,
   RskSocioFactors, DskHearingAndLanguage, DskSpeechAndLanguage. Bind those clearing
   assignments directly to the identically named TO properties. The included
   KD03 setter path still clears hidden data; no new applicability validation is
   invented. Other delegate logic, including decline clearing and null-list
   permissiveness, is retained.
5. Replace absent WCF faults/message bases with tiny shells preserving exception
   inheritance, Detail.Title, message/title/prompt and confirmation response.
   Messenger records sent objects and consumes explicit responses; missing or
   unused responses fail execution. Resource prose/.resx is unavailable: strings
   are original resource identifiers; format call sites are retained. Exact
   original prose/format placeholders and modal rendering remain unverified.
6. AbstractTO uses its supplied dictionary get/default/set and change-list
   semantics in a minimal shell; no inline validators are configured. GenerateLock
   supplies a stable placeholder and enables change events. Lock contents and
   optimistic-concurrency/edit paths are excluded, not asserted equivalent.
   Missing WSX model type and namespace shells exist only to compile entity
   navigation declarations; they have no recording rules.
7. Retain file 42's complete BMI/prescribed/expected range algorithms and file
   43's `UpdateRepeatFlags` method. Repository queries use LINQ-to-objects.
   Include is a no-op after explicit relationship hydration; Local sees the
   hydrated working entity rows. This cannot prove EF6 query translation,
   provider collation or original local-cache loading behaviour. Repeat grouping,
   timestamps, ties and patient filters are still the extracted algorithm.
8. File 44 retains ordinary GetKdpExamination/GetKdpResultTo/fresh GetResult,
   Save, Insert, key allocation and schedule selection bodies. Constructor and
   fields are narrowed to those methods. Update/delete throw unsupported;
   scheduled entry, display-domain model mapping and recall/next-due methods are
   excluded. Outstanding appointments return an explicitly empty fixture list.
   Appointment-status/produced-recall calls remain visible but their boundaries
   are deliberate no-ops. This is **not full save-service parity**.
9. Replace AutoMapper/transfer-object persistence with generated scalar
   assignments from file 44's mappings and naming conventions, including Y/N
   repeat conversion and reason conversion. Null navigation reads use safe access
   as AutoMapper's missing-navigation handling substitute; nullable FK measurement
   ID to long uses default zero. Nullable origin to given byte uses default zero.
   Existing scenarios only use linked measurements with nonnull FK and origin 2;
   absent-navigation display strings/null conversion edge cases are not original
   AutoMapper evidence. These substitutes are inspectable, not independent proof
   of AutoMapper itself.
10. `UnitOfWork` clones committed scalar entity rows and hydrates navigation
    properties per context. Insert maps into new parent/given/KDP/measurement
    rows, repeat logic acts on that context, Commit publishes scalar clones, and
    read-back creates another context and another TO. Observations therefore
    read committed rows rather than echoing submitted form values. Snapshot
    equality compares all writable scalar fields of the four recording tables;
    no-save and other-patient assertions are calculated, not constants.
11. `LookupDouble` supplies explicitly labelled synthetic operational values and
    SQL-backed reason/location choices. Stored procedures/cache/active-date
    endpoint behaviour are unavailable. The missing ActiveDateRange predicate
    uses null/open inclusive bounds in a compatibility filter; fixture schedule
    rows are well within their active dates, so endpoint parity is not claimed.
12. The adapter explicitly drives record setters and validators in the order in
    `migration-plan.md`, not inferred WinForms event delivery. Duplicate-code
    refusal stops recording; direct-save bypasses field validation as specified.
    It enforces KD03-only as a **scope adapter**, not a legacy validation rule.
    Field/save head limits remain contradictory. A rejected raw height=0 save
    does not invoke the BMI getter in observations (it would divide by zero);
    that excluded event-order limitation is not silently fixed.
13. Repeated BMI messages are deduplicated by semantic resource identity in
    first-occurrence order; other messages retain call order. Locks are outside
    expected projections. No dates, stored measurements, warnings, refusal,
    errors or repeat flags are normalized away.

## Validator findings and construction checks

No new validator findings were supplied in this invocation. Previously recorded
V01 is implemented by `ObservedService`, which observes/rethrows the actual
inner validator fault, and the retained file 5 `Save`, which catches it and sends
its actual `NonFatalErrorEncountered` with the different outer prompt. The runner
captures both boundaries. It does not fabricate aggregate messages from
expectations.

Construction smoke commands were run individually for:

`KD03-002`, `KD03-004`, `KD03-011`, `KD03-026`, `KD03-027`, `KD03-029`,
`KD03-033`, `KD03-035`, `KD03-038`, `KD03-040`.

Each command was `characterise/verify <ID>`, each yielded 1 pass, 0 failures,
0 skips. Exact observations/differences are in `evidence/results.<ID>.json`
and stdout captures in `evidence/smoke.<ID>.jsonl`. The build succeeded with
0 warnings/0 errors. KD03-004 and KD03-011 specifically check V01, ordered errors,
no-save storage and (for 011) clearing/required flags.

Those filtered runs remain construction checks. The subsequent unfiltered
`characterise/verify` execution passed **40/40 required scenarios, zero failures,
zero skips**, exit 0; build had zero warnings/errors. Full observations are in
`evidence/results.json` and `evidence/full-suite.jsonl`; `../execution.md`
records required-ID coverage and the V01 checks across all 11 affected scenarios.
No harness logic, fixtures or expectations needed changing. All adaptations and
unverified boundaries above remain limitations, not original-system evidence.
The later review task and human approval remain pending; the external plan is
unchanged. No Characterise completion, human approval, original-system parity
or Convert/Refactor implementation is claimed here.
