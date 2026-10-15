# Iteration 002: Implement the HCWP system experience

Status: Scope agreed through product-owner and architecture interview; ready to
use as the implementation seed. Characterise is the first assembly line and
must stop for revision-bound human approval before Convert begins.

## Outcome

Use the existing Legacy Modernisation Factory and the existing migrated HCWP
solution to turn the bounded KD03 demonstration into a recognisable NHS Wales
selected-patient workflow.

A user can see reliable patient context, browse and filter every recorded KD03
result, page through a longer history, inspect one result in human-readable
detail, and record another result. The shared shell and new product-authored
interface copy are available in English and draft Welsh.

This is an incremental migration slice, not a replacement application. Start
with the Characterise assembly line, retain iteration 001 and its approval as
an immutable baseline, and carry this slice through Characterise, Convert and
Refactor. Each line has its own evidence and boundary. Do not skip directly to
the desired interface.

## Vision alignment

This iteration must preserve `lmf/docs/vision.md` unchanged. Traceability to its
principles is part of the iteration evidence:

- **Behaviour is the specification:** characterise the supplied legacy patient
  summary and multi-result behaviour before changing the application.
- **Tests before translation:** no new legacy-derived logic enters Convert
  without passing executable reference scenarios.
- **Translate first, improve second:** Convert ports newly required legacy logic
  without introducing the routed web experience. Filters, pagination, NHSW
  presentation and bilingual interaction belong to Refactor and are identified
  as intentional presentation enhancements.
- **Incremental and shippable:** build on the existing migrated application and
  keep iteration-001 KD03 recording behaviour working throughout.
- **Evidence over assertion:** agents create artifacts; executable gates decide
  whether a line passes.
- **Humans decide:** Characterise stops for approval of the exact reviewed
  revision, including gaps and intentional differences.
- **Small, replaceable stations:** use the existing assembly-line definitions
  and stage-specific reviewers. Do not fold stage policy into application code.

The HCWP practice target is one migrated product built by LMF. It is not the LMF
product itself and does not narrow the factory's general vision.

## Existing solution and immutable baseline

Use, do not recreate, the existing solution under:

- `lmf/migrations/hcwp/refactor/src/`
- `lmf/migrations/hcwp/refactor/checks/`
- `lmf/migrations/hcwp/refactor/browser/`

Iteration 001 and its approved artifacts remain authoritative inputs:

- `lmf/iterations/001-characterise-and-migrate-hcwp.md`
- `lmf/migrations/hcwp/characterise/`
- `lmf/migrations/hcwp/approvals/characterise-approved.md`
- `lmf/migrations/hcwp/convert/`
- the iteration-001 parity and Refactor evidence

Do not overwrite, reinterpret or silently weaken iteration-001 scenarios,
approval, reference logic, conversion artifacts or reports. The existing 40
approved scenarios must still pass against the final application. A changed
iteration-001 input invalidates its existing evidence and is a blocker, not an
invitation to regenerate approval.

Keep iteration-002 artifacts separate beneath:

```text
lmf/migrations/hcwp/system-feel/
  characterise/
  approvals/
  convert/
  refactor/
```

Refactor may change the existing application and its checks in place; the
separate directory holds this slice's stage contracts, reports and evidence.

## Source and context inputs

Read all of these before planning:

1. `lmf/docs/vision.md`
2. this iteration document
3. `lmf/iterations/001-characterise-and-migrate-hcwp.md`
4. `example-code/patient-banner (pseudononymised).txt`
5. `example-code/HCWP Core (pseudonymised) - single file.txt`
6. iteration-001 approved Characterise artifacts and scenarios
7. the current Refactor source, checks, browser tests and limitations
8. `lmf/seeds/context/nhsw-component-library.md`
9. `lmf/migrations/hcwp/refactor/nhsw-provenance.md`

Record cryptographic identities for reviewed inputs. The two pseudonymised
source bundles and all demonstration fixtures are inputs only; never modify
them in place.

The patient-banner bundle supplies patient-summary retrieval, mappings,
formatting, status, school, organisation and alert behaviour. The HCWP bundle
supplies result retrieval and ordering. In particular,
`KdpExaminationDelegate.GetKdpResults` orders results by examination date
descending. The source defines no equal-date tie-break.

The NHSW context is target-design guidance, not evidence of legacy behaviour.
The current application is the baseline target to extend, not a substitute for
legacy reference evidence.

## Product boundary

The application continues to operate on an already-selected synthetic patient.
There is no patient search or patient switching in this iteration.

