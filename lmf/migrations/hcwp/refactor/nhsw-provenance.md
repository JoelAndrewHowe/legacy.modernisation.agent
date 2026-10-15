# NHSW asset and markup review

Official repository: https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library

Pinned commit reviewed: `043d882318918e2a4e8847e16fc3bfe694973c08`.
Assets were copied byte-for-byte from that commit (not rebuilt or fetched at runtime).
The upstream README recommends `preview/dist/nhsw.min.css` for production.
This is a local integration review, not a claim of upstream release certification.

| Upstream path | Local path (under `src/wwwroot/vendor/nhsw/`) | SHA-256 |
| --- | --- | --- |
| `preview/dist/nhsw.min.css` | `nhsw.min.css` | `117106cd1129ddfc0dae636d123d9123583c8f3970ebad63e2295d63bb502d99` |
| `LICENSE` | `LICENSE` | `0a657e4e9df62b5286ded60d036205904cc1ab1194f2e812f873848267fc114a` |

Review URLs use this prefix:
`https://github.com/DHCW-Digital-Health-and-Care-Wales/nhsw-component-library/blob/043d882318918e2a4e8847e16fc3bfe694973c08/`.

Reviewed README, MIT licence, `preview/_layouts/simple.html`, examples
`input-hint.html`, `select-hint.html`, `error-summary-default.html`,
`summary-list-no-border.html`, `button-secondary.html`, and component/token
sources `src/components/actions/_button.scss` and `src/tokens/_colours.scss`.
The matching `dist/nhsw-behaviours.js` error-summary behaviour was inspected.

## Razor translation

- Official main-wrapper/width-container layout, heading classes, form groups,
  labels, date input styling, hint association and native select.
- Official primary/secondary buttons and responsive summary-list rows with
  semantic `dl`/`dt`/`dd`. The selected patient and exclusions remain explicit.
- Full-flow save errors use the NHSW error-summary classes, alert role,
  title association and focusable container, with explicit Blazor summary/link
  focus. Inline errors translate pinned `preview/error-states.html` input and
  `preview/examples/select-error.html` markup, retaining form-group error and
  `nhsw-is-invalid` classes, hidden Error prefix and ARIA associations.
- Warnings translate pinned `preview/examples/warning-callout-default.html`:
  heading (adapted to h2), hidden decorative icon, heading-text with hidden
  Important prefix, content wrapper and body class. Approved message identities
  are unchanged. `full-flow.md` links executed changed-state evidence; historical
  preview evidence below must not certify the expanded interface.
- Native HTML date input is deliberately not the library date-picker component.
  None of the current components requires a library behaviours script. No tabs,
  expandable/conditional content, counts or date-picker are introduced, and no
  unnecessary script or runtime CDN is included. The upstream summary script
  scans only on load; it must not be assumed to wire later Blazor error panels.
- Zero bespoke CSS. Library system fonts, colours, spacing, responsive rules and
  focus styles are used unchanged. Asset URL is local; build-time assets are
  enabled for the documented local `dotnet run` demo even with its default
  Production environment. This is not production deployment verification.

## Current task-3 English shell evidence

The historical preview/full-flow measurements below apply to the previous interface, not the new shared shell. Current revision-bound English shell/routes evidence is in `../system-feel/refactor/evidence/task-3-accessibility-passing/`: source identities, Chromium 7/7 groups, 986 contrast observations, 42 keyboard-focused links, per-link screenshots and alert-bearing component-harness accessibility snapshots at 320/1280px. See `../system-feel/refactor/task-3.md` for the validator findings, focus repairs, exact command and test-only harness boundary. This is not the later bilingual/filter gate or a full WCAG/assistive-technology audit.

## Executed evidence

