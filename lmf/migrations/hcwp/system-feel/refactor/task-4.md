# Task 4 — URL-backed history, grouped details and synthetic volume

Scope: the fourth plan item only. The factory run plan is deliberately unchanged.
Validator finding: the prior status region headed “Some URL values were ignored”
and its browser assertion contradicted approved Characterise decision 2. Restored
the NHSW error summary headed **Invalid filters**, with alert semantics, a labelled
heading and links to the focusable filter heading. The human-approved decision is
unchanged. Browser checks now assert the summary, linked focus target, invalid
and unavailable tokens, invalid page/size defaults, retained valid selections,
excessive-page clamping and absence of an error summary on valid URLs.
Unrelated working-tree changes and all approved iteration-001/Characterise/Convert
inputs are preserved. `verify-task-2` passed before implementation in
`evidence/task-4-prestart/`: current approval and immutable-input checks, bound
53/53 Convert observations, 34 shared application-boundary scenarios, 43 query
checks, 4 persistence checks and the 40 approved recording regressions.

## Implementation and observable rules

- `ResultsUrlState` owns URL decoding/encoding outside Razor. Repeated `state`,
  `repeat`, `finding`, `location` and `examiner` keys provide OR within a category;
  the existing query service applies AND across categories before count/paging.
  `from` and `to` use inclusive ISO calendar dates. Selected-patient lookup choices
  come through the application query, never the store in a component.
- The GET form applies filters and page size together and omits `page`, resetting
  to page 1. Sizes are 10, 25, 50 (default 10). Pagination links retain filters;
  the current page is announced with `aria-current`. Cards are the readable list
  alternative to a wide table and label every required overview value.
- Invalid/unavailable known filter values are ignored and surfaced in the
  **Invalid filters** error summary, as required by approved decision 2.
  Numeric enum values are not accepted. Duplicate values are deduplicated with
  a notice. Invalid dates are ignored; reversed ranges discard both boundaries
  with a notice. Empty date inputs mean no boundary. Invalid/nonpositive/overflow
  page values default to 1; unsupported sizes default to 10. Unknown query keys
  are ignored and never re-emitted (including attempted patient/return URL keys).
- The query clamps excessive pages to the nearest valid page, or page 1 for an
  empty result. The visible notice explains clamping; the original URL remains
  unchanged on initial load, while subsequent paging/detail links use the resolved
  page. Filters never mutate records. The count, active-filter summary, clear-all
  action and explicit empty state remain available with zero matches.
- Detail links carry only validated list query state. Return links are constructed
  as local `/results` URLs, not arbitrary supplied return destinations. Reload,
  query-only navigation and detail-return restore the list query. Missing and
  other-patient keys retain the identical safe not-found outcome.
- `ResultDisplay.Groups` assigns every iteration-001 recording field exactly once
  across contact, measurements, physical, child/family, location/professional and
  metadata groups. Missing values are explicit; unknown lookup descriptions use
  `Description unavailable`. No technical key is clinical content. The existing
  bounded BMI display calculation is shared unchanged with recording. Withdrawal
  is a command, not a persisted result field: details honestly state that it is
  not stored and ordinary save does not update patient consent. No deviation
  values or other unsupported calculations are invented.

## Synthetic history provenance

`refactor/src/synthetic-history.json` is newly invented target-only input, not an
edit to an approved fixture. It seeds the existing EF InMemory graph only at web
startup. There are 23 patient-101 KD03 rows (8001–8023) and one patient-202 isolation
row (8024). Keys are persistence/route mechanisms only. Allocation advances above
the fixture keys. The two clinics and two professionals are explicitly named
`Synthetic demonstration clinic A/B` and `Synthetic professional X/Y`. All names,
dates, associations and assessments in this history are invented test data.
The approved synthetic patient-banner provenance remains in `task-3.md`.

The history deliberately contains repeated contact dates, equal recorded dates,
missing recorded dates, recorded/not-examined, initial/repeat and all three physical
values. January 2–3, 2025 is an inclusive six-row date-boundary example. Two locations
and two examiners support combinations. The last isolation row remains in storage
but cannot enter selected-patient results/details. **This volume is not a claim of
clinically typical KD03 history.** It is an intentional presentation/test fixture.
No aggregate clinical status is added.

Existing isolated recording browser checks explicitly set `DemoHistory=false` to
retain their original empty-store precondition; scenario seeding is unchanged.
The new `history.mjs` browser suite explicitly enables and tests the default
history. The ordinary local demonstration defaults to history enabled.

