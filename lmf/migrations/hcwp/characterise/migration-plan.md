# KD03 migration slices and shared scenario contract

## Status and gate

`fixtures.json` and `scenarios.json` define shared inputs/outcomes, not execution evidence. The independently inspectable `reference/` harness and `verify` command now exist; construction smoke evidence and actual adaptations are documented in `reference/README.md`. The subsequent task must execute the full suite. The external run plan remains unchecked. Validator finding V01 (save fault versus parent notification) is corrected in the shared contract and implemented/checked at both executable boundaries; this is not a validator approval.

Evidence may establish **parity with extracted legacy logic**, never parity with the original Windows/Oracle application or full save service. Source SHA-256 and original paths are in `fixtures.json` and `behaviour.md`. No Convert/Refactor code is created here. Human approval of the exact completed Characterise revision is required before Convert.

## Deliverable slices (proposed, not approved)

These are vertical deliverables within the agreed KD03 workflow, not permission to introduce other contact types. Each slice passes Characterise, then literal runtime/dependency Convert, then architectural Refactor. Shared scenarios accumulate; none may be weakened to fit a target.

| Slice | Deliverable and dependency boundary | Required shared evidence / acceptance |
| --- | --- | --- |
| 01 — KD03 recording | Already-selected synthetic patient; draft defaults; KD03-only selection; common fields and all five physical assessments; validate, insert parent/given/KDP and optional measurement; fresh persistence read; repeat recalculation on save. Includes invalid submissions and warnings, not just the happy path. | All scenarios in `scenarios.json`; iteration acceptance examples 4, 5, 9, 10. Repeat ordering/isolation/exact grouping/ties/idempotence are part of this slice, not deferred. |
| 02 — literal runtime port | After approval, port the included extracted C# logic to supported modern .NET retaining legacy structure. Replace only unavailable runtime/infrastructure boundaries, list each substitution. No Blazor or persistence redesign in Convert. | Same approved scenario IDs, fixtures and expected projections on reference and converted adapters; acceptance examples 3 and 6. |
| 03 — usable browser delivery | After Convert passes, introduce server-interactive Blazor and EF Core in-memory persistence. Only KD03 offered; reload during a running process reads saved data through a fresh context. Preserve field/save path differences and warning/confirmation decisions. | Same shared suite plus build/style checks and browser add/read-back, invalid no-save and unsupported-code demonstration; examples 3–5, 8–10. Restart data loss explicitly disclosed. |

Slices 02/03 deliver the same functional slice at later assembly lines, not new clinical scope. Do not defer essential validation, physical fields or repeat flags to later feature work. Further workflows require a new bounded seed; patient search, editing/deletion, scheduled entry, appointment/recall processing, PostgreSQL, production deployment and database migration remain excluded.

## Shared JSON contract (version 1)

Both files are UTF-8 JSON objects with `schemaVersion: 1`. Every item in `scenarios` has a unique stable `id`, is `required: true`, and must produce a separate result. No framework-specific test code or target rules are stored in expectations. Source references are keys into `fixtures.json.sourceReferences`, whose values identify original bundle files/methods.

### Fixture resolution and isolation

- Start every scenario with a newly seeded store, clock `2025-03-15T12:00:00`, and examination/measurement sequences starting at 9001/8001. Dates are timezone-free legacy DateTime values; no UTC conversion. Today is `2025-03-15`.
- `patient` names a patient fixture; `history` names a history set (default `empty`). Read existing results for the selected patient before creating the draft. Other-patient fixtures remain in storage for isolation checks.
- `draft` names a full result-input fixture; `overrides` shallowly replaces its fields. Missing overrides mean unchanged, explicit null clears. All fixtures are synthetic except source-backed choice dictionaries. No real patient identifiers are reused.
- Draft fixtures omit patient ID, generated IDs and entry timestamp: creation supplies these from the selected patient, sequences and pinned clock. Other nullable recording fields default to null, withdrawal/repeat false, three declined flags and reschedule N, origin 2. The `unselected` draft has code null and date `0001-01-01T00:00:00`.
- Operational lookup `Description` supplies the examination entity's LongDescription and lookup text; HCP Name1/Name2 and location Name supply fresh-read names. History rows seed linked parent/given/KDP entities with no measurements and the specified raw Y/N repeat string; patient context uses medical preschool consent category 2/type 11. These are dependency fixture mappings, not new business rules.
- `environment` selects `standard` unless specified. Schedule absence is a genuine null range, not a guessed 6–8-week mandate. Source bands are provided, not precomputed range outputs substituted for the aggregation logic.

### Operations: explicit paths, not simulated Windows events

