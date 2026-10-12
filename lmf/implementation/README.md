# Legacy Modernisation Factory (LMF)

LMF characterises the supplied HCWP bundle, stops for revision-bound human approval, then converts and refactors the scoped KD03 add/read-back workflow. The retained deterministic adapter migration is completed, including Blazor, fresh-context EF Core read-back and Chromium verification. A separate real-agent Characterise run passed verification but is awaiting human approval; its Convert/Refactor/browser completion remains **unverified**. The baseline is **parity with extracted legacy logic**, not the original Windows/Oracle application.

## Prerequisites

Run commands below from `lmf/implementation/` on Linux/the development container:

- .NET 10 SDK (see `global.json`); `./lmf` builds/runs the CLI. Alternatively publish `Lmf/Lmf.csproj`.
- Python 3 for the supplied stage adapters, verification wrappers and tests, not just smoke tests.
- NuGet access to restore Microsoft.EntityFrameworkCore.InMemory 10.0.0 for Refactor.
- Python Playwright and Chromium, including browser system libraries, for the Refactor browser gate:

  ```sh
  python3 -m pip install playwright
  python3 -m playwright install --with-deps chromium
  ```

- For real-agent execution only: locally installed Pi, a configured provider/model and valid credentials. See [real-agent configuration and checkpoint](docs/hcwp-real-agent.md). Deterministic extraction does not need provider credentials.

Missing build/restore/browser prerequisites fail verification; they are not replaced by mocked success. Agents and checks are trusted local executables. Use only synthetic data, and bind the demonstration server to loopback.

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

The runner deletes each check's old result file, invokes the command itself, requires exit 0 and a newly generated result JSON `{"passed": 12, "failed": 0, "skipped": 0}`. Passed must be positive, failed/skipped must be zero. Test wrappers must faithfully aggregate actual execution, not write fabricated success. Counts alone do not establish parity. The supplied runner-invoked HCWP verifiers additionally enforce ordered scenario identities and full expected/reference/target observation equality; Convert and Refactor emit scenario-level parity reports. See [verification gate evidence](docs/verification-gates.md).

Artifacts remain under `characterise/`, `convert/`, `refactor/`. Every attempt has its own numbered `attempts/NNNN/` containing the request, exact command, stdout, stderr, copied check results and failure diagnostics. Revision changes do not reset evidence numbering. Stage commands and agents are trusted local programs with normal user permissions, not sandboxed plugins. Keep real patient data out of inputs and logs.

## Supplied HCWP Characterise adapter

`adapters/hcwp_characterise.py` is a deterministic source-extraction adapter, not a real coding-agent run. It accepts the same appended request JSON contract, reads the actual 94-file bundle and target description, and generates the reviewed documents, complete DTO inventory, original-file index, fixtures, shared scenarios and independently inspectable C# reference. It dispatches Convert to `adapters/hcwp_convert.py` and Refactor to `adapters/hcwp_refactor.py`. Convert retains approved extracted source and dependency substitutions in a separate assembly (no reference assembly dependency), with a source/hash manifest and `PORT.md`. Its runner-executed `verify.py` builds/runs both assemblies using the approved scenarios/fixtures, requires ordered scenario identities and full observation equality with approved expectations, and emits `parity-report.json`. This is a runtime port, not persistence or browser evidence.

For a reproducible deterministic run, create inputs and configuration with absolute script paths (choose a new migration directory rather than overwriting retained evidence):

```sh
mkdir -p workspaces/hcwp-demo
python3 - <<'PY'
import json
import sys
from pathlib import Path
root = Path('workspaces/hcwp-demo')
(root / 'target.md').write_text('Modern .NET server-interactive Blazor with EF Core in-memory persistence\n')
(root / 'agent.json').write_text(json.dumps({'command': {
    'executable': sys.executable,
    'arguments': [str(Path('adapters/hcwp_characterise.py').resolve())],
    'timeoutSeconds': 600}}, indent=2))
PY
./lmf characterise --workspace workspaces/hcwp-demo/migration \
  --source '../../example-code/HCWP Core (pseudonymised) - single file.txt' \
  --target workspaces/hcwp-demo/target.md \
  --agent workspaces/hcwp-demo/agent.json --repairs 2
./lmf status --workspace workspaces/hcwp-demo/migration
```

