# HCWP slice 01 — Characterise

Run the Characterise stage for the bounded Healthy Child Wales Programme
6–8-week contact (`KD03`) add-and-read-back workflow.

Read these inputs before planning or changing anything:

- `lmf/docs/vision.md`
- `lmf/iterations/001-characterise-and-migrate-hcwp.md`
- `example-code/HCWP Core (pseudonymised) - single file.txt`

Work only in this target's `characterise/` directory. Do not create Convert or
Refactor implementation code.

Produce:

- `characterise/behaviour.md`: observable behaviour with original source-file
  references, including success, validation, warnings and saved/read-back data.
- `characterise/dependencies.md`: UI, delegate, validator, service, mapping,
  persistence and excluded infrastructure dependencies.
- `characterise/gaps.md`: contradictions, unavailable dependencies, synthetic
  fixtures, adaptations and explicit limitations.
- `characterise/migration-plan.md`: small deliverable slices, beginning with the
  agreed KD03 recording workflow.
- `characterise/fixtures.json` and `characterise/scenarios.json`: shared inputs
  and expected observable outcomes with stable scenario identifiers.
- `characterise/reference/`: an independently inspectable executable reference
  harness retaining extracted legacy business logic as far as practical.
- `characterise/verify` or an equivalent documented command that executes every
  required scenario against the reference and emits per-scenario observations
  plus a machine-readable result with positive passes, zero failures and zero
  skips.
- `characterise/review.md`: the exact files, commands, results, source revision,
  limitations and human decisions that must be reviewed before Convert.

The supplied source bundle is not a buildable original application. Evidence
must say parity with extracted legacy logic, never parity with the original
Windows/Oracle system. Preserve legacy quirks by default and flag possible bugs
for human review. Do not silently harmonise contradictory rules. Use synthetic
patient data only.

Characterise is complete when the required artifacts exist, the shared scenarios
pass against the reference harness, and every remaining limitation is accurately
classified. Unknown behaviour blocks only when a required scenario cannot run or
its expected observable outcome is indeterminate. Do not expand accepted areas
with speculative mutation tests.

Do not create or claim human approval. The operator will review the completed
artifacts and record approval separately before starting Convert.
