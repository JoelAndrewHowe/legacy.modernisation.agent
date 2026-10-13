# KD03 Characterise review handoff

## State: awaiting human approval

The named Characterise artifacts exist and the extracted-reference mechanical evidence passes. This handoff is **not human approval** and does not mark the external plan task done. Do not enter Convert or Refactor until the operator reviews and approves the exact current revision through the LMF approval workflow. No target implementation was created.

Evidence supports **parity with extracted legacy logic**, not parity with the original Windows/Oracle system and not full save-service parity.

## Exact review inputs and revision

Paths in this document are relative to `lmf/migrations/hcwp` unless labelled repository-root. Repository HEAD at this handoff: `f8e2475c64e7dac07d11e83b4df5c67459827749`. HEAD alone does not identify working-tree artifacts; `characterise/review-files.sha256` inventories exact review files and their content hashes, including this document, but excludes itself and disposable `bin/`, `obj/` and Python caches. It includes retained construction evidence as well as current full-suite evidence. It is a review inventory, not an approval token or a substitute for the LMF runner's calculated revision.

Repository-root source: `example-code/HCWP Core (pseudonymised) - single file.txt`, SHA-256 `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`. It contains 94 original-file banners and is explicitly not a buildable original application. Required inputs also include repository-root `lmf/docs/vision.md` and `lmf/iterations/001-characterise-and-migrate-hcwp.md`; their reading/hashes are recorded in `characterise/input-reading.md`.

Review the following exact artifacts (individual paths/hashes, including every extracted file, are in the inventory):

| Files | Review purpose |
| --- | --- |
| `characterise/behaviour.md` | Source-referenced fields, defaults, validation, warnings, saved/read-back values and preserved quirks. |
| `characterise/dependencies.md` | UI/delegate/validator/service/mapping/persistence boundaries and excluded infrastructure. |
| `characterise/gaps.md` | Q01–Q13 classifications, synthetic inputs, V01 and remaining limitations. |
| `characterise/migration-plan.md` | Proposed bounded KD03 slices and shared operation/observation contract. |
| `characterise/fixtures.json`, `characterise/scenarios.json` | Synthetic inputs, independent expected projections, all required KD03-001–040 IDs. |
| `characterise/reference/README.md`, `extraction-manifest.json`, `extract.py` | Extraction provenance and all 13 adaptation/double categories. |
| `characterise/reference/original/*.txt`, `legacy/*.cs` | Original normalized file bodies and retained/adapted executable C# logic, with original identities in the extraction manifest. |
| `characterise/reference/Reference.csproj`, `Program.cs`, `ScenarioAdapter.cs`, `Mapping.cs`, `Infrastructure.cs`, `Compatibility.cs`, `Resources.cs`, `.gitignore` | Build, input-only path driver, comparison runner, explicit mapping and dependency doubles. |
| `characterise/verify` | Reproducible complete-suite command. |
| `characterise/reference/evidence/results.json`, `full-suite.jsonl`, `build.log` | Current full-suite machine report, per-scenario observations and build diagnostics. |
| Other files under `characterise/reference/evidence/` | Historical filtered construction checks only; not the full-suite gate. |
| `characterise/input-reading.md`, `execution.md`, `review.md` | Reading, previous execution and this current handoff. |

Earlier documents contain task-time statements such as “review pending” or “harness not yet built”. Those describe earlier steps, not current missing artifacts; this handoff and current full-suite results identify the present state. Previous HEAD values in those notes are historical, not the current approval revision.

## Commands and observed results

Prerequisites: Linux bash and .NET SDK **10.0.401** (observed with `dotnet --version`). No Windows, Oracle, live service or NuGet package dependency is required. Python 3 supports JSON inspection and optional extraction regeneration; regeneration was not performed at this step.

From `lmf/migrations/hcwp`, reran:

```sh
characterise/verify > characterise/reference/evidence/full-suite.jsonl 2>&1
python3 -m json.tool characterise/fixtures.json > /dev/null
python3 -m json.tool characterise/scenarios.json > /dev/null
git diff --check -- characterise
```

All exited **0**. Reference build: **0 warnings, 0 errors**. Unfiltered `verify` report: **40 total, 40 passed, 0 failed, 0 skipped**, mode `verify`, null scenario selection. Every required ID has nonempty observations and no differences. A separate Python inspection checked ordered required-ID coverage, uniqueness, status/counts, and all 11 V01 inner/outer prompts, parent notifications and no-save snapshots. It passed. No reference rules, scenario expectations or fixtures were changed to achieve these results.