At this point **stop for human review**; no target app has been generated. After reviewing the artifacts below, the operator—not an agent—may run:

```sh
./lmf approve --workspace workspaces/hcwp-demo/migration --revision REVIEWED_CURRENT_HASH
./lmf resume --workspace workspaces/hcwp-demo/migration
./lmf status --workspace workspaces/hcwp-demo/migration
```

Replace the hash placeholder with the exact current revision reviewed by the operator. A failure retains diagnostics; fix the failed line or prerequisite and use the same `resume` command. Do not weaken approved scenarios to obtain a pass. The runner executes the generated `verify.py`; it builds/runs extracted C#, compares actual observations against every scenario, and writes `results.json`, `observations.json` and `reference-report.json`. Read `behaviour.md`, `gaps.md`, `dependencies.md`, `migration-plan.md`, `fixtures.json` and `reference/ADAPTATIONS.md` before any approval. Unadapted sections for all 94 files remain under `reference/original/`; `source-index.json` gives banner lines and section hashes. All reference sources, original sections, scenario inputs and verification code are revision-bound review files.

The examples expose head circumference 100 rejected by field validation yet accepted by direct save, and PhysicalGeneral alone not counted as a result. Do not harmonise these findings. Warnings use symbolic resource identifiers because translated resources are absent. Saved observations are detached input clones, **not persistence read-back**. Synthetic patient/date/schedule values are explicitly invented. DaysBetween/WeeksBetween are recovered from the bundle's DateCalculation.cs, including truncation toward zero before division by seven; fractional-day and negative-interval examples verify those extracted bodies. Repeat-flag recalculation for the selected patient's KD03 results is included and covered by the existing extracted scenarios. Windows lifecycle and excluded infrastructure remain review limitations rather than approval blockers. This is inspectable extracted-reference evidence, not parity with the original Windows/Oracle application.

To rerun extracted verification independently, run `python3 WORKSPACE/characterise/verify.py`. Prerequisites are Python 3 and .NET 10; no NuGet test framework or Oracle installation is required. `scenarios.feature` is the readable BDD companion; `scenarios.json` is the executable Given/When/Then suite interpreted by the reference adapter (not a Cucumber feature runner).

## Real-agent checkpoint

`adapters/pi_agent.py` connects the appended-request contract to locally installed Pi. See [`docs/hcwp-real-agent.md`](docs/hcwp-real-agent.md) for configuration, the actual agent-assisted Characterise run (371 runner-verified passes), retained evidence and the human approval handoff. Its separate workspace is awaiting approval; real-agent downstream migration and browser completion remain unverified.

## Synthetic seeding, launch and evidence

After the new migration reaches `completed`, launch it:

```sh
dotnet run --project workspaces/hcwp-demo/migration/refactor/app/Hcwp.csproj -- --urls http://127.0.0.1:5080
```

Open `http://127.0.0.1:5080`. Patient 1001 (boy, born 2025-01-01) is preselected and starts without saved results. Startup seeds patient 2002 with one KD03 result whose repeat flag is true, for isolation checks. Seeding is automatic and idempotent within the process; stopping and restarting the app resets the in-memory store and reproduces the initial fixtures. Reloading the page retains saves while that process runs. New drafts preset KD03/date 2025-02-20; the clock is fixed at 2025-03-01. Schedule 6–8 weeks, measurement/BMI bands and SYNTH lookup codes are invented review fixtures, **not clinical guidance**. Physical dropdown codes/labels come from the extracted source. Generated `refactor/REFACTOR.md` and approved `characterise/fixtures.json` document origins and defaults.

Read saved results beneath the form. Validation errors and unconfirmed warnings do not save; confirm warnings explicitly when appropriate. For a second result use a different date; read-back marks the earliest KD03 result non-repeat and later results repeat without changing patient 2002. Only KD03 is offered, and unsupported submissions are rejected. Persistence verification reads detached data through a fresh context rather than echoing the form.

Evidence relative to each migration workspace:

