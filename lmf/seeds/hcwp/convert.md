# HCWP slice 01 — Convert

Run the Convert stage for the approved HCWP `KD03` add-and-read-back slice.
Read `lmf/docs/vision.md`, `lmf/iterations/001-characterise-and-migrate-hcwp.md`,
and this target's accepted `characterise/` artifacts before planning.

The operator must have created `approvals/characterise-approved.md`, identifying
the reviewed Characterise evidence revision. If it is absent, stale, or does not
cover the current scenarios and reference artifacts, record the human-owned
blocker and do no conversion work. Never create or amend that approval yourself.

Work only in this target's `convert/` directory. Port one approved slice to
modern .NET while retaining the legacy structure and observable behaviour. This
source and target are both C#, so this is a runtime and dependency conversion,
not a language rewrite.

Required outcomes:

- Retain the approved control flow, validation, warning, calculation and
  read-back behaviour. Preserve known quirks unless the approval explicitly
  authorises a difference.
- Document every runtime or dependency substitution in `convert/PORT.md`.
- Keep the converted implementation independent of the executable reference;
  it must not delegate its work to reference code.
- Do not introduce Blazor, redesign persistence, improve object structure, or
  fix business rules. Those changes belong to Refactor.
- Run the same approved scenario identifiers, inputs and expected observations
  against both the reference and conversion.
- Produce per-scenario observations and `convert/parity-report.md`, including
  commands, revisions, exact matches, limitations and any normalisation.
- Provide a repeatable verification command with positive passes, zero failures,
  zero skips and no omitted approved scenario.

Convert is complete only when the executable parity evidence matches the current
approved Characterise baseline. Do not weaken scenarios, edit the reference, or
replace runtime evidence with a work-log assertion.
