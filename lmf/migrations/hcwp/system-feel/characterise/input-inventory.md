# Iteration-002 verified input inventory

Task 1 only. No plan checkbox, approval, baseline artifact or product code changed.
No validator findings were supplied after the findings heading.

## Inspection scope and constraints

All file bytes were opened and individually hashed; all directory members (including hidden, ignored, untracked, binaries, node_modules, bin/obj and caches) are included without exclusions. This is an input identity/availability inspection, not a claim of exhaustive semantic review of every dependency file. Behaviour extraction and scenario execution remain downstream tasks.
Read the vision, both seeds, baseline approval/review, source patient-service/resolver/model sections, KD03 GetKdpResults, target application boundary, test driver/browser flow, design context/provenance, Convert parity and Refactor parity/verification/completion reports. The entire Characterise/Convert/Refactor trees supplement these inspected entry points.
Existing user modifications and untracked inputs were observed with `git status --short` from repository root and preserved. Configuration is a working-tree input, not assumed to match HEAD.

## Nine-of-nine reconciliation

### 1. Immutable factory vision; trace all future stages to its principles.
- `lmf/docs/vision.md` — SHA-256 `a5280da556de24f8d6d9254df5b1bdd22ace59c7fc0a5ac64b9485dd71483444`.

### 2. Current contract; Characterise only, then human approval.
- `lmf/iterations/002-implement-system-feel.md` — SHA-256 `34408ee46bc427ec17654f934aa35c177e78d2ad5e4dc2d485545a00d6a72c75`.

### 3. Immutable bounded KD03 baseline contract.
- `lmf/iterations/001-characterise-and-migrate-hcwp.md` — SHA-256 `73c53da335f85625dd0ce180d69eec64a21431f9ab8247a58520e0dfbd3addcd`.

### 4. Input-only patient retrieval, mappings, resolvers and banner source.
- `example-code/patient-banner (pseudononymised).txt` — SHA-256 `d0365ffb8b625eeb8085bf7cb23284837525caf61126a90756b9d8e330b51713`.

### 5. Input-only KD03 legacy bundle; original file identities, not a buildable system.
- `example-code/HCWP Core (pseudonymised) - single file.txt` — SHA-256 `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`.

### 6. Immutable approved packet, 40 scenarios, extracted reference and revision-bound human approval.
- `lmf/migrations/hcwp/characterise/` — 147 recursively enumerated files; every individual path/hash is in `input-files.sha256`, full directory membership in `input-membership.json`.
- `lmf/migrations/hcwp/approvals/characterise-approved.md` — SHA-256 `1dc949df7d3663db3ea9f93fbf0c07be95c2908b3480dc575cfcaff989145731`.

### 7. Existing target, regression and browser boundaries; do not modify or execute evidence-writing baseline runners.
- `lmf/migrations/hcwp/refactor/src/` — 541 recursively enumerated files; every individual path/hash is in `input-files.sha256`, full directory membership in `input-membership.json`.
- `lmf/migrations/hcwp/refactor/checks/` — 43 recursively enumerated files; every individual path/hash is in `input-files.sha256`, full directory membership in `input-membership.json`.
- `lmf/migrations/hcwp/refactor/browser/` — 184 recursively enumerated files; every individual path/hash is in `input-files.sha256`, full directory membership in `input-membership.json`.
- `lmf/migrations/hcwp/refactor/limitations-and-completion.md` — SHA-256 `bf5b9b72aab3464bb467f3b1b0fce3f6844f258e9e2fee9802d0c617bc5a18e0`.

### 8. Target-design guidance, NOT legacy behavioural evidence; does not authorise asset upgrades.
- `lmf/seeds/context/nhsw-component-library.md` — SHA-256 `307e3c750c6673b68ac3d00cf9b3b600a3791120a4787ff737164acd8b9b5680`.

