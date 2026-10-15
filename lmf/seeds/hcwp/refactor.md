# HCWP slice 01 — Refactor

Run the Refactor stage for the accepted converted HCWP `KD03` add-and-read-back
slice. Read `lmf/docs/vision.md`, `lmf/iterations/001-characterise-and-migrate-hcwp.md`,
the approved `characterise/` artifacts, and the accepted `convert/` evidence.

## Feed-forward context

Before planning or changing user-facing code, read
`../context/nhsw-component-library.md`, resolved relative to this seed. Treat it
as required implementation guidance for UI tasks and record any necessary
Blazor adaptation. It does not broaden the KD03 slice or override approved
behaviour and executable evidence.

Do not begin unless `approvals/characterise-approved.md` still covers the current
Characterise baseline and Convert has complete matching parity evidence. Agents
must not create human approval records or weaken upstream scenarios.

Work only in this target's `refactor/` directory. Introduce the agreed target
architecture: modern .NET, server-interactive Blazor and EF Core in-memory
persistence for the bounded synthetic demonstration.

Required outcomes:

- Preserve all approved scenario outcomes, validation, warnings, calculations
  and patient-specific saved/read-back values.
- Use cohesive responsibilities, encapsulate invariants and separate domain,
  presentation and persistence concerns where the current slice benefits.
- Support only KD03; do not imply coverage of other contacts or excluded
  appointment/recall behaviour.
- Read saved data back through a fresh EF context rather than echoing form values.
- Keep the complete user flow clear: add a valid result, reject approved invalid
  input, show applicable warning/confirmation behaviour and reload saved data.
- Use the official [DHCW NHSW component library](https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library)
  for the Blazor interface. Vendor a reviewed release or pinned commit of its
  compiled `nhsw.min.css` into the app's static assets, record its provenance and
  checksum, retain its MIT licence, and avoid a runtime CDN dependency. Translate
  applicable documented component markup to Razor while retaining NHSW classes
  and accessible structure. Add the matching behaviours script only for
  components that require it. Keep bespoke CSS small and based on library tokens
  or utilities where practical.
- Run the same approved scenarios against reference, conversion and refactored
  implementation, producing per-scenario observations and
  `refactor/parity-report.md`.
- Run build, configured formatting/style checks, persistence checks and a real
  browser-level add-and-read-back demonstration. Missing browser prerequisites
  must fail the gate and be reported, not replaced by mocked success.
- Include browser checks for responsive layout, visible keyboard focus, labels,
  error summary links, contrast and the applicable NHSW component presentation.
- Document synthetic fixtures, EF in-memory limitations, excluded infrastructure
  and the absence of original Windows/Oracle and PostgreSQL verification.

Refactor is complete only when parity, build/style, persistence and applicable
browser checks have positive executed evidence with zero failures and zero skips.
Optional visual polish and speculative architecture work are not blockers.
