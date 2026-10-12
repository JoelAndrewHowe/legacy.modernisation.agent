# Refinement loop review

## Purpose

This note records why the factory became stuck refining Characterise, what has been changed in the iteration seed, what must be done to recover the current run, and what should be strengthened in later versions of the factory.

## What happened

The factory made real, passing changes, but stopped progressing through the main milestones. Its implementation plan grew to 81 checklist items, of which 72 were complete, while the top-level Characterise task remained open.

Recent tasks repeatedly strengthened already-passing evidence: object identity, collection identity, temporary replacement and restoration, mutation detection, and increasingly narrow boundary cases. Many plan entries said that approval blockers were unchanged and that the validator had supplied no findings.

This was a refinement loop rather than a failed-validation loop:

```text
Broad Characterise task remains open
              |
              v
Agent finds another possible improvement
              |
              v
Agent adds a narrow test and passes validation
              |
              v
Only the narrow subtask is closed
              |
              +--------------------------+
                                         |
                                         v
                         Broad task still remains open
```

## Why it happened

The iteration seed required strong evidence but did not define when the evidence was sufficient. Characterise was broad enough that an agent could always discover another method, event, boundary, identity, or hypothetical mutation to test.

The factory also has an important distinction between local and global success:

- The validator determines whether the latest change is satisfactory.
- The planner determines whether more tasks exist.
- Nothing independently determines whether the proposed next task is necessary for the seed's outcome.

Validation retry limits did not help because the changes were passing. `--all` bounds attempts within a task, but it does not bound the number of successful tasks the planner may create.

A human scope decision remained unresolved. The factory had no `waiting-for-human` state, so it continued finding adjacent work instead of stopping. Once the plan had grown, it became the planner's main description of the remaining work and weakened the connection to the original seed.

## Scope decision: repeat flags

Repeat-flag recalculation is **in scope** for iteration 001.

For the selected synthetic patient and supported `KD03` contact:

- The earliest `KD03` result is not a repeat.
- A later `KD03` result is a repeat.
- Recalculation does not alter another patient's results.

The existing extracted scenarios covering patient isolation, exact-code grouping, date ordering, equal-date behaviour, and idempotence are sufficient Characterise evidence. More repeat-flag tests are not required unless an existing scenario fails, the source or agreed scope changes, or a validator reports a concrete defect.

Effects on unsupported contact types are outside this slice. Appointment-status updates and recall processing remain excluded and must be reported as limitations. This means the iteration does not claim full save-service parity.

## Changes made to the seed

The iteration seed now includes:

1. The explicit repeat-flag decision above.
2. A Characterise completion policy tied to the named artifacts and shared scenarios.
3. A boundary limiting Characterise to behaviour reachable from the `KD03` add-and-read workflow.
4. A rule against adding tests solely for hypothetical mutations after applicable behaviour passes.
5. Defined reasons for reopening completed work:
   - an acceptance example or existing verification fails;
   - the validator identifies a concrete defect in the current change;
   - a required artifact is missing or malformed; or
   - the source or agreed scope changes.
6. A distinction between blocking gaps and documented limitations.
7. A requirement to stop at the approval gate when human action is required.
8. A planning rule requiring every unfinished task to name the acceptance example, required artifact, failing check, or validator finding that justifies it.
9. An acceptance example for repeat-flag behaviour and patient isolation.

These are specification constraints. They guide planning but do not yet provide mechanical enforcement in the iteration-2 factory.

## Recovery for the current run

Changing the seed does not automatically rewrite the existing `.factory/plan.md`. The current run must be reconciled before using `--all` again.

1. Review the interrupted, uncommitted Characterise changes and either validate and retain them or deliberately discard them.
2. Record the repeat-flag decision in the implementation plan and close its resolved blocker.
3. Review the open executable-delegate-coverage parent task. Close it if its named behaviours are covered and its remaining items are documented non-blocking limitations.
4. Classify Windows control behaviour, Windows event delivery, excluded infrastructure, and behaviour outside `KD03` as non-blocking limitations.
5. Run the existing Characterise verification once.
6. If the required artifacts exist and the shared scenarios pass, close Characterise.
7. Proceed to reference verification and the explicit human approval gate.