### 9. Existing pinned design assets/provenance; preserve current pin.
- `lmf/migrations/hcwp/refactor/nhsw-provenance.md` — SHA-256 `da50c11db3881005c916e344ff678112ec728c88fda155c248d4594a40d81969`.

## Supplemental inputs

- `lmf/migrations/hcwp/.assembly-lines/`: 22 files, individually bound. Overlapping group-7 paths are deduplicated, not omitted.
- `lmf/migrations/hcwp/convert/`: 225 files, individually bound. Overlapping group-7 paths are deduplicated, not omitted.
- `lmf/migrations/hcwp/refactor/`: 1098 files, individually bound. Overlapping group-7 paths are deduplicated, not omitted.

### Exact linked baseline evidence paths

- `lmf/migrations/hcwp/refactor/parity-report.md`
- `lmf/migrations/hcwp/refactor/verification.md`
- `lmf/migrations/hcwp/refactor/full-flow.md`
- `lmf/migrations/hcwp/refactor/evidence/gate-results.json`
- `lmf/migrations/hcwp/refactor/evidence/completion-assessment.json`
- `lmf/migrations/hcwp/refactor/evidence/gate-prerequisites-before.log`
- `lmf/migrations/hcwp/refactor/evidence/gate-prerequisites-after.log`
- `lmf/migrations/hcwp/refactor/evidence/full-flow-build.log`
- `lmf/migrations/hcwp/refactor/evidence/gate-style.log`
- `lmf/migrations/hcwp/refactor/evidence/full-flow-model.json`
- `lmf/migrations/hcwp/refactor/evidence/full-flow-persistence.json`
- `lmf/migrations/hcwp/refactor/evidence/full-flow-browser/results.json`
- `lmf/migrations/hcwp/refactor/evidence/parity/comparison.json`
- `lmf/migrations/hcwp/refactor/evidence/parity/reference/results.json`
- `lmf/migrations/hcwp/refactor/evidence/parity/conversion/results.json`
- `lmf/migrations/hcwp/refactor/evidence/parity/refactor/results.json`
- `lmf/migrations/hcwp/refactor/evidence/nhsw-browser/results.json`
- `lmf/migrations/hcwp/convert/parity-report.md`
- `lmf/migrations/hcwp/convert/baseline-confirmation.md`
- `lmf/migrations/hcwp/convert/source-provenance.json`
- `lmf/migrations/hcwp/convert/evidence/scenario-comparison.json`
- `lmf/migrations/hcwp/convert/evidence/results.json`
- `lmf/migrations/hcwp/convert/evidence/reference-results.json`
- `lmf/migrations/hcwp/characterise/reference/evidence/results.json`

All remaining report, log, screenshot, HTML, script, configuration and disposable-tree members are also listed individually in the manifest; no directory hash substitutes for them.

## Symlink handling

Enumeration uses sorted `Path.iterdir()` recursively, resolves each entry strictly, opens each regular file in binary mode and streams SHA-256. It follows directory links with cycle detection and hashes file links through their targets. Unresolved, unreadable or unsupported entries fail. Directory membership and link targets/resolution are retained in `input-membership.json`.
- `lmf/migrations/hcwp/refactor/browser/node_modules/.bin/playwright` → `../playwright/cli.js`; resolves to `/workspaces/legacy.modernisation.agent/lmf/migrations/hcwp/refactor/browser/node_modules/playwright/cli.js`; bytes hashed under the input path.
- `lmf/migrations/hcwp/refactor/browser/node_modules/.bin/playwright-core` → `../playwright-core/cli.js`; resolves to `/workspaces/legacy.modernisation.agent/lmf/migrations/hcwp/refactor/browser/node_modules/playwright-core/cli.js`; bytes hashed under the input path.

## Unavailable dependencies and limitations

