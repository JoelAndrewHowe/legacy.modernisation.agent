# Convert evidence report — task 4

Scope: isolated patient-summary and multi-result conversion only. No validator findings were supplied; none are inferred. This is doer-produced evidence, not independent approval, task completion or stage completion. All plan checkboxes are preserved. Refactor remains a separate run.

## Provenance and adaptations

The approved Characterise manifest revision is `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655`. The human approval, review document, manifest and all 1692 reviewed identities are retained in each prerequisite evidence directory. Gates verify current membership and hashes rather than trusting this revision string alone.

Conversion is separate modern .NET 10 source, not application integration. See `port.md` for the file-by-file origin table and `../characterise/reference/README.md` for every inherited extraction adaptation and original citation ID. The chain is original pseudonymised bundles → approval-bound extracted spans and C# reference → physically separate `src/*.cs`. `PatientSummaryAndResults.cs` retains name/address/age/school/organisation/alert/physical lookup and result retrieval rule bodies; `Compatibility.cs` retains the approved graph and doubles; `ObservationAdapter.cs` retains selected-patient mapping and observation construction. Namespace/comments and a prerequisite-gated entry point are the only additional changes. Retained three-file source-preservation evidence is revalidated against current source hashes, not overwritten.

Important inherited adaptations: controlled clock; LINQ-to-Objects graph/repositories instead of EF6/Oracle; explicit mapping instead of full AutoMapper/service execution; symbolic unavailable constants; resource identities and arguments instead of invented prose; excluded access dependency as a no-op; saved-row identity mapping. The explicit KD03 restriction follows the original all-KDP retrieval. Seed-authored examination/repeat/physical facets are observations, not a persisted aggregate clinical status. Original nulls, formatting separators, date arithmetic and single-row/lookup failures remain. Organisation is not relabelled Health board here.

No routes, NHSW shell, product filters, pagination, bilingual interaction or secondary date/ID ordering are introduced. Contact-date descending remains the sole source ordering contract. Matching retained fixture tie sequences does not turn equal-date ordering into a guaranteed rule.

## Reproduce and inspect

From `lmf/migrations/hcwp`:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/produce-report.py --evidence-prefix task-4-report
```

Use a fresh prefix for every rerun. The producer preflights all output directories and refuses reuse. It retains exact argv/cwd/exit codes, stdout/stderr, UTC times, tool versions, Release build output, source/binary hashes, isolated-test results, complete machine-readable per-scenario observations and aggregate parity. Failure yields nonzero; no missing prerequisite becomes a skip. It does not run the historical one-shot `check-port.py` or regenerate any approved reference evidence.

Evidence layout beneath `evidence/`:

- `task-4-report/report.json`: commands, isolated-test counts, parity counts, integrity result and evidence pointers.
- `task-4-report/artifact-identities.sha256`: reviewed converter source/docs/tools and retained task-4 evidence file identities. The report binds this manifest; it intentionally does not hash itself recursively. Build hashes identify the generated binary; compiler caches are excluded.
- `task-4-report-prestart/`, `task-4-report-final/`: read-only packet/approval gates and full input identity manifests. Exact before/after manifest equality plus the approved packet's full membership reconciliation demonstrates iteration-001 sources, approval, scenarios, conversion, Refactor inputs and retained evidence were not rebaselined or changed.
- `task-4-report-parity/`: nonincremental build, `parity.json`, `observations.json` and detailed command log.
- `task-4-report-parity-runtime/`, `task-4-report-parity-final/`: runtime and post-comparison approval/input gates.
- `task-4-report/{approval-tests,comparator-tests,working-tree-before,working-tree-after,diff-check}.log`: auxiliary executable checks and preservation of unrelated working-tree state.

The parity runner uses all 53 exact approved scenarios/fixtures. Fifty-two requests execute the converted runtime; the ordering-contract scenario inspects converted method keys. Each observation satisfies unchanged scenario expectations AND complete reference comparison (types, keys, row counts, values and order). Reference is manifest-bound `../characterise/task-6-final-reference-observations.json`, not an ambient DLL or a regenerated baseline. Empty, missing, failed or skipped evidence is rejected. Approval tests require 10 passes and comparator/contract tests require 11 passes in this revision; scenario parity requires 53/53 with zero failures/skips. See retained JSON for actual execution outcomes, timestamps and versions rather than interpreting this command description as a pass claim.

## Vision traceability

- Behaviour is the specification / tests before translation: approved extracted rules, exact scenarios and complete observation comparison.
- Translate first, improve second: physically separate conversion, unchanged bodies and deferred UI/query enhancements.
- Incremental and shippable: no application or iteration-001 modifications; integration is not claimed yet.
- Evidence over assertion: executable nonempty parity, identities and machine-readable gates.
- Humans decide: revision-bound approval checked before build, at runtime and after comparisons; no agent-created approval.
- Small replaceable stations: separate prerequisite/build/parity/report tools, no factory stage policy added to application code.

## Limitations and handoff

Evidence proves parity with approved extracted legacy logic and disclosed adapters, **not** original Windows/Oracle/EF6 execution or production clinical correctness. All fixtures are invented, including deliberately nonvalid SYN-NHS identifiers and the artificial 23-result history; they are immutable reference inputs, not typical clinical history or final presentation fixtures. Missing resource prose and numeric lookup identities remain unresolved; neither clinical translation nor resource text is invented.

This task does not execute the final application's 40 iteration-001 regression scenarios, browser/accessibility checks or persistence integration. Their inputs/evidence remain intact; Refactor must run them and the seed's new application gates. No PostgreSQL compatibility, production readiness, database concurrency, operational access control or load/performance assurance is claimed. Existing target remains EF InMemory and a local demonstration. Welsh is future draft product copy requiring professional review. Health-board fixture provenance and approved deterministic paging order belong to Refactor, not this conversion.

Next task: independently review Convert evidence and mechanical gates. Do not mark Convert complete from this producer's success alone; do not begin Refactor in this run.
