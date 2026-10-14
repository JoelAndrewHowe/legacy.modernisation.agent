# System-feel migration plan — proposed downstream work

## Boundary and authority

This is Task 5 planning, not execution of Convert or Refactor, stage completion, or human approval. No validator findings were supplied with this invocation; earlier findings SF-G17–SF-G23 remain recorded in `gaps.md`. The next work is the Task-6 review packet, then a successful pause awaiting revision-bound human approval. Do not launch either downstream line in this Characterise run.

Repository-root-relative authority:

- `lmf/iterations/002-implement-system-feel.md` is the product/stage contract; `lmf/docs/vision.md` remains unchanged.
- `lmf/migrations/hcwp/system-feel/characterise/` (below, **slice Characterise**) contains `behaviour.md`, `dependencies.md`, `gaps.md`, `source-citations.json`, `fixtures.json`, `scenarios.json`, `fixture-scenario-contract.md` and `reference/README.md`. These define the source-backed rules, exact source spans, scenario protocol and actual extraction adaptations. This plan references those checked claims rather than introducing new legacy rules or citation bindings.
- Task-1 manifest revision: `3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a`. Exact reviewed membership and individual digests are in `input-membership.json` and `input-files.sha256`, not HEAD.
- Immutable iteration-001 `lmf/migrations/hcwp/characterise/`, `approvals/characterise-approved.md`, `convert/` and inventoried parity/Refactor evidence remain authoritative. Its approval binds review-manifest SHA-256 `5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699`. Preserve all KD03-001–040 expectations and Q01–Q13 quirks, including validator versus parent fault identity, field/save limits, clearing, repeats and read mapping. Do not regenerate baseline evidence to clear drift.

## Stop and approval validation

Task 6 must assemble `review.md` and `review-files.sha256`, rerun integrity/citations/reference gates with fresh evidence prefixes, report the manifest digest and disclose all remaining decisions. No such packet or approval is created by this task.

Only the human operator may create `lmf/migrations/hcwp/system-feel/approvals/characterise-approved.md`, naming the SHA-256 of the exact slice `review-files.sha256` and the state **approved for progression to Convert**. A successful agent/validator loop is not approval.

Future Convert must mechanically, before any translation:

1. Require that approval file, exact state and a single unambiguous bound revision; reject missing/malformed/unapproved records.
2. Hash the slice review manifest and compare with the approval revision, then verify every bound file using its documented working directory. Reject missing files, digest mismatches and unsafe paths. Check reviewed input membership as well as hashes; an omitted or newly added input is not silently accepted.
3. Independently validate the iteration-001 approval revision above and run the existing read-only `sha256sum --check characterise/review-files.sha256` from `lmf/migrations/hcwp`. Recheck the Task-1 input snapshot and original-bundle identities. Do not invoke a baseline evidence writer as the integrity check.
4. Rerun the approved reference and compare exact scenario IDs, counts and contract hashes to the reviewed packet; retain fresh evidence separately. Unknown operations, absent prerequisites, zero cases, failures, skips or omissions block progression.
5. Repeat prerequisite checks at the end of the line. A changed bound source, fixture, scenario, reference file, gap or decision makes approval stale; return to Characterise review and human reapproval, never silently rebind it.

A future Refactor run must additionally require accepted Convert evidence bound to the same Characterise revision and converted source hashes. No route or design work starts on partial Convert parity. Use distinct future run names `hcwp-system-feel-convert` / `hcwp-system-feel-refactor` with the existing matching assembly lines; do not change station policy in application code.

## Small Convert slices — literal translation only

Write new conversion artifacts beneath `lmf/migrations/hcwp/system-feel/convert/`. Do not replace iteration-001 conversion or edit the current target application during Convert. Each slice adds provenance, explicit infrastructure substitutions and per-scenario reference-versus-converted observations; earlier passing slices accumulate. The complete line exit gate still runs all 53 SF definitions, not just the subset touched last.

| Slice | Literal capability and boundary | Required parity evidence |
| --- | --- | --- |
| C1 — selected-patient summary | Port the inspected service/DTO/mapping graph and name/address/missing-value resolvers, preserving selected ClientId retrieval. Retain shared retrieval dependencies behind excluded fields without adding their presentation. | G01/G02/G06: SF-001–008 plus applicable isolation cases; exact separators, null/empty/dash distinctions and NHS-number versus internal-ID separation. |
| C2 — age, status, school, Organisation and alerts | Port the remaining summary rules using the reviewed clock, symbolic constants/resource arguments and declared mapping adaptations. Do not manufacture missing resolver prose or Oracle age semantics. | All G03–G05 scenarios (SF-009–032 and summary cases), including death/status precedence, literal status path, alert/no-alert, lookup absence and symbolic nested formatting observations. |
| C3 — persisted history and facets | Port selected-patient/all-KDP retrieval and delegate contact-date ordering, retain the disclosed KD03 adapter and nullable saved physical/reason/repeat values. Keep seed-authored read-only facets separately labelled, not a newly discovered clinical aggregate. | G06–G10: SF-033–053 plus summary isolation. Zero/one/many; complete descending date groups and unordered tie multisets; all five physical fields, null versus Not assessed, social-only false concern and unchanged inputs. |