- The original Windows/Oracle/EF6 application, runtime UI/event delivery, service infrastructure and original resource prose are not available as a runnable baseline. The supplied bundles remain mandatory inputs, not omitted dependencies.
- Patient summary needs repository/unit-of-work, AutoMapper/resolvers, lookups, resource formatting, clock, access-control and related location/alert data. Exact extraction adaptations and doubles require downstream documentation; no rule is inferred from the modern UI.
- Existing target uses temporary EF Core InMemory; no Oracle, PostgreSQL, production or full-system parity claim. This task does not rerun build/browser suites or alter their retained evidence.
- NHSW context guidance pin `5322c16910fbad0335b504ce80a1d8a50fe3b683` differs intentionally from current asset provenance pin `043d882318918e2a4e8847e16fc3bfe694973c08`; guidance explicitly forbids silent asset replacement. Remote upstream/network availability was not verified and is not required for this local input gate.
- Synthetic fixtures and resource-identity fallbacks remain baseline limitations. Future Welsh copy and Organisation/Health board decisions are not resolved by the inventory.

## Exact enumeration/hash and gate commands

Working directory for capture and recheck: `/workspaces/legacy.modernisation.agent`.
```sh
python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py --capture
python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py
sha256sum --check lmf/migrations/hcwp/system-feel/characterise/input-files.sha256
# Independent approval checks, working directory lmf/migrations/hcwp:
sha256sum characterise/review-files.sha256
sha256sum --check characterise/review-files.sha256
```
The script is the exact enumeration/hash implementation (Python hashlib.sha256 on binary streams). Default mode never refreshes manifests. Reconciliation compares the full file set and directories, link metadata, every digest and exact manifest text; re-enumeration must also match. It checks approval state/revision independently before checking bound baseline bytes. No baseline verifier that rewrites evidence is invoked.

### Executed initial gate

Start: `2026-10-14T18:02:01.604512+00:00`; finish: `2026-10-14T18:02:12.877586+00:00`.
Counts: 9/9 seed groups; 1499 unique file entries; 184 directory entries; 2 symlinks. No missing or extra manifest paths. All required and supplemental paths readable.
Membership, recomputed digests, exact manifest reconciliation, second enumeration and approval revision comparison: PASS.
Approval recorded and calculated revision: `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699` (matches: True).
- `sha256sum --check lmf/migrations/hcwp/system-feel/characterise/input-files.sha256`, cwd `/workspaces/legacy.modernisation.agent`, 2026-10-14T18:02:12.667002+00:00–2026-10-14T18:02:12.870290+00:00, exit 0; full output `input-hash-check.log`.
- `sha256sum characterise/review-files.sha256`, cwd `/workspaces/legacy.modernisation.agent/lmf/migrations/hcwp`, 2026-10-14T18:02:12.870705+00:00–2026-10-14T18:02:12.873336+00:00, exit 0; full output `baseline-revision-check.log`.
- `sha256sum --check characterise/review-files.sha256`, cwd `/workspaces/legacy.modernisation.agent/lmf/migrations/hcwp`, 2026-10-14T18:02:12.873358+00:00–2026-10-14T18:02:12.877568+00:00, exit 0; full output `baseline-hash-check.log`.

### Executed independent repeat

`python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py` exited 0 from repository root at 2026-10-14T18:02:12.926680+00:00–2026-10-14T18:02:14.336597+00:00. Membership and every recomputed digest matched; exact manifest reconciliation and second enumeration passed. All three SHA-256 commands exited 0 again, and immutable approval revision matched. Capture also exited 0. Input-manifest SHA-256: `3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a`.

Python syntax inspection (`ast.parse`) and repository-root `git diff --check` exited 0. No blockers were found; no dependent task was started. Task 1 remains unchecked for runner/validator assessment.

Latest repeat results/timestamps/exit codes are retained in `input-gate-results.json` and the three logs. Recheck before downstream work and again before review binding. Any missing path, changed membership, unreadable input, digest or approval mismatch blocks progression; record it in gaps.md and the run plan, without refreshing iteration-001 evidence.