- `draft`: call the parent add path, with empty outstanding appointments; inspect defaults and consent message. Does not save.
- `record`: create draft, set its contact date before `ValidateAndSetExamCode`, then assign recording values through applicable result setters, validate date/nonnull measurements, and save if preceding field checks permit. Assign location type/category first, load and validate lookup lists before assigning location code / `ExaminerKdpCode`, and assign height before weight. Populate raw declined flags before measurements, not via clearing boolean setters (those have their own `decline` scenario). Date validation precedes height, weight and head field validation; BMI notification can occur earlier while assigning measurements. Provide `confirmations` in order; unused or missing responses are a scenario execution error. A false confirmation/field error stops this submission without saving. Setting code must use the guarded delegate path, not bypass it. Do not claim this order is original WinForms event delivery.
- `save`: create a draft and populate the TO directly, then invoke `KdpExaminationDelegate.Save` (file 5), which calls the bounded `SaveKdpExaminationResult` service path (file 44), without field validators. This intentionally tests service validation, including head=150 acceptance and ordered aggregate errors. A missing code reaches the validator; the KD03-only scope guard rejects *nonempty* unsupported codes separately. The service propagates the validator fault; the parent catches `FaultException`, sends `NonFatalErrorEncountered` with `ExamResultsErrorSavingPrompt`, and returns false. Capture the inner fault separately from that observable notification; exceptions must not become skips.
- `field`: populate a draft and invoke the named delegate field method with `value`; no save. `method` is `ValidateHeadCircumference`, `ValidateHeight`, `ValidateWeight`, `ValidateAndSetExamCode`, `ValidateLocationCode`, or `ValidateExaminerCode`. Field fixtures carrying KD03 already do not re-run code selection. A head-null value is not sent to the nonnullable field method.
- `decline`: populate the delegate, apply the listed boolean setter assignments, inspect cleared measurements/required flags, then attempt save through the same parent/service path as `save`, capturing both inner validator fault and parent notification on failure. Explicitly exclude UI event ordering.
- `repeat`: seed existing entities, call extracted `UpdateRepeatFlags` for selected patient/code KD03 `runs` times, commit and read back. These are historical fixtures; do not insert same-day ties through save. Exact grouping is demonstrated using a sentinel KD04 group while asserting only KD03 flags; no unsupported-type recording or repeat outcome is claimed.
- `unsupported`: inspect offered codes and attempt a nonempty unsupported submission through the scope adapter; no legacy-validator attribution.

For `record`, BMI setter notifications are observable but their multiplicity depends on notifications; compare semantic message identities in first-occurrence order, not event count. All other message observations use call order. Numeric calculations use extracted decimal arithmetic, not binary floating point substitutions.

### Expected observation projection

`expected` is an explicit projection of observations, not an echoed output. `base` names a `fixtures.json.observationDefaults` object; resolve it first, then overlay the other expected keys. No-save projections include committed-snapshot equality even where field acceptance is true. `savedFixture` names `fixtures.json.savedProjections`, not the input draft. Choice labels in fixtures are source-backed; operational display names are synthetic. Compare every named key/value; unspecified observations are outside that scenario's assertion. An empty `messages` array asserts no messages, not an unexamined path. An error key list is ordered, preserving numbering order of the save validator. File 27 `ValidateOnSave` throws `ValidationFault.Default` with the numbered aggregate message and `ValidationErrorsPrompt`; file 44 propagates it. File 5 `KdpExaminationDelegate.Save` catches that fault, sends `NonFatalErrorEncountered(ex.Message, KdpResultsTitle, ExamResultsErrorSavingPrompt)`, and returns false. These are two layers of one failure, not two user-visible errors. Preserve both prompt identities without changing legacy behaviour. Field failures retain original prompt identity as mapped in `behaviour.md`.

Common observations:

