# Refactor task 1 — prerequisite inspection

The first plan task remains unchecked. No validator findings were supplied after the user's findings heading (`validatorFindings: []`). No approval, approved input, application code or unrelated user change was modified. Working-tree status was inspected before work; existing factory, configuration, documentation and untracked changes were preserved.

## Executed gates

From `lmf/migrations/hcwp`:

```sh
python3 system-feel/convert/check-prerequisites.py --evidence-prefix refactor-task-1-prestart
python3 system-feel/convert/verify --evidence-prefix refactor-task-1-parity
```

Both exited 0. The existing Convert verifier performed a fresh nonincremental build and executed all exact approved scenarios: **53 required/executed/passed, zero failures/skips/errors**. Its complete comparison uses approval-bound extracted-reference observations, not an ambient reference binary or regenerated reference evidence. The ordering-contract scenario inspects the converted method; the remaining 52 execute the converted runtime. SDK: .NET 10.0.401.

Evidence under `system-feel/convert/evidence/`:

- `refactor-task-1-prestart/`: approval, packet verification and 1692 input identities.
- `refactor-task-1-parity/`: build, per-scenario observations, aggregate parity and command logs.
- `refactor-task-1-parity-runtime/` and `refactor-task-1-parity-final/`: runtime/post-comparison approval checks.

All destinations were new; no historical evidence was overwritten. These are new prerequisite evidence files produced by existing Convert tools, not changes to converted rule sources.

`system-feel/refactor/evidence/task-1/results.json` records an additional mechanical inspection: exact scenario membership/order, positive complete counts, every observation passing, current parity-source hashes, successful before/after approval/input checks, and byte-identical before/after identity manifests. `evidence-identities.sha256` binds all 17 generated gate artifacts. Working-tree status, Python version and successful `git diff --check` are adjacent. Exact nested commands, timestamps, build output, source identities and observed values remain in the underlying reports/logs.

## Approval and context

Current slice approval binds review-manifest revision `6a44e9fcd19299d0886b6ccb7e48457d04b89b5913326ce445dba58cb246c655` and review-document hash `b5d76bd805491ca02bf48b4d0b52490884d3717c8a25f634fa72517db7b1fa4b`. The immutable iteration-001 approval binds `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`. Both revisions and all bound bytes matched mechanically. Original inventory membership (1499 files, 184 directories, two symlinks) and 1690 slice-review entries passed the existing read-only packet gate; no capture/rebaseline was invoked.

Read the vision, both iteration seeds, original patient-summary service/mapping/name/address/age/status/school/alert rules, original KD03 retrieval and complete GetKdpResults ordering method, approved baseline behaviour/approval, slice behaviour/dependencies/review, Convert report/review/prerequisites, current recording application/presentation/Razor/persistence boundaries, checks driver, complete browser flow, existing verification/limitations and NHSW context/provenance. The gate opened and hashed all reviewed inputs; this is not a claim of exhaustive semantic review of every dependency or binary.

Historical Characterise prose saying awaiting approval describes the earlier packet creation, not the current separately authored human approval. Its decisions are authoritative: Health board wording requires separately documented Welsh-health-board demonstration fixtures; do not change approved reference fixtures. Invalid filters must surface the approved error summary and defaults. Language uses a browser-local preference. Equal-date recorded-date/ID ordering is an intentional Refactor enhancement, not a Convert rule.

## Handoff and limits

Prerequisites pass for validator/runner assessment; no later plan task was started or marked complete. Next work is application/query-service integration with executable tests, retaining the existing recording boundary and patient isolation. Components must not query storage directly. Preserve the NHSW asset pin `043d882318918e2a4e8847e16fc3bfe694973c08`; the newer guidance pin is not permission to upgrade it.

This task did not rerun the 40 application regression scenarios, browser/accessibility suite or final slice gate. Their approved inputs and retained evidence remain unchanged; they are required later. Claims remain parity with extracted legacy logic and disclosed synthetic/dependency adaptations, not original Windows/Oracle/EF6 execution. Missing clinical resource prose stays unresolved; draft Welsh needs professional review. EF InMemory/local-demo, unverified PostgreSQL/production and deferred load testing limitations remain. No human approval was authored or inferred from agent success.
