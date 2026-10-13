# Current approved baseline confirmation

Performed the next unfinished task: confirm executable Convert parity against the current operator-approved Characterise baseline. The external plan remains unchanged and its final checkbox remains unchecked. This records mechanical evidence, not validator approval or an agent-owned completion decision.

## Verification

From `lmf/migrations/hcwp`:

```sh
convert/run-approved-scenarios
git diff --check -- convert
```

Both exited **0**. SDK: **10.0.401**; repository HEAD: `71d72cf14d3ca056783024f25659ecbb85a5d4fd`.

- Reference: **40 passed, 0 failed, 0 skipped**.
- Conversion: **40 passed, 0 failed, 0 skipped**.
- All required KD03-001–040 ran with identical approved inputs/expectations; no omitted IDs.
- **40 exact full-observation matches**, and **40 matches to the approved baseline**.
- Both builds: **0 warnings, 0 errors**.
- Current approval revision: `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`. Pre-execution approval/input/provenance checks and post-execution reviewed-inventory checks passed. No approved input, reference or approval was changed.

The reference was executed from a byte-identical disposable copy inside `convert/.reference-run/`; the independently compiled conversion does not delegate to reference code. Fresh per-scenario evidence is retained under `convert/evidence/`.

| Evidence | SHA-256 |
| --- | --- |
| `evidence/scenario-comparison.json` | `d2a276f2bf5bb87dec07ae9e0aa1a755a881f9fc005a350062aa3fcaa83e17a2` |
| `evidence/results.json` and `evidence/reference-results.json` (each; also matches approved results) | `7a507fabf93a11a11cf088ec0858a9e04c08386e89a6538321f131029b1f42cc` |
| `evidence/full-suite.jsonl` and `evidence/reference-full-suite.jsonl` (each) | `62df3e65384fcec406458037b81934ad97f483e6497f89bda8c7dfca53c09666` |

## Validator findings

No findings were supplied after the user's findings heading. Historical **V01** was rechecked on both fresh executions for KD03-004–011, KD03-014–015 and KD03-032: distinct inner/outer prompts, actual parent notification, no-save and unchanged committed storage all passed, with ordered errors matching the approved expectations. No repair or expectation change was necessary.

## Boundary

The executable evidence matches the current approved baseline. This establishes **parity with extracted legacy logic** only. All normalisation, synthetic-fixture, UI, mapping/persistence-double and excluded-infrastructure limitations in `parity-report.md` and `PORT.md` remain unchanged. No Refactor work was performed. Completion remains for the external validator/runner to decide; the plan was not marked done.