- `accepted`: field/submission/operation accepted, distinct from whether a save was attempted.
- `saved`: whether a new result was committed; `newRows`: examination/given/KDP/measurement deltas. Every no-save scenario must assert all four deltas zero and unchanged existing storage, including repeats. `storeUnchanged: true` requires a pre/post committed snapshot comparison, not a constant returned by the adapter.
- `messages`: ordered semantic `{kind, key}` items (`Warning`, `Confirmation`, `Error`, `ScopeError`). `errors` are ordered resource keys representing the validator's aggregate message, retained in the parent notification's `ex.Message`; they are not separate notifications. On aggregate save failure, `validatorPrompt` asserts the inner fault's `ValidationErrorsPrompt`, while `savePrompt` asserts the observable parent's `ExamResultsErrorSavingPrompt`. `parentNotification` asserts `{type: NonFatalErrorEncountered, kind: Error, title: KdpResultsTitle, prompt: ExamResultsErrorSavingPrompt}`. Capture these from the actual fault/notification boundaries, not constants supplied by the adapter. This object represents the single aggregate Error notification rather than adding a `{kind, key}` item for each constituent error to `messages`; earlier warnings/confirmations still use `messages`. `accepted: false` includes the parent's false return. Do not invent exact original resource prose.
- `savedFixture` plus `savedOverrides`: resolve an independently specified expected saved projection from fixtures, then compare it to a fresh service/context read. This shorthand does not permit comparing the submitted TO with itself. Read-back requires stable generated IDs, selected ClientId, OriginalExamCode, entry timestamp, optional measurement ID and named recording fields. Descriptions/names use explicitly synthetic lookups.
- `repeatFlags`: map persisted IDs to Y/N, independent of read display order. `unchangedPatients` demands full committed snapshot equality for those patient IDs. `kd03Order` asserts descending saved KD03 dates by ID; no equal-date display tie-break is invented. `sameAfterSecondRun` compares committed snapshots from the first and second recalculations.
- `bmi`: recomputed delegate value, not persisted BMI; `bmiOutsideRange` is the delegate predicate. `expectedRanges` tests raw-band aggregation; `fieldValues`, `requiredFlags`, `draftValues` inspect only named fields.

Additional observations may be emitted for human inspection. Normalisation may remove ephemeral lock/hash values, platform newlines, and repeated BMI notification copies only. It must not hide stored values, errors, warnings, refusal, repeat status or skipped/failed scenarios. Reference documentation must inventory actual adaptations. An unimplementable required projection is a blocker to identify, not permission to remove it.

## Bounded coverage and remaining work

The shared set covers success with/without measurements; ordered validation; all physical fields and counted-result omissions; reason/reschedule; field/save head contradiction; duplicate confirmation and same-day checks; consent/age/deviation/BMI warnings; declined-value clearing; lookup validation; and the five accepted repeat categories. Unsupported codes are explicitly scope-adapter behaviour. These are acceptance examples, not speculative mutation tests.

### Checks performed for this task

Executed from `lmf/migrations/hcwp`:

```sh
python3 -m json.tool characterise/fixtures.json > /dev/null && python3 -m json.tool characterise/scenarios.json > /dev/null && git diff --check -- characterise
```

Exit 0: both JSON syntax checks and tracked whitespace checks passed (new files are not covered by git diff). A separate Python structural inspection also resolved all fixture/expectation/source references, asserted all 40 IDs unique and required, checked no-save zero-delta/unchanged-store projections and verified the bundled-source SHA-256. Its output was:

```json
{"jsonFiles": 2, "requiredScenarioDefinitions": 40, "uniqueIds": true, "fixtureAndSourceReferencesValid": true, "sourceHashMatches": true, "referenceScenariosExecuted": 0}
```

These are definition checks only, not a Characterise gate or executable parity evidence. No human approval was created.

### Validator finding V01 — addressed in definitions

The supplied finding identified conflated inner/outer save prompts in KD03-004–010, KD03-011, KD03-014–015 and KD03-032. Source inspection confirms file 27 throws `ValidationErrorsPrompt` and file 5 replaces the prompt at the parent notification boundary with `ExamResultsErrorSavingPrompt`, retaining `ex.Message`. All 11 definitions now assert `validatorPrompt`, corrected `savePrompt`, and `parentNotification`; ordered errors, no-save storage invariants and declined-field assertions are unchanged. The `save`/`decline` operation contract now explicitly includes the parent catch. This corrects expectations, not legacy logic. Reference execution remains a later task.

Re-ran `python3 -m json.tool` on both JSON files and `git diff --check -- characterise` (exit 0). An inline Python contract check parsed the fixture/scenario files, asserted 40 unique required IDs, verified the exact two prompts and parent notification on all 11 affected IDs, verified resolved no-save zero deltas/unchanged-store expectations, and confirmed unrelated scenarios did not acquire save-fault fields. Output:

```json
{"requiredScenarioDefinitions": 40, "correctedSaveFailureDefinitions": 11, "promptLayersValid": true, "noSaveInvariantsValid": true, "referenceScenariosExecuted": 0}
```

These checks validate definitions only; no reference pass or approval is claimed.

Harness construction update: original snapshots, retained C# logic, explicit compatibility/persistence doubles and `characterise/verify` are now available; see `reference/README.md` for actual substitutions and ten passing filtered smoke checks, including V01. No new validator findings were supplied. No full-suite or approval claim is made, and no plan checkbox is changed.

Next: execute `characterise/verify` without a filter for **every** required ID with positive passes, zero failures, zero skips and per-scenario observations. JSON parsing/contract checks performed in this task are not reference passes. Final `review.md` must identify exact revisions, commands/results, all doubles/exclusions and pending human decisions (including synthetic clinical values, head limits and general-assessment omission). Stop awaiting approval after that mechanical gate; do not manufacture approval.
