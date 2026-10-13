# Migration assembly lines

Reusable iteration-4 factory configurations based on [the LMF vision](../../docs/vision.md).
Copy `.assembly-lines/` into a new migration product target. These files are
templates for `bin/factory`; the existing `lmf/implementation/lmf` CLI does not
load DOT files. They do not modify an existing migration or its approval state.

## Lines and machines

All three lines use the shared `planner` and `doer`. Each reviewer is a named
machine with `"role": "validator"` and a specialised lens. All harnesses are
initially `pi` and can be changed in the individual `config.json` files.

| Line | Review stations, in order | What they look for |
| --- | --- | --- |
| `characterise` | `source-fidelity`, `dependency-scope`, `reference-evidence` | Source-backed behaviour, honest scope and dependencies, executable legacy-reference evidence |
| `convert` | `translation-fidelity`, `behavioural-parity` | Literal translation or runtime port, unchanged approved behaviour and matching scenario observations |
| `refactor` | `architecture-review`, `behavioural-parity`, `delivery-review`, `nhsw-design-review` | Idiomatic design and encapsulation, preserved behaviour, delivery evidence and correct use of the DHCW NHSW design system |

The planner selects the next task. The doer implements it. All reviewers must
accept that attempt before it returns to the planner and its product work is
committed. Any rejection returns findings to the doer, and the next attempt
restarts the entire review chain for that line. The attempt limit counts doer
attempts per task, not reviewer calls.

The OO lens is deliberately confined to Refactor: Convert must be allowed to
retain awkward legacy structure. Delivery review follows the seed's interface
and architecture, without inheriting the Tetris-specific UX requirements. The
final NHSW review applies only to user-visible Refactor tasks and checks locally
vendored, traceable component-library assets and rendered accessible markup.

## Seeds define the stage's work

The line selects reviewers; the seed tells the shared planner and doer what to
build. The current factory does not apply a lens to the planner or doer, and a
line's filename is not a stage instruction. Use a separate, self-contained seed
for each stage and slice. Each should include:

- The stage, legacy source paths, slice boundary, target architecture, and exclusions.
- Required input artifacts and their revisions, expected output paths, and acceptance examples.
- The executable verification commands and evidence/report locations.
- Approved behaviour, intentional differences, and the applicable human approval record.
- A bounded task list or completion criteria, including what is explicitly deferred.

Characterise seeds should require behaviour scenarios, reference evidence,
dependency mapping, gaps, and a sliced migration plan. They must exclude product
conversion and stop for human review once the required evidence is ready.
Convert seeds must require the approved reference/scenarios and permit only
translation or necessary runtime/dependency substitutions. Refactor seeds must
require an accepted conversion and name the permitted architectural changes.

For HCWP, the accepted baseline is extracted legacy logic, not the unavailable
original Windows/Oracle application. Convert is a C# runtime/dependency port;
Blazor and EF Core changes belong to Refactor. Preserve these distinctions in
the seeds and reports.

## Install into a fresh target

From the repository root, choose a new migration target and copy the configuration:

```sh
mkdir -p migrations/example
cp -R lmf/templates/migration-target/.assembly-lines migrations/example/
```

Write the three scoped seed files first. For example, after creating
`migrations/seeds/slice-01-characterise.md`, the tutorial factory invocation is:

```sh
bin/factory --run slice-01-characterise \
  --target migrations/example --line characterise \
  --seed migrations/seeds/slice-01-characterise.md --attempts 6
```

Use distinct run names and matching seeds for `convert` and `refactor`. Their
plans belong to `factory/runs/<run-name>/plan.md`; they can share the product
target and its machine configurations. Run one at a time against that target.
Resume an unfinished run with its name and, if desired, `--attempts 6`.
These are setup examples, not evidence that a migration has been executed.

Do not use `lmf/implementation/` as the migration product target: that directory
contains the LMF tool itself. Likewise, the existing seed that builds the whole
LMF tool is not an appropriate seed for an individual migration stage.

## Review is not a mechanical stage gate

These configurations are agent review pipelines. They are not wired into LMF's
stage runner and do not automatically chain Characterise, Convert, and Refactor.
The tutorial factory currently does not enforce approval, upstream stage
completion, or a final whole-stage check. In particular, a planner returning
`complete` can finish a run without executing reviewers again.

Every lens requires concrete evidence and rejects unsupported claims, but its
`satisfied` result is still an agent judgment. The machines named
`reference-evidence` and `behavioural-parity` review evidence; their names do not
turn them into deterministic test executors. A successful DOT run is not proof
that a migration stage's mechanical gate passed.

For real migrations, retain the existing LMF runner's verification, revision-bound
human approval, and stage prerequisites described in
[the implementation README](../../implementation/README.md). Connecting these
DOT review loops to that runner requires an adapter; none is installed here.
Do not manually launch a Convert/Refactor run as a substitute for those gates.

Human-owned blockers must be escalated. This factory's review loop cannot enter
LMF's `awaiting-approval` state: a rejection retries until the attempt limit.
Do not let an agent fabricate approval or spend retries trying to resolve a
human decision. Use LMF's approval workflow for that checkpoint.

The lenses intentionally constrain findings to concrete blockers in the current
task, preserve accepted scenarios/reference artifacts, and prevent unrelated
redesign or speculative test expansion. Evidence requirements apply when that
task delivers or verifies the corresponding behaviour, not prematurely during
an earlier scaffold task.
