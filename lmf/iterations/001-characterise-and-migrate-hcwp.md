# Iteration 001: Characterise and migrate one HCWP recording workflow

Status: Scope agreed through interview; ready to use as an implementation seed. The generated behaviour specification still requires its own human approval during an LMF run.

## Outcome

Build the first usable slice of the Legacy Modernisation Factory (LMF): a command-line tool that takes supplied legacy source, infers a behaviour specification for a bounded workflow, pauses for human approval, and then produces a working modern implementation with executable evidence of preserved behaviour.

The first demonstration is adding a Healthy Child Wales Programme (HCWP) **6–8-week contact result** to an already-selected synthetic patient's record and reading that saved result back. In the supplied pseudonymised source, this contact is `KD03`: `KdpExaminationResultDelegate` defines `ExamCode6To8WeekContact = "KD03"` and uses it in `Is6To8WeekContact`. This identifies the chosen contact; it does not claim that it is the first contact in the programme's schedule. The source is a .NET Framework 4.5.1 Windows Forms application using delegates/view models, services, EF6, and Oracle. The demonstration target is modern .NET, Blazor, and Entity Framework Core's in-memory provider, running in Linux/a dev container.

Azure Database for PostgreSQL is the eventual storage destination. This iteration neither connects to PostgreSQL nor proves PostgreSQL compatibility. In-memory data is temporary and may reset when the application restarts.

## Product and input boundaries

The existing `factory/` is the tool that will implement this seed. LMF is the product it builds. LMF must itself perform the analysis, approval, conversion, refactoring, and verification workflow; a hand-built HCWP web application alone does not satisfy this iteration.

Use `example-code/HCWP Core (pseudonymised) - single file.txt`, relative to this repository's root, as the first legacy input. It bundles 94 source, test, and SQL files with original-file banners. Preserve the supplied input and use those file identities in source references.

The bundle explicitly is not a buildable legacy project. Its schema is reconstructed from mappings, with inferred details and omitted triggers. The user accepts an executable reference harness extracted from the supplied logic as the baseline for this demonstration. Evidence must say **parity with extracted legacy logic**, not parity with the original Windows/Oracle application. Verification against that application remains outstanding.

LMF must accept the source path and a target description as inputs. Keep the workflow and its stage contracts separate from stack-specific prompts/adapters. Implement only this source/target combination initially; support for arbitrary stacks is a future goal, not an iteration acceptance claim.

## Agreed functional scope

- A synthetic patient is already selected. Provide enough patient context for applicable legacy rules, such as date of birth and existing results.
- Support only the 6–8-week contact (`KD03`). Include the common recording fields and contact-specific fields/rules applicable to it. Other contact types, including 15/27-month contacts, are outside this iteration. The generated UI must not offer unsupported types, and submissions for them must not save a result.
- Infer the recording fields, available values, defaults, validation, warnings, calculations, and saved data from the supplied code. Do not ask the operator to re-specify behaviour that the source establishes.
- Add a result, associate it with the selected patient, and display the saved result after reading it through the persistence layer.
- Preserve applicable validation and warning/confirmation behaviour. Include unsuccessful submissions and demonstrate that they do not save a result.
- Preserve repeat-flag recalculation for the selected patient's `KD03` results: the earliest result is not a repeat and later results are repeats. Existing extracted scenarios for patient isolation, exact-code grouping, date ordering, ties, and idempotence are sufficient evidence for this iteration. Effects on unsupported contact types are outside this slice.
- Use synthetic patients and supporting lookup data with documented origins. Clearly identify invented demonstration values.
- Generate a readable behaviour specification and gaps report for human approval before generating the target implementation.

Excluded: patient search, editing or deleting saved results, appointment management, recall processing, production patient data, Oracle connectivity, Azure deployment, actual PostgreSQL persistence, and migration of an existing database.

### Scope decision: repeat flags

Repeat-flag recalculation is **in scope** for this iteration. When the selected patient has more than one `KD03` result, the earliest result is not a repeat and later results are repeats. Recalculation must not alter another patient's results.

The extracted reference scenarios already cover patient isolation, exact-code grouping, date ordering, equal-date behaviour, and idempotence. That is sufficient Characterise evidence for this iteration. Do not add further repeat-flag cases unless an existing scenario fails, the source or scope changes, or validation identifies a concrete defect.

