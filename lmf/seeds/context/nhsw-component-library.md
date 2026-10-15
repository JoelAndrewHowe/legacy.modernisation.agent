# DHCW NHSW component-library feed-forward

Use this context when a Refactor task creates or changes a user-facing web
interface. It supplements the stage seed; it does not override approved
behaviour, parity evidence or the task boundary.

## Provenance and authority

- Repository: <https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library>
- Guidance reviewed at commit: `5322c16910fbad0335b504ce80a1d8a50fe3b683`
- Reviewed: 2026-10-14
- Primary guidance: [`CLAUDE.md`](https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library/blob/5322c16910fbad0335b504ce80a1d8a50fe3b683/CLAUDE.md),
  [design-system rules](https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library/blob/5322c16910fbad0335b504ce80a1d8a50fe3b683/.agent/design-system-rules.md)
  and the [component registry](https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library/blob/5322c16910fbad0335b504ce80a1d8a50fe3b683/.agent/component-registry.md)
  at that commit.
- Canonical component markup: the relevant
  `src/components/<component>/macro.njk`, examples and preview at the commit
  selected for the implementation.

The upstream library is Sass and Nunjucks. For Blazor, translate the canonical
HTML structure, classes and accessibility relationships into Razor; do not add
Nunjucks as an application runtime. The library describes itself as in
development, so pin every consumed asset and do not treat a moving `main` branch
as a dependency version.

## Implementation rules

1. Reuse an existing NHSW component before inventing markup or styling. Start
   with the component registry, then inspect that component's macro and examples.
2. Use the standard shell where the slice needs a complete page: skip link,
   `nhsw-site-header`, `nhsw-main-wrapper`, `nhsw-width-container` (or the
   deliberately chosen fluid container), and `nhsw-site-footer`. Give the main
   content target the expected `maincontent` id.
3. Retain NHSW classes and semantic HTML. Do not invent colours, typography,
   spacing, breakpoints or inline styles. Keep unavoidable application CSS small
   and based on the library's tokens and utilities.
4. Every input has a visible matching label. Connect hints and errors with
   `aria-describedby`; set `aria-invalid="true"` when invalid. Group date parts
   and radio choices with `fieldset` and `legend`. Never use a placeholder as a
   label. Decorative SVGs are hidden from assistive technology.
5. Preserve the library's yellow focus treatment and verify visible keyboard
   focus. Do not weaken it to make the page look tidier.
6. Use DHCW identity. Do not introduce an NHS logo or imply generic NHS branding.
   Treat logos and other brand assets as separately reviewed dependencies.

The reviewed layout baseline uses a 960px maximum page width, 16px mobile and
32px desktop container margins, a 16px grid gutter, and 32px mobile/48px tablet
main-wrapper padding. Its breakpoints are 40.0625em (tablet), 48.0625em
(desktop) and 61.875em (large desktop). Use the library's implementation rather
than duplicating these values in application CSS; they are recorded here to make
invented breakpoints and spacing easy to spot during review.

## HCWP component map

For the HCWP add-and-read-back flow, prefer these documented patterns:

| Need | NHSW pattern and important structure |
| --- | --- |
| Text or numeric value | Form group, visible label, optional hint, input, and linked inline error |
| Choice | Select or radio component; radios retain `fieldset`/`legend` and conditional content semantics if used |
| Date | Date-input grouping with an explicit legend, unless a native date control is an evidenced intentional adaptation |
| Failed submit | Error summary with `role="alert"`, focus target and links to the affected control, plus its inline error |
| Clinical warning | Warning callout with its hidden prefix and decorative icon treatment intact |
| Save/secondary action | NHSW button variants with the correct native button type |
| Saved read-back | Summary list for labelled values; use a table only for genuinely tabular data |
| Successful completion | Panel when the flow needs a prominent confirmation, without replacing the saved values evidence |

Component markup is a pattern, not decoration. When Razor or Blazor lifecycle
behaviour requires an adaptation, record it beside the implementation and keep
the accessible outcome equivalent.

## Assets and behaviour

- Vendor a reviewed release or immutable commit's `preview/dist/nhsw.min.css`
  locally. Record repository URL, tag/commit, upstream path, local path,
  SHA-256 and the MIT licence. Do not use a runtime CDN.
- Add `dist/nhsw-behaviours.min.js` only when the selected components need it.
  Relevant examples include conditional reveal, character count, tabs, expander,
  file-upload status and session timeout. The date picker has a separate bundle.
- A script that scans the initial DOM may not automatically wire markup rendered
  later by Blazor. Exercise the real interactive lifecycle; do not infer it from
  static HTML.
- Do not overwrite a previously pinned asset merely because this context pack
  was refreshed. An asset upgrade is a deliberate, separately evidenced change.

## Evidence expected from the implementer

- Name the NHSW components used and any intentional Razor adaptations.
- Build and run the application, then exercise the real add, validation and
  persisted read-back flow in a browser.
- Check responsive behaviour at narrow and wide viewports, keyboard order and
  visible focus, labels and accessible names, error-summary links, error/hint
  associations, and rendered contrast.
- Verify that CSS and any necessary scripts are local and match the recorded
  checksums, and that no unexpected external requests occur.
- Keep failures and exclusions explicit. Upstream component tests do not prove
  that this application or its Razor translation meets WCAG.

## Refresh checklist

Before reusing this pack for a later iteration, resolve the new immutable
upstream commit or release and compare its `CLAUDE.md`, design-system rules,
component registry and relevant component macros with the commit above. Update
this summary only for material guidance changes. If assets are upgraded, update
their provenance, checksum and licence copy and rerun the application-level
browser and accessibility evidence.