`verify-nhsw` checks approval prerequisites, asset checksums, builds, launches a
real application and runs Chromium through `browser/nhsw.mjs`. Missing browser
prerequisites fail, not skip. `evidence/nhsw-browser/results.json` records six
passing check groups, zero failures/skips: local CSS/no external requests,
labels, official primary colour, keyboard focus, executed contrast and no
overflow at 320/768/1280 pixels. Screenshots are adjacent. These checks cover
the present preview only, not full-flow/error-link checks or the final gate.

### Current rendered contrast (validator repair)

Re-executed `refactor/verify-nhsw` in real Chromium 156.0.8078.4. The browser
uses `browser/contrast.mjs` to measure computed sRGB foreground/background
colours with ancestor alpha compositing and the WCAG relative-luminance
formula. Evidence retains colours, font size/weight, exact unrounded ratio,
threshold, state and pass result, plus execution timestamps and source hashes.
There are **146 measurements: 141 applicable AA threshold assertions pass**
and five explicitly informational yellow/page comparisons. Zero failures/skips.
Text uses SC 1.4.3 (4.5:1 normal; 3:1 at >=24px or >=18.667px bold);
control boundaries, the reviewed select arrow and contrasting focus portions
use SC 1.4.11 (3:1). Visible keyboard focus is checked separately (SC 2.4.7).

| Rendered presentation | Measured ratio (rounded here only) |
| --- | --- |
| Body, headings, labels and saved summary text / page | 13.022:1 |
| Hint / page | 5.751:1 |
| Input/select text and select arrow / white control | 14.420:1 |
| Input/select/secondary button boundary / page | 5.751:1 |
| Primary button white text / blue; blue fill / page | 12.122:1; 10.947:1 |
| Hover primary/secondary button text | 14.247:1; 12.881:1 |
| Focus button text and dark underline / yellow | 11.810:1 |
| Focus dark control edge / white; dark border / yellow | 14.420:1; 11.810:1 |
| Focus dark border/underline / page | 13.022:1 |
| Generic error red boundary / page; red / focused yellow outline | 4.571:1; 4.146:1 |

The yellow highlight alone is only **1.103:1 against the page**, retained as a
diagnostic, not counted as a qualifying AA indicator. The official dark edge/
underline (or red error-summary border) supplies the contrasting portion; no
vendor CSS was changed. The summary focus is explicitly programmatic, not a
claim of automatic error focus. Measurements include actual saved values and
the existing generic fault rendered by submitting a pre-birth date, and all
current text/hints/controls at 320, 768 and 1280px. The reviewed right-aligned
select SVG is separate from the text background; its fill is measured too.
Other background images or element opacity fail the measurement helper rather
than silently assuming a flat background. Native date-control internals and
OS popup rendering are not author-styled and are not independently audited.
This is current-interface contrast evidence, not full WCAG certification,
AAA SC 2.4.13 focus-area evidence, or later full-flow completion.

Also executed `verify-architecture` (40 approved scenario observation matches
against retained upstream evidence and four persistence checks, no failures or
skips) and `verify-preview` (three real-browser save/reload passes, no failures
or skips). Fresh upstream executions and complete parity remain later tasks.
Build logs show zero warnings/errors. No business rules or approved inputs changed.

Initial failures are retained: default local Production did not serve build-time
CSS (repaired by enabling static web assets); the test initially expected the
wrong blue (corrected to the reviewed official primary token `#1b365d`); and a
single Tab inside a native date input moved between date segments rather than
to the select (test now uses Shift+Tab from Save after circuit readiness).
These are not erased or counted as final success. No comprehensive accessibility
or original Windows/Oracle/PostgreSQL verification is claimed.

The supplied missing-current-interface-contrast finding is recorded and
addressed in `validator-findings.md`. Two contrast-test development failures
are retained: the flat-background guard initially rejected the reviewed select
SVG, and an outline assertion assumed the wrong computed shorthand order.
Both were repaired in the test, without changing NHSW assets or business rules.
The external plan is unchanged; no checkbox or stage completion is recorded.
