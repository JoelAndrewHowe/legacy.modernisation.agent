# Vision: Legacy Modernisation Factory

The Legacy Modernisation Factory is a software factory that takes an old service or module and migrates it, one deliverable slice at a time to a target architecture, proving at every step that the new code behaves like the old.

## Goal

Make the modernisation of a legacy module a repeatable, evidence-backed process instead of a risky one-off rewrite. For the capstone, that means taking one real life legacy module through the full factory to idiomatic code in the target stack, with the same behaviour driven tests passing on both the old and new implementations.

## What Legacy Modernisation Factory Is

The Legacy Modernisation Factory is a software factory for the migration of legacy software components. Given a legacy service or module and a target architecture or framework, it analyses the legacy code, captures its behaviour as BDD tests, and rebuilds it incrementally in the target.

The same test suite runs against the legacy code and the new implementation. A slice is finished only when both give matching results.

It is a factory rather than single agent because the "what" is already defined by a legacy module/system.

## Assembly Lines

The factory runs three lines in order, and each slide of the legacy system will pass through all three. Conversion and refactoring are deliberately separate lines: the first changes the language, the second changes the design, and neither does both. This allows us to enforce parity against the old solution and the new, before rearchitecting.

| Line            | Takes in                 | Produces                                                     | Gate to leave the line                                       |
| --------------- | ------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 1. Characterise | Legacy module            | Behaviour tests, dependency map, migration plan split into slices | Tests pass against the legacy code                           |
| 2. Convert      | One slice plus its tests | A literal translation in the target language that keeps the legacy structure | Same tests pass against the translation                      |
| 3. Refactor     | The literal translation  | Idiomatic code in the target architecture                    | Same tests still pass, plus the target's lint and style checks |

A slice that fails at any gate goes back to the start of the line it failed, and not back to the start of the factory.

## Principles

- **Behaviour is the specification**: What the legacy system observable does defines "correct". Comments and documentation can be used for hints to purpose. Legacy bugs are preserved by default and flagged for human review, never silently fixed.
- **Tests before translation:** No slice enters the convert line until its behaviour tests pass against the legacy code. The same tests follow the slice through every later line.
- **Translate first, improve second:** Whilst the Convert line may initially produce ugly code, it'll create code that is equivalent. Refactor may change structure but never the behaviour of the code. Each change is one kind of change, so a failure only has one kind of cause.
- **Incremental changes and always a shippable slice:** The factory aims to migrate one slice at a time, with legacy and new code being able to run side by side. Stopping after any slice should leave a working system.
- **Evidence over assertion**: An agent can't mark it's own work as done. Every gate is a mechanical check, and every slice ships with a parity report showing which tests ran and on which implementation.
- **Humans decide, the factory executes:** Humans chose the target architecture, approve the migration plan, and rule on intended differences in behaviour. Everything between those decisions should run without their intervention.
- **Small, replaceable stations**: each station has a narrow job and a defined input and output. Swapping a model or prompt, or adding a new language pair, should change one station and not the factory.