The supported clinical workflow remains KD03, the HCWP 6–8-week contact. Other
contact types must not be offered or accepted. All iteration-001 validation,
warnings, confirmations, calculations, repeat recalculation, persistence
read-back and patient isolation remain in force.

The product comprises three routed views in one selected-patient context:

1. **HCWP results** — filterable, paginated history.
2. **Result details** — complete read-only presentation of one saved result.
3. **Record result** — the existing add workflow presented as a dedicated view.

The DHCW/NHS Wales shell and patient banner remain visible and consistent on
all three views. Opening details and returning restores the result list state.

## NHS Wales shell

Use the already-pinned DHCW NHSW component library and its provenance rules.
Do not invent generic NHS branding, colours, typography, spacing, breakpoints
or an unreviewed logo.

The shared shell must include:

- skip link and correctly identified main-content target;
- DHCW/NHS Wales identity using reviewed, locally served assets;
- service name **Healthy Child Wales Programme**;
- a prominent **Demonstration — synthetic patient data** banner;
- primary navigation for **Patient summary** and **HCWP results**, with the
  active section programmatically and visually identified;
- standard page container, main wrapper and footer patterns;
- no unexpected external runtime requests.

This remains a local demonstration. The shell must not imply production
deployment, production assurance or use of real patient data.

## Patient banner

Display enough context to identify and safely distinguish the selected patient:

- full name;
- NHS number;
- date of birth and calculated age;
- sex;
- formatted address;
- current status;
- school;
- health board/organisation;
- visible child-alert text when present.

Do not display the internal client identifier. Use NHS number as the displayed
identifier. All names, addresses, NHS numbers, schools, organisations and
alerts in the demonstration must be explicitly synthetic and documented with
their provenance.

Characterise the legacy formatting and visibility rules, including missing
values, address assembly, age calculation, current status and `ShowAlert`.
Where the source says `Organisation`, the target may label the value **Health
board** only if Characterise confirms the fixture represents that concept; the
mapping and intentional wording choice must be recorded.

Excluded from this slice: remote-record decisions, default access, access
control, warning acknowledgement, patient search, GP, health visitor, practice,
treatment centre, examination centre, telephone and mobile display. Source
dependencies required to obtain included fields must still be mapped honestly.

An alert is prominent patient context, not a dismissible success message. The
normal demonstration may use a patient without an active alert, but executable
reference and presentation tests must exercise an alert-bearing synthetic
fixture and a no-alert fixture.

## Results overview

Show all saved KD03 results for the selected patient. The overview columns are:

- contact date;
- contact type/description;
- examination state;
- location;
- examiner;
- initial or repeat;
- recorded date;
- an accessible action to view details.

Do not show internal patient ID, result ID, measurement ID, `OriginalExamCode`
or raw lookup codes. Technical identifiers remain in persistence and parity
evidence. Use descriptions and human-readable values in the clinician-facing
interface.

### Status semantics

The legacy model does not define one overall clinical result status. Do not
persist or present a fabricated aggregate status.

The following presentation facets are permitted:

- **Recorded** / **Not examined**: derived from whether a saved
  reason-not-examined value is present.
- **Initial** / **Repeat**: the persisted repeat flag.
- **Satisfactory**, **Concern**, **Not assessed**: source-backed values of the
  applicable physical-assessment fields.
- **Has concern**: a display/filter predicate that is true when at least one
  applicable physical assessment has the legacy `Concern` value. It is not a
  stored clinical status.

Characterise the exact fields included in the `Has concern` predicate. Do not
extend it to social/family fields or infer severity.

### Filters

Provide filters for:

- recorded or not examined;
- initial or repeat;
- physical finding, including `Has concern`;
- inclusive contact-date range;
- location;
- examiner.

Filters combine with AND across categories and OR among multiple selected
values within a category. Filtering changes only the displayed query and never
the records. Show the filtered count, active-filter summary, clear-all action,
and an explicit no-results state.

Store filter state in the URL. It must survive browser reload, language change,
opening a detail view and returning. Invalid or unavailable URL filter values
must be ignored or reported safely without changing data; define and test the
chosen observable behaviour.

### Ordering and pagination

Filtering and pagination execute through the application/persistence boundary,
not by reading the in-memory store from the component and not solely by hiding
already-rendered rows.

- Apply filters before counting and paging.
- Default to 10 results per page.
- Offer page sizes 10, 25 and 50.
- Show a human-readable range and total, for example, “Showing 1–10 of 23
  results.”