Until this reconciliation is complete, run one factory pass at a time rather than running to completion with `--all`.

## Factory changes still needed

The seed reduces ambiguity. A robust factory should also enforce the boundary:

### Keep planning anchored to the seed

The planner should compare every proposed task with the original outcomes and acceptance examples, even after a plan exists. A task should carry a stable identifier and cite the acceptance criterion, failure, artifact, or validator finding that requires it.

### Add a scope gate

Before work begins, a separate decision should determine whether the proposed task is necessary. The work validator answers "was this task done correctly?"; the scope gate answers "was this task required?"

```text
Planner proposes a task
          |
          v
Scope gate checks the seed
       /     \
      /       \
 required   unjustified
    |            |
    v            v
  Doer       reject, finish,
             or wait for human
```

### Represent human waiting explicitly

A run needs at least three outcomes: more automated work is ready, the run is complete, or it is waiting for a named human decision. Waiting must stop execution without pretending that the whole plan is complete or failed.

### Bound the whole run

Retry limits apply only to failed attempts at one task. The factory also needs a configurable maximum number of tasks or passes for an unattended run. Reaching that limit should retain state and report the remaining work.

### Detect stalled progress

The factory should stop when the same parent milestone keeps gaining completed subtasks while its blocker and completion state remain unchanged. Useful signals include plan growth, repeated blocker text, and repeated successful passes under the same parent task.

### Validate against the relevant contract

The validator should receive the seed and the current task's acceptance criterion, not only the plan and current diff. Findings should identify the violated criterion rather than introduce open-ended improvements.

## Effect of later course iterations

Later iterations improve the architecture and the ability to intervene, but they do not automatically remove this failure mode.

| Course iteration | Improvement | Effect on refinement loops |
| --- | --- | --- |
| 003 — Assembly line | Configurable graph of machines and routes | Provides a place for scope and human gates, but the planner can still create unbounded work. |
| 004 — Runs and targets | Named runs with isolated plans | Improves recovery and isolation, but does not define sufficiency. |
| 005 — Fan out | Multiple reviewers and synthesis | Can improve decisions; can also produce more optional findings without a scope policy. |
| 006 — Watching | Monitoring, stop, and resume | Makes a loop visible and interruptible. |
| 007 — Steering | Messages can steer a working machine | Allows a human to redirect a looping planner or doer. |

The later features make the safeguards above easier to implement. The factory still needs explicit completion, scope, budget, waiting, and escalation policies.

## Vision review

The product vision remains sound: behaviour preservation, incremental slices, mechanical evidence, and human decisions are appropriate foundations. The experiment exposed missing operating principles rather than a wrong goal.

Recommended additions to the vision are:

- **Evidence is proportional to the slice:** Agree the required observable behaviours before implementation. Record unrelated or unreachable behaviour for later work.
- **Every loop has an exit:** A station ends as passed, failed with retained diagnostics, or waiting for a named human decision.
- **Discovery does not silently expand scope:** A new finding becomes a documented limitation or proposed follow-up unless it blocks an agreed acceptance example.
- **Completion is externally defined:** Agents may produce work and evidence, but the gate's finite criteria are established before the work begins.

The sentence "A slice that fails at any gate goes back" should also state a bounded retry/escalation policy. The phrase "everything between those decisions should run without their intervention" should allow the factory to pause when it discovers a new decision that only a human can make.

There is also a typographical error: "each slide of the legacy system" should be "each slice of the legacy system."

## Expected learning

This behaviour is understandable for an iteration-2 teaching factory executing a large, open-ended seed. It is not a desirable production behaviour, but it exposes an important distinction:

> Quality control asks whether a change was done well. Production control asks whether that change was necessary and whether enough has now been produced.

A dependable software factory needs both.