Before exit, execute **SF-001–SF-053 in full** on independent reference and converted runtimes using identical approved fixtures and strict observation projections. Emit 53 per-runtime outcomes and 53 comparisons, positive passes, zero failures/skips/missing/extra IDs. Preserve type/null/cardinality checks and unordered tie comparison; do not sort ties to hide discrepancies or send expected values into runtime logic. Record structural equal-date-order evidence separately from runtime observations. No clinical rule, expectation or comparator is weakened to accommodate a port.

Convert must not add routes, NHSW shell/banner design, filters, URL state, pagination, recorded-date/ID tie keys or bilingual UI. Runtime/API substitutions are individually documented with the retained rule and unproved infrastructure behaviour. Keep the original 40 recording scenarios authoritative; run applicable carried-forward regression checks in isolated slice evidence, without overwriting baseline reports. A discovered conflict blocks the affected slice for owner resolution.

## Small Refactor slices — integrate only after full Convert parity

Integrate into existing `lmf/migrations/hcwp/refactor/src/`, checks and browser suite only in a later authorised Refactor run. Keep this iteration's contracts/reports/evidence beneath `lmf/migrations/hcwp/system-feel/refactor/`. Extend the existing test stack, do not substitute a second application. Each slice leaves the existing KD03 recording workflow working and reruns applicable parity plus all 40 recording regressions.

| Slice | Integration and intentional enhancement | Added acceptance / rollback boundary |
| --- | --- | --- |
| R1 — application/query foundation | Place summary orchestration and result-query contracts in Application; implement replaceable persistence adapters with EF Core InMemory. Retain Domain rules and Presentation/Rules delegates. Components receive models, never access the store or own clinical rules. | Compare integrated summary/history projections to C1–C3. Fresh-context reads, selected-patient sentinels, no mutation by queries. Keep legacy date-only parity projection distinct from the later paged product order. |
| R2 — shell, patient context and routes | Shared pinned NHSW shell, local reviewed assets, synthetic-data banner, skip/main/footer/navigation semantics; context on results, details and record routes. Patient summary navigation stays within the selected patient, no search/switching. | Full/missing/alert/no-alert banner variants, no displayed ClientId. Organisation label until SF-G04 evidence and product-owner wording approval exist. Unknown/other-patient detail keys produce safe indistinguishable not-found outcomes. No edit/delete actions. |
| R3 — result detail and existing record view | Read-only labelled groups cover every clinically meaningful iteration-001 saved field with explicit absent values and descriptions, not raw codes/technical IDs. Move existing add flow to its own route; keep validation, clearing, calculations, warnings and confirmations unchanged. | Field-inventory coverage, valid save and fresh-context detail match; invalid/declined/unsupported submissions save nothing. Successful save has confirmation and navigation to saved detail/history. Preserve repeats and other-patient storage; saved row appears at its correct ordered position. |
| R4 — query filters and deterministic paging | Application/persistence applies selected-patient KD03 scope, AND across categories / OR within, inclusive dates, filters before count/page. Add 10/25/50 paging, ranges and accessible controls; order contact date, recorded date, result ID descending. Has concern uses applicable Heart/Hips/Eyes/Testes/PhysicalGeneral Concern only, never social/family fields or persisted aggregate status. | Use the 23-row synthetic history and sentinels: 10/10/3 default pages, complete no-duplicate/no-loss membership, equal-date/recorded-date ties, date boundaries, combined filters, count/range/empty state, unchanged storage and fresh queries rather than hiding rendered rows. |
| R5 — URL and navigation state | URL represents filters/page/page size; detail-return and reload restore list state. Clear-all and filter/page-size changes reset page 1. | Specify invalid/unavailable URL values and out-of-range page behaviour before implementation, with safe deterministic outcomes and no data changes. Test state across reload, detail-return and save navigation. |
| R6 — English/draft Welsh and final assurance | External reviewable string inventory, English missing-string fallback, active document language and shared switch. Preserve selected patient, URL state and unsaved draft across language changes. | Both languages, wide/narrow layouts, local-demo language persistence, missing-string fallback, draft-Welsh disclaimer, no invented/translated missing clinical resource prose; inventory every unresolved resource from resource-reconciliation.json. |

R2–R6 are seed-authorised product/presentation enhancements, **not legacy UI parity**. Refactor reports must separate (1) extracted-source parity, (2) carried-forward iteration-001 rules, (3) intentional differences and (4) new product-authored UX. Apply ordering enhancements only to product queries; the legacy parity adapter must still demonstrate date-only ordering with unspecified equal-date order.

## Decisions before the affected implementation

Do not treat this plan as an owner decision. Carry SF-G01–SF-G16 into the review packet, including:

- **SF-G04:** fixture author confirms whether invented Organisation represents a health board; product owner explicitly decides wording. Until both exist, retain Organisation. Characterise review may disclose this unresolved decision; implementing Health board may not bypass it.
- **SF-G01/G02/G03/G06:** reviewer acknowledges symbolic resource/status/enum/format, controlled-clock and graph/UI adaptations. Original message prose, Oracle age and UI events remain unavailable; no missing prose is recovered by porting.
- **SF-G11/G12:** product owner/application engineer specify invalid URL values and page bounds in the later Refactor contract and tests before coding. Proposed safe policy for review: ignore invalid/unavailable filter tokens and report them nonclinically, use page 1/default 10 for invalid numeric parameters, clamp a positive excessive page to the last nonempty page (or page 1 for zero rows). This is a proposal, not an approved legacy rule.
- **SF-G13:** product owner documents local-demo language persistence (proposal: browser-local preference with English default); translation lead reviews draft Welsh. Unsaved draft retention must be tested without storing clinical production data. No professional translation approval is claimed.
- **SF-G07/G08/G16:** all identifying values and histories stay explicitly synthetic; the 23-result volume is a test fixture, not typical clinical history. No copied operational patient data or real health-board claim.

Any new source/baseline conflict requires a named clinical/product owner decision and renewed affected evidence/approval, not silent repair of Q01–Q13 or a broadened Has concern predicate.

## Accumulating verification and evidence gates

These are future exit criteria, not checks executed by this planning task:

1. **Parity:** every approved SF definition executes on reference/Convert and applicable Refactor adapters with bound contracts, strict per-scenario comparisons, positive counts and zero failures/skips/omissions. Product tie keys/filters/routes/language use separate enhancement assertions, not modified legacy expectations.
2. **Baseline regression:** all unchanged KD03-001–040 pass against the final application, including aggregate errors, decline clearing, unsupported contact rejection, BMI/deviation, repeat recalculation, persistence read-back and isolation. Run `refactor/run-approved-scenarios` and `refactor/verify-gate` from `lmf/migrations/hcwp`; these are future baseline-required commands, not invoked here because current runners write baseline evidence. Future implementation must preserve historical baseline evidence and route/archive new outputs into distinct slice destinations before execution, documenting any runner adaptation without changing approved artifacts.
3. **Application/persistence:** selected-patient scope at every query/detail/save boundary, filters/count/page ordering, stable tie keys, inclusive ranges, invalid URL/page choices, no query mutation, complete detail fields and fresh-context persistence. No component-only paging or draft echo.
4. **Build/style:** current application build plus configured format/style checks; record actual commands, scope and versions rather than claiming every possible analyser ran.
5. **Real Chromium:** English and Welsh result/detail/record journeys, alert/no-alert, valid/invalid/declined saves, confirmations, filter combinations/empty state, paging and reload/detail-return/language/unsaved-draft retention. Wide and narrow viewports; keyboard order/visible focus, labels/error-summary links, headings/landmarks, active navigation, table/pagination semantics, alert announcement and rendered contrast. Retain important-state screenshots and machine-readable checks. Missing browser/runtime prerequisites fail, never skip.
6. **Assets:** local pinned NHSW asset checksums/provenance and no unexpected external runtime requests; no silent guidance-pin upgrade, generic branding or unreviewed logo.
7. **Single slice gate:** add future `system-feel/refactor/verify` aggregating new checks and baseline-required gates. Reject stale evidence/source hashes, empty counts, missing groups, failures, skips and absent prerequisites; no success based solely on a historical report.

Every future gate retains exact working directories/commands, start/end timestamps, exit codes, tool/.NET/browser versions, input/source/contract hashes, actual/expected per-scenario observations and aggregate counts. Use fresh write-once destinations; preserve failed attempts. Exclude compiler bin/obj, every __pycache__ and *.py[cod] from review binding. Preserve SF-G17/SF-G18 retention rules and required explicit prefixes; historical Task-4 patches are not current source review (SF-G23).

## Limitations and present execution

Evidence remains parity with extracted rules and declared adaptations, not execution of original Windows/Oracle/EF6 or full legacy infrastructure. Retain local-demo, synthetic-data, draft-Welsh, process-lifetime EF InMemory and unverified PostgreSQL/production limitations. No patient search/switching/creation, editing/deletion, other contacts, appointment/recall, access-control/remote-record workflow, excluded demographic displays, Oracle/Azure/database migration or production deployment. Performance/load beyond deterministic query/paging is deferred; pagination itself is required.

Task-5 pre-start root command `PYTHONDONTWRITEBYTECODE=1 python3 lmf/migrations/hcwp/system-feel/characterise/verify-source-citations.py --evidence-prefix task-5-prestart` passed: 3 documents, 81/81 citations resolved, zero failures; 9/9 groups, 1499 input files, 184 directories, 2 symlinks and immutable approval passed. Exact timestamps, commands and logs are retained in `task-5-prestart-*`. No downstream scenario execution is claimed by this planning document. Final Task-5 recheck/evidence is recorded separately; Task 6 and human approval remain pending.