- Provide accessible previous/next and page navigation with current-page state.
- Store page and page size in the URL.
- Changing a filter or page size resets to page 1.
- A page beyond the filtered result count resolves safely to a valid page or
  the empty state; specify and verify the selected behaviour.

Order by contact date descending, then recorded date descending, then internal
result ID descending. The last two keys are an approved intentional
presentation difference needed for stable pagination because the legacy source
leaves equal contact dates unordered. The internal ID is an ordering mechanism,
not a displayed field.

Create at least 23 clearly synthetic patient-101 results so three default pages
can be demonstrated. Cover recorded/not-examined, initial/repeat, all three
physical values, `Has concern`, at least two locations, at least two examiners,
date boundaries and equal contact dates. Keep another synthetic patient's
results in storage and prove they never appear. Document that this volume is a
test fixture, not a claim about clinically typical KD03 history.

## Result details

Present a saved result as read-only, human-readable groups:

- contact details;
- measurements and calculated display values where already supported;
- physical assessments;
- child and family information;
- location and professional;
- recording metadata.

Display every clinically meaningful saved field in the iteration-001 scope,
using descriptions rather than raw codes. Explicitly represent absent values;
do not silently omit a group in a way that could imply a negative result.

The detail route may use an internal result key, but the key must not be shown
as clinical content. A missing result or a result belonging to another patient
must produce a safe not-found outcome and reveal no other-patient information.
Editing and deletion are not offered.

## Record-result view

Move the existing add flow into its own route without changing approved
behaviour. Preserve:

- the complete KD03 field inventory;
- defaults and clearing behaviour;
- validation and aggregate errors;
- warning and confirmation behaviour;
- BMI and deviation calculations;
- rejection of unsupported contact types;
- fresh-context save/read-back;
- repeat recalculation and patient isolation.

After a successful save, provide an unambiguous confirmation and a route to the
saved detail or updated results history. The newly saved result must appear in
the correct ordered page and match persistence. Invalid or declined submissions
must not save.

## English and draft Welsh

Add an English/Welsh language switch to the shared shell. Translate all
product-authored interface copy introduced or owned by this application,
including navigation, banner labels, filters, table headings, pagination,
empty states, actions, detail-group headings and form labels.

Requirements:

- English is the fallback for a missing Welsh string.
- Language switching retains selected patient, filters, pagination and unsaved
  form state.
- The chosen language survives navigation and browser reload for the duration
  of the local demonstration using a documented mechanism.
- Maintain a complete, reviewable bilingual string inventory outside component
  markup; do not scatter hard-coded translations through Razor files.
- Correctly set the document language for the active language.
- Browser and accessibility checks run in both languages, including narrow
  layouts where Welsh strings may be longer.
- The interface or demonstration documentation states that Welsh wording is a
  draft awaiting professional Welsh-language review.

Do not claim an agent-generated translation is production-approved. The
original legacy warning/error prose remains unavailable: iteration 001 retained
resource identities. Do not invent or clinically translate missing messages.
Record them as gaps, use the existing honest fallback, and list every unresolved
resource in the translation review inventory.

## Assembly-line boundaries

### 1. Characterise — start here

Run the existing `characterise` assembly line. Work only in
`system-feel/characterise/` plus the factory's run plan. Do not modify
`refactor/src`, introduce routes, or implement the desired interface in this
line.

Produce at least:

- `behaviour.md`: source-backed patient-summary, multi-result, formatting,
  status, alert and ordering behaviour with original-file references;
- `dependencies.md`: services, DTOs, mappings, resolvers, lookup/persistence
  dependencies, existing migrated boundaries and excluded infrastructure;
- `gaps.md`: missing resources, ambiguous health-board naming, undefined
  equal-date order, unavailable UI behaviour, synthetic data and intentional
  target enhancements;
- `migration-plan.md`: small slices through Convert and Refactor without doing
  their work;
- `fixtures.json`: synthetic patient summaries and result histories, including
  alert/no-alert, missing values, other-patient isolation and page/filter data;
- `scenarios.json`: stable, executable expected observations;
- `reference/`: independently inspectable executable legacy-reference harness;
- `verify`: one command that executes every required reference scenario;
- machine-readable per-scenario observations and aggregate results with a
  positive pass count, zero failures and zero skips;
- `review.md`: exact inputs, hashes, adaptations, commands, results,
  limitations, intentional differences and human decisions;
- `review-files.sha256`: hashes for every file bound to approval.

Required Characterise scenario groups include:

1. patient summary mapping and formatting with all included values;
2. missing optional patient-summary values;
3. calculated age at a controlled clock and applicable deceased/status paths;
4. alert visibility with and without child alerts/status triggers;
5. school and organisation/health-board lookup formatting;
6. selected-patient isolation;
7. retrieval of zero, one and multiple KD03 results;
8. descending contact-date ordering;
9. explicit evidence that equal-date order is unspecified by the source;
10. source field values needed for recorded/not-examined, repeat and physical
    finding facets.

Reference evidence may use dependency doubles for unavailable EF6/Oracle/UI
infrastructure, but it must retain the source-backed rules under test and
document every adaptation. Evidence remains parity with extracted legacy logic,
not the original Windows/Oracle application.

Characterise is complete only when its artifacts exist, every required
scenario passes, all source references are checkable, and remaining gaps are
classified. Then stop. Do not change application code and do not create human
approval on the operator's behalf.

### Human approval gate

The operator reviews `system-feel/characterise/review.md`, source-backed
behaviour, fixtures, gaps, intentional differences and passing reference
evidence. Approval is stored in
`system-feel/approvals/characterise-approved.md` and must name the SHA-256 of
`review-files.sha256` plus the state “approved for progression to Convert”.

Any change to a bound source, fixture, scenario, reference file, reviewed gap or
target decision makes approval stale. Convert must mechanically reject absent
or stale approval. Awaiting approval is a successful pause, not a failed line.

### 2. Convert

Only after current approval, run the `convert` assembly line. Port newly needed
patient-summary and multi-result retrieval logic to modern .NET while retaining
legacy structure and behaviour. Use the approved fixtures and scenarios without
weakening them.

Convert must not add Blazor routes, NHSW presentation, filters, pagination,
bilingual UI or the deterministic tie-break. Those are approved target
enhancements for Refactor. Produce separate converted source, provenance,
adaptation documentation, executable parity observations and a report comparing
reference and conversion for every approved scenario.

### 3. Refactor

Only after Convert parity passes, run the `refactor` assembly line. Integrate
the converted capability into the existing application and implement the
agreed shell, patient banner, routed workflow, details, filters, pagination and
bilingual experience.

Preserve domain and application boundaries. Razor components must not query the
store directly, contain legacy business rules, or own translation dictionaries.
Use a query model/application service for filtered, ordered and paged results.
Keep persistence replaceable and compatible with the existing EF Core
in-memory demonstration; do not claim PostgreSQL compatibility.

The Refactor report must separate:

- source-parity behaviour;
- carried-forward iteration-001 behaviour;
- approved intentional presentation differences;
- new product-authored UX with no legacy parity claim.

## Acceptance examples

1. Given the iteration seed and existing HCWP target, the factory runs the
   Characterise line first, writes only slice-specific Characterise artifacts,
   executes reference scenarios and stops awaiting human approval.
2. Given absent or stale approval, Convert cannot start.
3. Given current approval, Convert ports only approved legacy-derived logic and
   all observations match the Characterise reference.
4. Given the final application, the shared DHCW/NHS Wales shell, synthetic-data
   banner and selected-patient banner appear on results, details and recording
   views.
5. Given the selected synthetic patient, the banner shows name, NHS number,
   birth date/age, sex, address, status, school and health board/organisation,
   but no internal client identifier.
6. Given an alert-bearing patient-summary fixture, the alert is prominent and
   accessible; given no alert, no empty alert container is announced.
7. Given at least 23 selected-patient results and other-patient rows, the first
   page shows 10 selected-patient results in the agreed stable order and no
   other-patient data.
8. Given results on equal contact dates, recorded date and then internal result
   ID produce deterministic order without displaying the ID.
9. Given filters from several categories, AND applies across categories, OR
   within a category, counts and ranges reflect the filtered query, and storage
   remains unchanged.
10. Given the `Has concern` filter, a result matches if any approved physical
    assessment is `Concern`; no aggregate status is saved.
11. Given an inclusive date range, results on both boundary dates are included.
12. Given a filter or page-size change while on a later page, the overview
    returns to page 1 and reports the correct filtered total.
13. Given result-list URL state, reload and detail-return restore filters, page
    and page size; invalid URL values fail safely.
14. Given a result detail request, all clinically meaningful iteration-001
    values appear in labelled groups with descriptions rather than raw codes or
    technical identifiers.
15. Given an unknown result or another patient's result ID, the application
    returns a safe not-found outcome without revealing data.
16. Given a valid new KD03 result, save, confirmation and fresh-context read-back
    succeed; the result appears at its correct list position and its details
    match persistence.
