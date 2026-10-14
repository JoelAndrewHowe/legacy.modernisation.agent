# Task 3: executable parity

No validator findings were supplied. No task checkbox was changed.

From `lmf/migrations/hcwp`:

```sh
PYTHONDONTWRITEBYTECODE=1 system-feel/convert/verify --evidence-prefix <fresh-prefix>
PYTHONDONTWRITEBYTECODE=1 python3 system-feel/convert/test-parity.py
```

The entry point gates current revision-bound approval before building, at converted runtime entry, and after comparison. Evidence prefixes are exclusive-create; reuse exits nonzero. A nonincremental Release build executes the converted DLL with only resolved approved inputs; expectations never enter its request stream. The approved Characterise helper supplies contract validation, fixture resolution and the unchanged scenario expectation comparator. No fixture, scenario, reference or approval file is rewritten.

Every scenario also compares the **complete** converted observation against its manifest-bound approved `task-6-final-reference-observations.json` observation, including all keys, scalar types, rows and ordering. This is stronger than the scenario subset comparison. Equal-date fixture observations match the retained reference sequence but this does **not** define a new semantic tie-break: the approved ordered-date-group expectation still allows unspecified equal-date order. No deterministic secondary ordering is introduced.

The ordering-contract observation inspects the complete converted `GetKdpResults` method. Its `sourceArtifact` fields identify original port provenance (`reference/original/C022.txt`); the inspected converted source hash is separately retained in `parity.json`. The runtime handles the other 52 requests. Missing/extra observations, errors, incomplete contracts and nonpassing reference entries fail the gate. Completion requires exactly 53 executed scenarios, positive passes, zero failures and zero skips.

## Retained evidence

- `evidence/task-3-prestart/`: pre-work approval and identity check.
- `evidence/task-3-parity/`: build log/identities, commands/tool version, `parity.json`, `observations.json`, `parity.log`, comparator tests and collision rejection.
- `evidence/task-3-parity-runtime/` and `task-3-parity-final/`: runtime and final approval/input gates.

Execution passed 53/53 approved scenarios, zero failures/skips. Eleven isolated checks passed, zero failures/skips, exercising exact matching and rejection of changed fields, missing/extra keys/rows, changed order, bool/int confusion and incomplete/non-required scenarios; converted ordering inspection also passed. Retained-prefix reuse was rejected with exit 2. `git diff --check -- system-feel/convert` passed.

The reference is the approved retained executable evidence, not a fresh reference rerun. This avoids changing its approval-bound evidence or build outputs. Claims remain extracted legacy rules with dependency doubles and synthetic fixtures, not original Windows/Oracle parity, application integration or Refactor completion. Iteration-001 input integrity is checked by the prerequisite packet verifier. Broader conversion provenance/stage review belongs to subsequent tasks.