| File | SHA-256 |
| --- | --- |
| `characterise/fixtures.json` | `ece4997b76d12a9fa488974e76d02bc4c89ecad1779cee1d89715d1b24b4e6a3` |
| `characterise/scenarios.json` | `409f6d6d8615d0bc851810feed5343e10954750ac52a7d463301ffdd385bad3b` |
| `characterise/reference/evidence/results.json` | `7a507fabf93a11a11cf088ec0858a9e04c08386e89a6538321f131029b1f42cc` |

Check the reviewed inventory from this same directory with `sha256sum --check characterise/review-files.sha256`. Verification rebuilds and can change build diagnostics; regenerate/review the inventory if content changes. Passing this command checks identity, not approval.

## Validator findings

No new findings were supplied after the findings heading in this invocation. Previously recorded **V01** is addressed and rechecked: KD03-004–010, 011, 014–015 and 032 distinguish the actual inner `ValidationErrorsPrompt` from the retained parent's `ExamResultsErrorSavingPrompt` and assert `NonFatalErrorEncountered`, `KdpResultsTitle`, ordered errors and unchanged committed storage. All 11 passed. No additional repair was necessary; this is execution evidence, not validator approval.

## Limitations to accept or resolve before Convert

No required scenario is blocked or has an indeterminate expected outcome. Remaining limitations are non-blocking for this bounded Characterise scope, not claims that unknown original behaviour is correct:

- Windows control binding, event ordering, focus/visibility, modal rendering and exact missing resource prose are unverified. The adapter drives explicit documented paths; it does not simulate the original UI.
- WCF/message/change-tracking shells, fixed clock/IDs, missing-member substitutions, explicit scalar mappings, LINQ-to-objects queries and cloned entity persistence are adaptations. Read-back uses fresh committed storage/context, not echoed input. Original AutoMapper/EF6/Oracle behaviour, constraints, rounding, empty strings, collation, triggers, sequence rollback and concurrency remain unverified.
- Appointment status, recall processing and appointment prefill are excluded/no-op boundaries. Scheduled save/consent withdrawal, editing/deleting, unsupported contact effects, search, historical database migration, PostgreSQL/Azure and production security/deployment are excluded.
- Patient data, operational lookups, schedule rows, centile bands and BMI limits are synthetic and explicitly labelled. They are not clinical truth. The 6/8-week demonstration schedule is not a mandatory age rule inferred from KD03's name.
- Source contradictions/possible bugs Q01–Q13 are preserved. Field head validation uses exclusive 0–100 while save uses exclusive 0–1000; general/core/consent/decline-only values are omitted from the counted-results predicate. No gender-specific testes rejection or categorical save whitelist is invented. Schedule selection, range aggregation, null-list permissiveness, display/mapping oddities and zero-height event-order risk remain disclosed.
- Repeat evidence covers the agreed patient isolation, exact-code grouping, date ordering, earliest ties and idempotence. No unsupported-type parity or speculative mutation coverage is claimed.
- Comparisons use named expected projections. BMI notification copies are deduplicated by semantic identity; locks/platform formatting are excluded. Stored values, validation errors, warning/refusal outcomes and repeat flags are not normalized away.

## Pending operator decisions

1. Review the source-backed behaviour, all 40 scenarios, dependency exclusions and proposed slices beginning with KD03 recording.
2. Accept or explicitly change the preserved head-limit contradiction, counted-results omissions, physical-field applicability and other Q01–Q13 quirks. Default is preservation, not silent correction.
3. Review synthetic schedule/BMI/centile and operational lookup values and the KD03-only scope adapter; acknowledge that these do not establish clinical policy or legacy whitelist behaviour.
4. Accept the extracted-reference, mapping/persistence/UI limitations and excluded appointment/recall effects without describing them as full-system/save-service parity.
5. Record approval separately against the exact current LMF-calculated revision, or request a scoped correction. Changes to source, target description, behaviour or scenarios invalidate prior approval and require renewed review.

Only the operator can attest approval. While awaiting that decision, stop: no Convert/Refactor work, no approval creation and no expansion into speculative tests.
