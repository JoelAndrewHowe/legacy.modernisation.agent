# Task 2 — query integration; not marked complete

## Validator correction — shared SF application-boundary evidence

Finding: retained SF comparisons covered reference versus Convert only; three-way evidence covered KD03 scenarios and query checks used other fixtures/pass labels. Addressed with an input-only observation mode in the existing partial `QueryChecks`, an executable shared-SF comparator, and mandatory integration in `verify-task-2`. Full finding, field projections, deterministic tie normalization, infrastructure exclusions and extracted-reference limits are recorded in `shared-scenarios.md`.

Fresh `evidence/task-2-shared-sf-final-recheck/` passes current prerequisites, build, **34/34 approved shared SF application-boundary comparisons**, **43/43 query checks**, **4/4 persistence checks**, and **40/40 iteration-001 three-way comparisons**, zero failures/skips. It retains exact resolved inputs, live reference/current outputs, verified historical Convert outputs, approved/projected expectations, full per-scenario comparisons, hashes and commands. No approved inputs/reference artifacts were changed. Task and plan remain unchecked; no later task was started.

## Validator correction — preserve shared legacy getter (2026-10-15)

Finding: `KdpExaminationResultTO.cs:94` changed shared legacy getter behaviour outside this behaviour-preserving task. The original throws for stored null, while the replacement returned null; passing scenarios did not authorize that bug fix.

Addressed: restored the getter exactly to the HEAD implementation (`GetPropertyOrDefault<DateTime>`). Nullable-date handling is now exclusively `Kd03ResultsQuery.RecordedDate`, reading the existing property bag for query ordering and presentation. No human scope expansion was requested or assumed. Added executable checks proving the shared getter still throws for stored null and the adapter preserves populated dates; existing null-last ordering and explicit-absence checks exercise the adapter. The earlier intentional-correction disposition below is superseded, not approved scope.

Fresh `evidence/task-2-legacy-getter-fix/` records passing current approval/immutable-input checks, verified historical 53/53 Convert parity and current source hashes, build, **43/43 query checks**, **4/4 persistence checks**, and **40/40 approved three-way regression comparisons**, zero failures/skips. Task and plan remain unchecked; no later task started.

## Earlier doer recheck (2026-10-15)

No new validator findings were supplied in this request; the earlier findings and their dispositions remain below. The next unchecked task already has its query/summary implementation, so this pass retained it and reran `verify-task-2` rather than starting later work. Fresh evidence is in `evidence/task-2-doer-current-validation/`: current revision-bound approval/immutable-input checks passed, historical 53/53 Convert parity and its current source hashes verified, build passed, 41/41 query checks, 4/4 persistence checks and 40/40 approved regression comparisons passed with zero failures/skips. `git diff --check` passed for the application, checks and slice evidence. No new application changes were needed. The plan remains unchecked; this is not the final slice/browser gate.

## Latest validator follow-up (2026-10-15)

Task 2 remains unchecked. The supplied three findings are recorded verbatim with dispositions in `evidence/task-2-validator/findings.json`.

- **Implementation:** the reviewable changes include the existing application query/summary services and executable checks. Added defensive unavailable-patient result retrieval in `Kd03Recording.ReadResults` without changing recording semantics. Added checks for other-patient history isolation, unavailable patient context, filtering before counting/paging, and rejection of a mis-scoped summary repository response. The new unavailable-patient test initially failed; its failure is retained in `evidence/task-2-validator/current/`, and the fix passes in the final packet.
- **Stage separation:** all 12 `refactor-task-*` packets have moved, byte-for-byte, from Convert to `system-feel/refactor/evidence/`. `evidence/task-2-validator/relocation.json` maps historical paths to current paths and records every digest. Embedded historical logs are unchanged; task-1 evidence index manifests now resolve to the relocated files. No Convert implementation, approval, or bound Characterise input was edited.
- **Authoritative prerequisites:** `evidence/task-2-validator/final/input-identities.sha256` records all 1692 reviewed prestart identities. Adjacent `results.json` binds their digest, verified approval hash, review revision, original before/after prerequisite packets, and the observed **53/53** Convert parity result. `verify-task-2` verifies identity membership against the approved review manifest, approval hashes, relocated bytes, exact scenario membership, observations and current Convert parity-source digests. This is an authoritative **historical prestart** binding, not a newly granted approval. The old `refactor-task-2-final` packet is a failed post-change check; its missing identities reflect that failure. It remains intact and is superseded for prestart evidence by the explicitly scoped authoritative packet, not relabelled as passing.
- **Boundary resolution:** `check-prerequisites.py` now verifies the current approval, approved Characterise packet, legacy sources and immutable Convert baseline while treating `lmf/migrations/hcwp/refactor/` and `.assembly-lines/` as the authorized mutable boundaries defined by the iteration. The original snapshot and failed post-change evidence remain unchanged; no approval or Characterise inventory was regenerated or weakened.

Run from `lmf/migrations/hcwp` with a fresh destination:

```sh
system-feel/refactor/verify-task-2 --evidence-dir system-feel/refactor/evidence/task-2-validator/final
```

Current boundary-fix validation is retained in `evidence/task-2-boundary-fix-validation/`: **41/41 query checks, 4/4 persistence checks, 40/40 approved three-way regressions**, build success, zero failures/skips, and exit **0**. The prerequisite result verifies the current approval plus 570 immutable review entries and 418 immutable inventory entries. It writes only Refactor evidence and rejects empty/failed/skipped product checks. It is a task-specific verifier, not the later final slice/browser gate. No later task was started or marked done.

## Earlier validator findings and disposition

1. **Restore immutable iteration-001 parity baseline (P1).** Restored `refactor/evidence/parity/comparison.json`, the three `*-build.log` files and `refactor/parity-report.md` byte-for-byte from HEAD. Fresh execution is under `evidence/task-2/revision/`. The existing runner now accepts `--evidence-dir`; this execution did not overwrite baseline evidence.
2. **Uncharacterised extracted-code change (P1) — superseded by the validator correction above.** Earlier disposition (not current implementation or authorized scope): retained an explicit Refactor adaptation: `ResultEnteredDate` reads `DateTime?`, rather than unboxing a stored null as `DateTime`. This is an intentional correction, not legacy parity for absent dates. It preserves absence instead of manufacturing a date. Query checks exercise null-last recorded-date ordering within equal contact dates and the explicit `Not recorded` display fallback. This is a formatting-contract check, not a browser rendering claim. With the original getter temporarily restored, the named `absent recorded date query mapping and ordering` check fails (1 failure, exit 1, `revision/old-getter-negative.log`). With the adaptation restored, all 37 checks pass, including `stable ordering and null recorded dates` and `absent recorded date remains null and renders explicitly`. No Characterise/Convert extraction was changed.
3. **Missing reviewable query implementation/evidence (P1).** Include `Application/Kd03ResultsQuery.cs`, `Application/PatientSummary.cs`, `checks/QueryChecks.cs` and this evidence packet in the reviewable change. Results are 37/37 query, 4/4 persistence, 40/40 three-way approved regression comparisons, zero failures/skips. The negative control is intentionally failing and is not a passing suite.
4. **Omitted linked compile inputs (P1).** `revision/parity/comparison.json` includes both linked Convert files under `identity.implementationSha256.refactor.linked/…`. The runner hashes these before compilation and verifies them again afterwards. The files remain unchanged at their approved Convert paths; provenance is `system-feel/convert/port.md`. No immutable baseline hash inventory was rewritten.
5. **Input gate failure (P1).** The pre-implementation gate DID pass: `evidence/refactor-task-2-prestart/prerequisites.json`, `packet-verification.log`, `input-identities.sha256` and `parity.json` record approval/input verification and 53 exact passing Convert comparisons before product work. Paths here are relative to `system-feel/refactor/`. Approval revision is `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655`. Approval was not created or modified by this task. The later `input-gate-failure.json` is retained as evidence that the Characterise whole-tree snapshot cannot serve as a post-change Refactor gate. The Refactor-specific gate now preserves every immutable approved entry and exact immutable inventory membership while permitting only the application and assembly-line boundaries to change. No approval or bound inventory was regenerated.

## Implementation scope

The existing application recording boundary remains responsible for fresh-context retrieval and mapping. The query service scopes to selected patient and KD03, applies AND across categories and OR within categories, inclusive dates, five physical-assessment facets (not social/family fields), count-before-paging, deterministic contact/recorded/ID descending ordering, and patient-safe detail lookup. It defaults to 10 rows, permits 10/25/50, clamps pages to valid bounds, and returns page 1/range 0–0 for no results. Queries and returned DTO mutation do not modify persistence. Patient-summary formatting/age/alerts reuse the approved converted rules through a replaceable repository.

Filtering/paging is application-side over the existing EF InMemory retrieval adapter, not database-side paging. No performance or PostgreSQL claim. Query-only synthetic volume covers 24 selected-patient rows plus other-patient/unsupported-contact rows; the application demonstration fixture is still a later task. No routes, bilingual UI, shell or browser work is included. Summary demonstration repository/wiring remains later work.

## Reproduction

From `lmf/migrations/hcwp`:

```sh
dotnet build refactor/checks/Checks.csproj --no-incremental
dotnet run --project refactor/checks --no-build -- --queries refactor/src/demo-fixtures.json
dotnet run --project refactor/checks --no-build -- --persistence refactor/src/demo-fixtures.json
refactor/run-approved-scenarios --evidence-dir system-feel/refactor/evidence/task-2/revision/parity
```

Executed logs and per-check observations are in `evidence/task-2/revision/`. Parity evidence records SDK/runtime, source hashes, commands and full observations. `review-files.sha256` binds the task packet including the linked sources. Earlier evidence is historical, not the current candidate's result. Browser, accessibility and full final slice gates remain unexecuted. Task and plan remain unchecked; no later task was started.