| Location | Evidence |
| --- | --- |
| `state.json`, `./lmf status` | Stage state, accepted attempts, current and approved revisions |
| `characterise/` | Behaviour/dependencies/gaps/plan, fixtures, scenarios, original-file index, reference sources/adaptations, `reference-report.json`, `observations.json` |
| `convert/` | Standalone port, `PORT.md`, `port-manifest.json`, `parity-report.json` |
| `refactor/` | Generated app, `REFACTOR.md`, manifest, `parity-report.json`, `persistence-report.json`, `browser-report.json`, `browser.png`, build/style/browser logs |
| Each stage's `attempts/NNNN/` | Requests, commands, stdout/stderr, check results and failure diagnostics |

Rerun checks independently with `python3 WORKSPACE/characterise/verify.py`, `python3 WORKSPACE/convert/verify.py` or `python3 WORKSPACE/refactor/verify.py`. These regenerate gate reports; numbered runner attempt evidence remains retained. The completed adapter migration and its approval are documented in [approval evidence](docs/hcwp-approval-gate.md) and [Refactor evidence](docs/hcwp-refactor.md). The separate [real-agent checkpoint](docs/hcwp-real-agent.md) must not be described as downstream completion or approved on the operator's behalf.

## Scope and limitations

This is a local synthetic KD03 add/read demonstration, not a production medical system. Patient search, editing/deletion, appointment management, recall processing, real patient data, Oracle connectivity, existing-database migration, Azure deployment and production authentication/authorisation are excluded. Other contact types are unsupported. Original Windows control/binding/event delivery, real service/lookup/transaction behaviour and original Windows/Oracle parity remain unverified. Head-circumference field/save limits differ in the supplied logic and are documented, not harmonised. Missing translated resources use symbolic warning identifiers.

EF Core in-memory data is temporary; no actual PostgreSQL persistence or PostgreSQL compatibility is established. Excluded appointment/recall effects mean this is not full legacy save-service parity. Real-agent Convert, Refactor and browser evidence remain unverified pending human approval of that separate workspace.

## Tests

Run the full implementation suite with `python3 -m unittest discover -s tests` (actual build/browser regressions require the prerequisites above).

The retained supplied-bundle approval checkpoint is documented in [`docs/hcwp-approval-gate.md`](docs/hcwp-approval-gate.md); its current revision is operator-approved. The retained migration has accepted Convert evidence. Refactor prerequisites are NuGet access for EF Core InMemory 10.0.0 and Python Playwright/Chromium (`python3 -m pip install playwright`, `python3 -m playwright install --with-deps chromium`). Missing prerequisites fail the gate. Launch the generated synthetic app with `dotnet run --project workspaces/hcwp/migration/refactor/app/Hcwp.csproj -- --urls http://127.0.0.1:5080`. Its `REFACTOR.md` documents source/default adaptations, synthetic fixtures, read-back and temporary-storage limitations. See [`docs/hcwp-refactor.md`](docs/hcwp-refactor.md) for evidence and scope.

`python3 tests/test_hcwp_refactor.py` checks final-assembly parity, EF fresh-context read-back, browser add/reload/invalid/warning paths, calculation mismatch, persistence defect, unavailable-browser failure, changed-input invalidation and recovery.

`python3 tests/test_hcwp_convert.py` checks standalone port parity, changed-calculation mismatch reporting, malformed observations, reviewed-input protection and recovery.

`python3 tests/test_hcwp_approval.py` exercises the actual reference verifier through the CLI and checks the revision-bound approval gate without generating a target.

`python3 tests/test_hcwp_characterise.py` runs the supplied bundle through actual extraction/build/verification, checks the documented discrepancies and approval readiness, and introduces an expected-observation mismatch to ensure comparison fails.

`python3 tests/test_cli.py` builds the CLI and executes subprocess-based deterministic agent doubles in temporary workspaces. Coverage includes approval stops, revision invalidation, blocking gaps, empty/skipped/failed/missing/stale verification, bounded repairs, retained diagnostics, workspace isolation and recovery without redoing accepted stages. These synthetic fixtures demonstrate orchestration only and do not represent HCWP behaviour.
