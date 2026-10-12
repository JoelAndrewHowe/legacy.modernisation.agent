# HCWP reference verification and approval checkpoint

Acceptance examples 1–2 of iteration 001 were exercised with the supplied 94-section bundle and the deterministic `adapters/hcwp_characterise.py` extraction adapter. This is **not a real coding-agent migration** or parity with Windows/Oracle.

## Retained local run

Workspace: `workspaces/hcwp/migration` (ignored local evidence, not committed).
Target description/config: `workspaces/hcwp/target.md`, `workspaces/hcwp/agent.json`.

The runner invoked the generated reference verifier, which reported **371 passed, 0 failed, 0 skipped**. Characterise was accepted and stopped at `awaiting-approval`. An unapproved `resume` stayed at that gate; neither Convert nor Refactor was generated. No human approval was given.

Reviewed revision:

```text
6515ffc7f2a4f89ff8efc5bbb0887b5031ebf9cc02f6191de3c225cc49984ad2
```

Evidence under the workspace:

- `state.json`: at the initial checkpoint, awaiting approval with null approved revision (see current recheck below).
- `characterise/attempts/0001/`: agent/check commands, logs and runner-copied results.
- `characterise/reference-report.json`: per-scenario comparison outcomes.
- `characterise/behaviour.md`, `dependencies.md`, `gaps.md`, `fixtures.json`, `migration-plan.md`, `scenarios.json`, `reference/ADAPTATIONS.md`: human review inputs.

Review those artifacts and exclusions before explicitly approving the current revision. Run `./lmf status --workspace workspaces/hcwp/migration` to check freshness. Source, target, contract or reviewed artifact changes require re-characterisation and new approval. Do not treat the seed's scope agreement or passing tests as approval.

The supplied adapter supports only Characterise. After approval, Convert/Refactor still need a target-capable agent; they are not implemented by this checkpoint. Persistence read-back, browser behaviour, original Windows event delivery and real-agent migration remain unverified.

## Automated evidence

`tests/test_hcwp_approval.py` executes actual extraction through the CLI, checks runner-retained counts against shared scenarios and matching reference observations, tests unapproved/stale approval stops, and uses an isolated simulated operator approval to prove reviewed-behaviour changes invalidate approval before target generation. Regeneration retains previous attempt evidence and requires a fresh approval even if deterministic artifacts restore the same revision.

Existing `tests/test_cli.py` covers source, target, behaviour, scenario and reference changes plus blocking gaps and failed verification with deterministic orchestration doubles.

Validation: `python3 -m unittest discover -s tests` passed all 10 tests. No validator findings were supplied for this task.

## Current checkpoint recheck

A subsequent doer recheck found the retained workspace in `approved` state, with `ApprovedRevision` and `CurrentRevision` both matching the revision above. This differs from the initial awaiting-approval snapshot; this recheck did not issue approval and does not establish who approved it. Only Characterise is accepted, with one attempt; no Convert or Refactor artifacts exist. No resume or target generation was attempted. The next task remains planner-owned.

The full automated suite passed again (10 tests), and `git diff --check` passed. No validator findings were supplied.