## Findings discovered and addressed

- Initial compile exposed Razor treating bare `@page` inside a loop as a directive;
  replaced with an explicit value expression.
- Initial parser checks exposed absent dictionary keys; absent categories now
  safely parse as empty selections. All 16 history checks pass after the fix.
- Chromium exposed a prerender/hydration race resetting edited controls. Filter
  controls now remain disabled until the first interactive render; native GET
  submissions still carry the full filter state. Runtime prerequisites are
  mandatory; this is not a no-JavaScript demonstration.
- Chromium exposed same-route query changes not refreshing component parameters.
  The results component now subscribes to navigation changes and unsubscribes on
  disposal, refreshing via the query boundary.
- Pagination introduces another current-page marker; the existing shell browser
  assertion is now scoped to primary navigation without weakening its check.

Failed browser attempts are retained in `evidence/task-4-browser*` (original,
recheck, debug and stable). `task-4-browser-fixed` passes 7/7 after the above fixes.
Development build/check logs are retained under `evidence/task-4-development`.

## Additional validator findings — NHSW controls and task-scoped evidence

Recorded and addressed all three supplied findings:

1. Unstyled filters omitted documented NHSW structures and cramped native controls
   wrapped date labels at 320px. Adapted pinned checkbox item/input/adjacent-label,
   fieldset/legend, form-group, label, input and select markup in `Results.razor`.
   Explicit IDs associate each checkbox label; date boundaries occupy separate
   stacked groups. Clinical wording, OR/AND filtering and GET URL state are unchanged.
2. Adjoining pagination links lacked numbered-pagination/current-item treatment.
   Added pinned nav/list/item/number-link and previous/next/title classes, with
   current-item styling alongside `aria-current`. Browser checks assert three list
   items and distinct rendered current-page background; URL state remains intact.
3. Inherited link focus did not verify the new controls. `browser/history.mjs` now
   traverses all 15 controls in native Tab order at 320 and 1280px, toggles every
   checkbox with Space, adjusts/restores both dates with arrows, changes page size
   with arrows and submits with Enter. Each focused control has a screenshot and
   measured styles. `contrast.mjs` measures actual checkbox label pseudo-elements
   (boundary, checked tick and focused dark edge), plus date/select text, boundaries,
   select arrow and dark focus edges against their backgrounds. No native input
   opacity is mistaken for visible checkbox rendering. Control rectangles and page
   overflow are asserted at both widths. Native OS popup internals are not audited.

The pinned checkout was verified as `043d882318918e2a4e8847e16fc3bfe694973c08`;
reviewed example/source paths are recorded in `refactor/nhsw-provenance.md`.
No custom CSS, new library dependency or bilingual implementation is introduced.
The prior `task-4-validator-final` packet is preserved as
`task-4-validator-final-before-controls`; the new final packet binds these changes.
The plan item is deliberately not marked done.

## Repeatable checks and limitations

Run from `lmf/migrations/hcwp`:

```sh
system-feel/refactor/verify-task-4 --evidence-dir "$PWD/system-feel/refactor/evidence/task-4-validator-final"
```

This runs the prerequisite/approved regression/shared parity/query/persistence
checks through `verify-task-3`, plus its shell/banner/recording/alert/responsive/
contrast/focus checks, then 16 new history/URL/details checks and 8 task-scoped Chromium
flows, including control keyboard/focus/contrast at both widths. The validator rerun is retained in `evidence/task-4-validator-final/`, including
`browser/invalid-filters.png` and the supplied finding/resolution in `results.json`.
Initial validator reruns (`task-4-validator` and `task-4-validator-focus`) exposed
fragment-navigation focus loss. Error links now explicitly focus the filter heading
without route navigation; the browser asserts actual keyboard focus.
Earlier task-4 evidence is historical and does not establish the corrected error
summary behaviour. Evidence includes commands, timestamps, versions, screenshots, source and
evidence hashes. Empty, failed and skipped evidence is rejected. Earlier regression
execution also passed at `evidence/task-4-regression/` (including 7/7 shell browser
checks). This task does not claim the final slice verifier or bilingual completion.

Source parity remains the extracted-reference parity, not Windows/Oracle runtime
parity. URL filters, deterministic ties, paging, grouped details and volume are
approved target enhancements. Draft Welsh, complete translation inventory,
language/draft retention and expanded final accessibility gates are subsequent
plan items. The local synthetic, EF-in-memory, unverified PostgreSQL/production
and deferred production-scale performance limitations still apply.