Effects on unsupported examination/contact types are outside this slice. Appointment-status updates and recall processing are also excluded.

The save service also updates appointment statuses and recalls. The Characterise line must identify these excluded dependencies. Excluding appointment and recall processing must not be described as full save-service parity. Existing results are fixtures for repeat-flag recalculation, duplicate checks, and other included recording rules.

## Assembly lines and approval

### 1. Characterise

Inspect the supplied UI, delegates, contracts, validators, services, mappings, tests, and SQL relevant to the workflow. Produce:

- A behaviour specification with source references, observable examples, and a field/rule inventory.
- A dependency map and a migration plan for this one workflow.
- A gaps and assumptions report distinguishing source-backed behaviour, synthetic fixtures, unavailable dependencies, contradictory rules, and intentional exclusions.
- Shared executable BDD scenarios and an executable reference harness using extracted legacy logic.
- Results showing which scenarios pass against that harness and the limitations of that evidence.

Retain the original reference logic as far as practical. Document every adaptation needed to compile or execute it and every dependency double. Doubles may stand in for excluded infrastructure; they must not invent the business rules being verified. Keep the reference independently inspectable from the target implementation.

Source inspection has already exposed potentially different head-circumference limits in field validation and save validation. Investigate the observable paths and report such differences; do not silently harmonise them.

For the selected contact, inspect the physical-assessment fields (including heart, hips, eyes, testes, and general assessment) and their applicability, alongside the shared recording fields. Do not infer mandatory fields or enforce an exact age window from the contact's name: the source obtains recommended age limits from schedule data and has age-warning logic. Identify unavailable schedule/lookup values as gaps or explicitly labelled demonstration fixtures for review.

#### Characterise completion policy

Characterise is complete when the named artifacts exist, all shared scenarios required by this seed pass against the extracted reference, and remaining limitations are recorded in the gaps report. It covers behaviour reachable from the scoped `KD03` add-and-read workflow; it does not seek exhaustive coverage of every supplied method, UI event, object identity, mutation, or hypothetical defect.

A completed area may be reopened only when an acceptance example or existing verification fails, the validator reports a concrete defect in the current change, a required artifact is missing or malformed, or the source or agreed scope changes. Do not add tests solely to detect hypothetical mutations after the applicable acceptance behaviour passes.

Unknown or unverified behaviour must be recorded as a limitation. It blocks Characterise only when it prevents a required scenario from executing or makes its expected observable outcome indeterminate. Windows control behaviour, event delivery, excluded infrastructure, and behaviour outside the selected workflow are non-blocking when accurately reported.

When the only remaining action is human review or a scope decision, stop at the approval gate and report that action. Do not create unrelated implementation or verification work while waiting. Passing checks plus a documented limitation are sufficient when this policy classifies that limitation as non-blocking.

Once the Characterise gate passes, stop in an explicit awaiting-approval state. The operator reviews the behaviour specification, scope exclusions, assumptions, and plan. Blocking gaps require resolution or an explicit scope adjustment. Approval must refer to the exact reviewed revision. A change to the source, target description, approved behaviour, or scenarios invalidates that approval.

### 2. Convert

After approval, move the included extracted business logic to modern .NET while retaining its legacy structure and behaviour. Both source and target are C#, so this stage is a runtime/dependency port rather than a language translation. Document necessary compatibility substitutions.

Do not introduce the Blazor presentation or redesign persistence in this line. Its gate is the same approved BDD scenarios passing against the converted implementation, with observable results matching the reference.

### 3. Refactor

Introduce an idiomatic Blazor interface and EF Core in-memory persistence around the converted behaviour, keeping the approved recording rules and outcomes. Presentation may adapt to the browser; behavioural differences require review.

The gate requires shared scenarios passing against the final implementation, matching reference outcomes, and passing build, configured style checks, and a browser-level add-and-read-back demonstration. Persistence checks must read saved data through a fresh context, not merely echo form values.

## Execution and evidence

Use a configurable locally installed coding-agent command, following the existing factory's harness approach. Document the command contract and prerequisites. Keep agent invocation replaceable and allow deterministic doubles for automated workflow tests.