17. Given invalid input, a declined confirmation or an unsupported contact,
    nothing is saved and existing iteration-001 outcomes remain unchanged.
18. Given English or Welsh, the active document language and visible
    product-authored copy match the selection. Switching language preserves
    navigation, filters, pagination and an unsaved draft.
19. Given a missing Welsh string or unavailable legacy resource prose, the
    documented English fallback is used and the gap appears in the translation
    review inventory.
20. Given narrow and wide viewports and keyboard-only use, the banner, filters,
    table/list alternative, pagination, errors, confirmations and navigation
    remain readable, operable and visibly focused.
21. Given the completed slice, all iteration-001 approved scenarios and the new
    reference/conversion/refactor suites pass with positive counts, zero
    failures and zero skips.
22. Given the final evidence, reports state the extracted-reference,
    synthetic-data, draft-Welsh, EF-in-memory, local-demo and unverified
    PostgreSQL/production limitations.

## Verification and evidence

The final gate must execute, not merely describe:

- exact Characterise reference scenarios;
- exact reference-versus-Convert comparisons;
- applicable reference/Convert/Refactor comparisons;
- all 40 iteration-001 approved regression scenarios;
- application unit/integration tests for patient isolation, query semantics,
  stable ordering, paging bounds and not-found behaviour;
- fresh-context persistence checks;
- build and configured format/style checks;
- a real Chromium flow in English and Welsh;
- narrow and wide responsive layouts;
- keyboard order and visible focus;
- accessible names, headings, landmarks, active navigation and table/pagination
  semantics;
- patient alert announcement;
- filter labels, active summary and empty state;
- error-summary links and form associations;
- language retention, URL-state retention and unsaved-draft retention;
- rendered contrast using the existing evidence approach;
- local asset checksums and absence of unexpected external requests.

Missing browser/runtime prerequisites fail the gate; they are never converted
to skips. Retain exact commands, tool/browser versions, timestamps, source
hashes, per-scenario observations, screenshots for important states and
machine-readable aggregate results.

Extend the existing checks rather than replacing them with a second unrelated
test stack. At minimum, the completed Refactor must still pass from
`lmf/migrations/hcwp`:

```sh
refactor/run-approved-scenarios
refactor/verify-gate
```

Add one documented `system-feel/refactor/verify` entry point that aggregates the
new slice checks and refuses empty, failed or skipped evidence.

## Explicit exclusions

- Patient search, patient switching and patient creation.
- Authentication, authorisation, remote-record access and access control.
- Production patient data or production deployment.
- Editing or deleting results.
- Contact types other than KD03.
- Appointment and recall processing.
- GP, health visitor, practice, treatment centre, examination centre, telephone
  and mobile presentation.
- A persisted or clinically asserted aggregate result status.
- Professionally approved Welsh translation; this iteration produces a draft
  and review inventory.
- Recovery or invention of unavailable legacy localised warning/error prose.
- Oracle connectivity, PostgreSQL/Azure deployment or database migration.
- Proof of PostgreSQL compatibility or production-scale performance.

Pagination itself is included. Performance/load testing beyond deterministic
query and paging behaviour is deferred and must be recorded as such.

## Factory execution

Use the existing target and assembly-line configuration. From the repository
root, start only Characterise:

```sh
bin/factory --run hcwp-system-feel-characterise \
  --target lmf/migrations/hcwp \
  --line characterise \
  --seed lmf/iterations/002-implement-system-feel.md \
  --attempts 6
```

The target has unrelated and possibly uncommitted work. Before every task,
inspect the working tree, preserve user changes and restrict edits to files
required by this iteration. A task is not allowed to modify iteration-001
approved artifacts merely because they are inside the same target.

The Characterise planner must split work into small evidence-producing tasks
and finish at the approval pause. Do not launch Convert or Refactor in the same
run. After approval, use distinct run names and their matching assembly lines:

```text
hcwp-system-feel-convert   / convert
hcwp-system-feel-refactor  / refactor
```

The same seed remains the product contract, but each run obeys only its named
stage section and prerequisites. Do not use a successful agent-review loop as a
substitute for the mechanical checks or revision-bound human approval described
above.

## Completion

Iteration 002 is complete only when all three lines have passed their stated
gates, the routed bilingual experience is present in the existing application,
all old and new executable evidence passes, and limitations are accurately
reported. Completing Characterise alone is the first milestone, not completion
of the iteration.

Stop immediately after the first Characterise run reaches its human approval
gate and present the exact review packet, revision and unresolved decisions to
the product owner.
