# LMF CLI foundation

Requires .NET 10 SDK. Run `./lmf help`, or publish `Lmf/Lmf.csproj` for a standalone command. Python 3 is required only for the smoke tests: `python3 tests/test_cli.py`.

This implements the orchestration foundation and a source-bound HCWP Characterise adapter, **not a completed HCWP migration**. Characterise now produces approval-ready extracted-reference evidence for the bounded KD03 workflow, including the agreed repeat-flag behaviour. Windows lifecycle, excluded infrastructure and unsupported-contact behaviour remain documented limitations. Target-stage mechanical parity, style/build/browser gates and real-agent evidence remain subsequent tasks. No parity with the original Windows/Oracle application is claimed; the baseline is extracted legacy logic. No real-agent migration or browser demonstration has been verified here.

## Commands

From this directory:

```sh
./lmf characterise --workspace workspaces/hcwp \
  --source '../../example-code/HCWP Core (pseudonymised) - single file.txt' \
  --target /absolute/path/to/target-description.md \
  --agent /absolute/path/to/agent.json --repairs 2
./lmf status --workspace workspaces/hcwp
./lmf approve --workspace workspaces/hcwp --revision SHA256_FROM_STATUS
./lmf resume --workspace workspaces/hcwp
```

Target is a text-file description, not an output directory. Each new migration gets a separate workspace; initialization never overwrites an existing state. Relative input paths resolve against the caller's directory. Agent and check executables run inside their stage directory, so use absolute script paths or executables on PATH.

Characterise runs verification and stops normally at `awaiting-approval` (exit 0). Approval is an explicit operator action and rejects blocking gaps and stale hashes. Resume without approval cannot generate a target. The hash binds source, target description, characterisation contract and every listed reviewed artifact, including scenarios and reference files. Changes cause re-characterisation and require new approval. Approval of the implementation seed is not approval of the generated behaviour specification.

Resume skips accepted stages, retries the failed stage, and retains attempts. Repairs are 0–10 additional attempts per invocation (default 2), not an unlimited automatic loop. Nonzero agent/check exits, missing/empty/failed/skipped verification and timeouts produce exit 1. Awaiting approval is a normal stop; complete execution reaches `completed`. State is atomically replaced in `state.json`; an exclusive `.lock` prevents simultaneous runners.

## Replaceable local agent contract

Agent configuration:

```json
{
  "command": {
    "executable": "/absolute/path/to/agent-wrapper",
    "arguments": ["--your-option"],
    "timeoutSeconds": 600
  }
}
```

The runner appends **one argument**, an absolute request JSON path. There is no shell expansion. A wrapper adapts this to any installed coding agent. The request includes stage (`characterise`, `convert`, `refactor`), workspace, output directory, source and target paths, approved revision and prior failure diagnostic. Read the source and target; generate artifacts inside the output directory. Do not change accepted artifacts or approved scenarios. Exit 0 means artifact generation succeeded, **not** that the gate passed.

Each stage writes `stage.json`, for example:

```json
{
  "reviewFiles": ["behaviour.md", "dependencies.md", "gaps.md", "fixtures.json", "migration-plan.md", "scenarios.json", "reference/Program.cs"],
  "blockingGaps": [],
  "checks": [
    {
      "command": {
        "executable": "/absolute/path/to/verification-wrapper",
        "arguments": [],
        "timeoutSeconds": 600
      },
      "results": "results.json"
    }
  ]
}
```

Characterise requires the six named documents and at least one `reference/` file. List **all** reviewed reference source, fixtures and scenario inputs: only listed files enter the review hash. Convert and Refactor need nonempty review artifacts and checks. Every listed artifact must be nonempty. Paths are relative to the stage directory and may not escape it.

The runner deletes each check's old result file, invokes the command itself, requires exit 0 and a newly generated result JSON `{"passed": 12, "failed": 0, "skipped": 0}`. Passed must be positive, failed/skipped must be zero. Test wrappers must faithfully aggregate actual execution, not write fabricated success. These initial count gates do not yet establish scenario identity or reference/target parity; that runner-owned comparison is a later plan task.

Artifacts remain under `characterise/`, `convert/`, `refactor/`. Every attempt has its own numbered `attempts/NNNN/` containing the request, exact command, stdout, stderr, copied check results and failure diagnostics. Revision changes do not reset evidence numbering. Stage commands and agents are trusted local programs with normal user permissions, not sandboxed plugins. Keep real patient data out of inputs and logs.

## Supplied HCWP Characterise adapter

`adapters/hcwp_characterise.py` is a deterministic source-extraction adapter, not a real coding-agent run. It accepts the same appended request JSON contract, reads the actual 94-file bundle and target description, and generates the reviewed documents, complete DTO inventory, original-file index, fixtures, shared scenarios and independently inspectable C# reference. It supports Characterise only; it explicitly fails Convert/Refactor rather than fabricate implementation evidence.

Create a target description containing `Blazor` and `in-memory` (for example, `Modern .NET server-interactive Blazor with EF Core in-memory persistence`) and an agent config using absolute paths:

```json
{"command":{"executable":"/usr/bin/python3","arguments":["/workspaces/legacy.modernisation.agent/lmf/implementation/adapters/hcwp_characterise.py"],"timeoutSeconds":600}}
```

Then use the Characterise command above. The runner executes the generated `verify.py`; it builds/runs extracted C#, compares actual observations against every scenario, and writes `results.json`, `observations.json` and `reference-report.json`. Read `behaviour.md`, `gaps.md`, `dependencies.md`, `migration-plan.md`, `fixtures.json` and `reference/ADAPTATIONS.md` before any approval. Unadapted sections for all 94 files remain under `reference/original/`; `source-index.json` gives banner lines and section hashes. All reference sources, original sections, scenario inputs and verification code are revision-bound review files.

The examples expose head circumference 100 rejected by field validation yet accepted by direct save, and PhysicalGeneral alone not counted as a result. Do not harmonise these findings. Warnings use symbolic resource identifiers because translated resources are absent. Saved observations are detached input clones, **not persistence read-back**. Synthetic patient/date/schedule values are explicitly invented. DaysBetween/WeeksBetween are recovered from the bundle's DateCalculation.cs, including truncation toward zero before division by seven; fractional-day and negative-interval examples verify those extracted bodies. Repeat-flag recalculation for the selected patient's KD03 results is included and covered by the existing extracted scenarios. Windows lifecycle and excluded infrastructure remain review limitations rather than approval blockers. This is inspectable extracted-reference evidence, not parity with the original Windows/Oracle application.

To rerun extracted verification independently, run `python3 WORKSPACE/characterise/verify.py`. Prerequisites are Python 3 and .NET 10; no NuGet test framework or Oracle installation is required. `scenarios.feature` is the readable BDD companion; `scenarios.json` is the executable Given/When/Then suite interpreted by the reference adapter (not a Cucumber feature runner).

## Tests

`python3 tests/test_hcwp_characterise.py` runs the supplied bundle through actual extraction/build/verification, checks the documented discrepancies and approval readiness, and introduces an expected-observation mismatch to ensure comparison fails.

`python3 tests/test_cli.py` builds the CLI and executes subprocess-based deterministic agent doubles in temporary workspaces. Coverage includes approval stops, revision invalidation, blocking gaps, empty/skipped/failed/missing/stale verification, bounded repairs, retained diagnostics, workspace isolation and recovery without redoing accepted stages. These synthetic fixtures demonstrate orchestration only and do not represent HCWP behaviour.
