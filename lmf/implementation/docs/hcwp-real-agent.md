# Orchestration and real-agent checkpoint

## Deterministic evidence

The full existing suite passed: 13 tests, 263.038 seconds. Retained output is
`docs/evidence/real-agent-characterise/orchestration-tests.txt`. After adding the
wrapper tests, the full suite passed all 15 tests (240.464 seconds); output is
`docs/evidence/real-agent-characterise/final-tests.txt`. `git diff --check` passed.
`tests/test_cli.py` exercises approval invalidation, failed/skipped/missing/stale
verification, bounded agent repairs, retained diagnostics and recovery without
rerunning accepted stages. Convert/Refactor regressions exercise actual generated
assemblies, deliberate observation mismatches, failed verification and recovery.
The Refactor regression also executes fresh-context persistence and Chromium
add/read-back, reload, invalid-input and confirmation checks. These are
**deterministic adapter-generated demonstrations**, not real-agent browser evidence.

## Actual local-agent execution

Prerequisites checked: Pi 1.0.4, .NET SDK 10.0.401, Python 3; local
`pi auth check --provider openai-codex --json` returned `ready` (OAuth).
A tool-free request to `openai-codex/gpt-6.1-sol` returned `LMF_AGENT_READY`.
No credentials were printed or copied into evidence.

Added `adapters/pi_agent.py`, which adapts the runner's appended request path to
non-interactive Pi. It disables project context, extensions, skills and MCP,
uses read/bash/edit/write, inherits stdout/stderr for runner retention, and
propagates Pi's exit code. It never manufactures stage results or grants approval.
LMF owns verification and the configured 600-second process timeout. The agent
is still a trusted local program, not a filesystem sandbox.

Reproduce from `lmf/implementation/` in a **new** workspace:

```sh
mkdir -p workspaces/hcwp-real-agent
cp workspaces/hcwp/target.md workspaces/hcwp-real-agent/target.md
python3 - <<'PY'
import json
from pathlib import Path
Path('workspaces/hcwp-real-agent/agent.json').write_text(json.dumps({
    'command': {'executable': '/usr/bin/python3',
                'arguments': [str(Path('adapters/pi_agent.py').resolve())],
                'timeoutSeconds': 600}}, indent=2))
PY
export LMF_PI_PROVIDER=openai-codex LMF_PI_MODEL=gpt-6.1-sol
./lmf characterise --workspace workspaces/hcwp-real-agent/migration \
  --source '../../example-code/HCWP Core (pseudonymised) - single file.txt' \
  --target workspaces/hcwp-real-agent/target.md \
  --agent workspaces/hcwp-real-agent/agent.json --repairs 0
```

Provider/model are configurable; omit both to use Pi's configured default.
`LMF_PI_EXECUTABLE` can select another Pi executable. Provider requires model.
`tests/test_pi_agent.py` checks argument forwarding (including paths with spaces),
working directory, isolation flags, stdout/stderr/exit propagation and rejection
of invalid configuration using a fake executable, not a provider request.

The actual run completed Characterise on its first attempt. The runner executed
`verify.py`: **371 passed, 0 failed, 0 skipped**. State is `awaiting-approval`,
with no approved revision and no Convert or Refactor directories. An unapproved
`resume` returned the same awaiting-approval message and generated no target.

Current review revision:

```text
ffa9d6f246f635f224277786c64e6b1591e4770ed8c34ea73f1131d3728c12be
```

The real agent reused the explicitly permitted source-bound extraction adapter;
this is **agent-assisted adapter execution**, not independently authored migration
logic. Its generation notes disclose source/document inspection, a Python-command
retry, and two document/report-label corrections. It did not modify scenario
expectations or reference business logic. Those generated changes produce a new
review revision; the existing migration's approval does not approve this one.

Full workspace evidence: `workspaces/hcwp-real-agent/migration/characterise/`,
including reviewed artifacts, original sections, observations, reference report
and `attempts/0001/`. Small durable snapshots of commands, agent final output,
generation notes, runner verification counts and state are retained under
`docs/evidence/real-agent-characterise/`. Print-mode output records the agent's
final account, not a complete tool-event transcript; inspect generated files
and runner-owned results rather than treating that account as verification.

## Human-owned stop

**Real-agent Convert, Refactor and browser demonstration remain unverified.**
Local agent credentials and browser prerequisites were available; the remaining
blocker is revision-bound human review, not a missing prerequisite. Do not
substitute the deterministic browser demonstration for a real-agent completion.
No approval was granted by this change. The previously completed approved
migration and its retained attempts were left untouched.

The operator must review `behaviour.md`, `dependencies.md`, `gaps.md`,
`migration-plan.md`, fixtures, scenarios, reference adaptations and the agent's
changes in the new workspace. Only after that review, the operator can run:

```sh
./lmf status --workspace workspaces/hcwp-real-agent/migration
./lmf approve --workspace workspaces/hcwp-real-agent/migration --revision REVIEWED_CURRENT_HASH
LMF_PI_PROVIDER=openai-codex LMF_PI_MODEL=gpt-6.1-sol \
  ./lmf resume --workspace workspaces/hcwp-real-agent/migration
```

Downstream runner gates must pass before claiming real-agent target/browser
completion. The baseline remains **parity with extracted legacy logic**; Windows/
Oracle application parity, production lookups, PostgreSQL, appointment/recall
processing and production security remain excluded or unverified. EF in-memory
storage is temporary and may reset on restart.
