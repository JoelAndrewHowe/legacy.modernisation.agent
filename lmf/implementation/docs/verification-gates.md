# Runner-owned verification gates

Acceptance examples 3, 6 and 7 are covered by the existing runner and HCWP verifiers, with downstream failure/recovery evidence added in `tests/test_cli.py`.

## Enforcement

`Lmf/Program.cs` invokes each stage's configured check itself, deletes its results file before invocation, requires a zero command exit, and reads explicit integer `passed`, `failed`, and `skipped` counts. A gate needs positive passes, zero failures and zero skips. Missing checks, empty artifacts, absent results and malformed counts fail closed. Agent-authored success counts are not sufficient. Refactor uses runner-invoked `verify.py` to perform build, configured whitespace checks, parity, fresh-context persistence checks and Chromium checks; Convert runs its own build and parity verifier.

The runner retains numbered attempts with requests, command descriptions, stdout/stderr, returned counts and failure diagnostics. Repair requests include the previous diagnostic. Failed stages remain failed after the bounded repair budget is exhausted. Resume skips accepted stages. The approved revision is checked after downstream verification; modifying reviewed inputs cannot produce an accepted downstream stage.

## Executable evidence

- `tests/test_cli.py`: nonempty/complete counts, missing/stale results, approval invalidation, bounded repairs and accepted-stage preservation. The downstream gate regression invokes synthetic build/style/parity commands through the actual CLI. It checks nonzero build/style exits, parity mismatch counts and scenario identification, stale agent-authored results, retained diagnostics passed to the next attempt, byte-for-byte preservation of earlier attempt evidence and recovery without rerunning Characterise or Convert. These commands are orchestration doubles, not HCWP build or parity evidence.
- `tests/test_hcwp_convert.py`: real generated assemblies and shared observations; mismatches, malformed observations, changed approved inputs and build failure invalidate success evidence; recovery passes.
- `tests/test_hcwp_refactor.py`: real generated final assembly, build/style checks, 371 matching shared scenarios, four fresh-context persistence checks and six Chromium checks. Deliberate calculation, persistence and browser failures reject the gate; restoring the implementation passes again. Changed approved scenarios reject verification.
- Retained HCWP migration evidence and launch instructions: `docs/hcwp-refactor.md`.

Validation performed for this task:

```sh
python3 -m unittest discover -s tests -p test_cli.py
# 8 tests passed
python3 -m unittest discover -s tests
# 13 tests passed (237.194 seconds)
git diff --check
# passed
```

No validator findings were supplied. No approved artifacts or reference expectations were changed. No production enforcement change was needed: the runner and stage verifiers already implement these gates. This evidence does not claim parity with the original Windows/Oracle application or PostgreSQL compatibility. Real-agent migration evidence remains owned by the next plan task, not supplied by these deterministic tests.