Agents produce artifacts; the LMF runner executes verification commands and determines gates from their results. An agent's claim that tests passed is insufficient. Failed, skipped, missing, or empty verification cannot constitute a successful gate.

The shared suite must exercise the reference, converted logic, and refactored implementation through adapters using the same scenarios, inputs, and expected observations. Include saved values and relevant warnings/errors in the comparison. Control time and generated identifiers where necessary; document any normalisation so differences are not hidden.

Produce a readable parity report identifying the input revision, approved specification, implementation/stage, scenario identifiers, results, comparison outcomes, commands, and evidence locations. Explicitly list unverified behaviour and excluded infrastructure.

Preserve artifacts and stage state across invocations. Resuming after approval continues with conversion. A failure returns to the failed line without discarding previously accepted lines. Do not automatically weaken approved scenarios or mutate the reference to make target tests pass. Unresolved failures must stop with actionable diagnostics and retained evidence.

## Agreed operational defaults

- Use a local CLI and files for review and approval; no LMF management web interface.
- Keep each migration's artifacts in its own workspace, with explicit commands to characterise, approve a revision, resume, and inspect status. Exact command names are an implementation choice.
- Implement LMF in C# on a supported modern .NET release available in the development environment. Use server-interactive Blazor for the generated demonstration to keep local operation simple.
- Use a bounded, configurable retry count for automated stage repairs and return a nonzero exit code on failure. Awaiting approval is a distinct normal state.
- Provide reproducible synthetic seeding and a local launch command. Reloading a page retains saved results during the running application's lifetime; restarting may reset them.
- Keep this a local demonstration without production authentication, authorisation, or deployment infrastructure.

## Acceptance examples

1. Given the supplied bundle and target description, LMF generates the characterisation artifacts, runs reference scenarios, and stops for approval without generating the target application.
2. Given an unapproved or changed specification, attempting to resume cannot enter conversion.
3. Given approval of the current revision, LMF converts the logic, mechanically verifies parity, then refactors and verifies again.
4. Given a valid 6–8-week contact (`KD03`) result for a selected synthetic patient, the generated browser application saves and reads back its values against that patient, including the approved contact-specific fields.
5. Given invalid input covered by the approved specification, the application presents the corresponding validation outcome and saves no result.
6. Given a deliberately introduced target behaviour mismatch, the relevant parity gate fails and the report identifies the scenario and differing observations.
7. Given an agent failure or failed verification, LMF retains diagnostics and resumes at the failed line without rerunning accepted lines unnecessarily.
8. Given the completed demonstration, its report explicitly states the extracted-reference and in-memory-storage limitations.
9. Given another contact type, the generated application does not offer it and rejects an attempted submission without saving a result.
10. Given two `KD03` results for the selected patient on different dates, read-back identifies the earliest as not a repeat and the later result as a repeat without changing another patient's results.

Test LMF's orchestration deterministically with agent doubles, including the approval and failure paths. Also perform and document one real-agent run on the supplied bundle, followed by the generated application's tests and browser demonstration. If prerequisites prevent that run, report it as unverified rather than substituting a mocked success.

## Implementation handoff

This document is the existing factory's implementation seed and must be usable without conversation history. Use `lmf/implementation/` as the default separate target directory, leaving the source bundle and iteration documents as inputs. Document how to supply the bundle and target description, review and approve the inferred specification, resume, inspect evidence, and launch the generated demonstration.

Keep the implementation plan bounded by the outcomes and acceptance examples in this document. Every unfinished task must name the acceptance example, required artifact, failing check, or validator finding that justifies it. Do not create a new task merely to strengthen already-passing assertions against a hypothetical mutation. Once a task's stated evidence passes, close its parent task unless a named blocker remains. A human-owned blocker must pause progress rather than cause the plan to expand around it.

From the repository root, the implementation can be started with:

```sh
bin/factory --seed lmf/iterations/001-characterise-and-migrate-hcwp.md --target lmf/implementation --all
```

This command builds LMF; the resulting LMF CLI is then used to run the HCWP migration and its separate approval workflow.

This iteration's implementation specification and LMF's generated HCWP behaviour specification are separate artifacts. Agreeing to this seed does not pre-approve the behaviour subsequently inferred by LMF.
