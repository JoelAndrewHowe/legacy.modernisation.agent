# Task 3 — synthetic fixture and scenario contract (v1)

## Status and provenance

`fixtures.json` and `scenarios.json` are **authored inputs, not executed reference evidence**. Task 4 must supply an independently inspectable extracted-legacy harness and compare observations against these expectations. No original Windows/Oracle execution, clinical accuracy, human approval, or completed task is claimed. No validator findings were supplied for this execution; previous findings remain recorded in gaps.md SF-G17/SF-G18.

The Task-3 pre-start source/input/immutable-approval gate passed. Retained evidence is `task-3-prestart-source-citation-results.json`, `task-3-prestart-source-citation-verification.log`, `task-3-prestart-gate-results.json` and its three hash/revision logs. The input manifest and approved baseline revisions are repeated in fixtures.json. The original 40 KD03 scenarios and all baseline artifacts remain untouched; these 53 SF scenarios extend rather than replace them.

`define-fixtures.py` records literal provenance and deterministic row construction, **not legacy logic**. It exclusively creates the two new contract files and refuses existing destinations. Expectations are hand-authored from behaviour.md, with references to its existing `source-citations.json` records. Those IDs link previously verified original-source spans; they are not new inline document bindings or a claim that this contract is one of the three Task-2 citation documents. `validate-fixture-contract.py` checks schema, provenance and fixture/expectation consistency only. Its positive check count is not a reference-scenario pass count.

All identifying values are invented. SYN-NHS strings are intentionally nonvalid synthetic NHS-number field values, not real/checksummed NHS numbers or internal client identifiers. Code/name pairs, addresses, alerts, dates and result histories are deliberately artificial. The 23 patient-101 results are stored read-back/query inputs, not 23 valid submissions or a typical KD03 history. Equal-date rows bypass insertion deliberately; baseline duplicate/repeat rules remain unchanged. Their repeat booleans are stored inputs, not a new recomputation rule. Another patient and unsupported KDP/non-KDP contacts are independent sentinels. The first history input contains mixed patients and unsorted dates: do not pre-filter it in the fixture loader.

The fixture author has documented Organisation as an invented authority concept only. **Health-board concept confirmation and Health board wording remain unresolved with the product owner** (SF-G04). Organisation remains the label until that decision; no synthetic real health board has been asserted.

## Resolution and observation protocol

- Load fixtures and scenarios from the same directory, with schemaVersion 1. Fail on missing/unknown fields required by an operation, invalid references, duplicate scenario IDs, empty scenarios or missing groups. Every scenario is required. Unknown operation, absent runtime prerequisite or unhandled adaptation is a failure, never a skip.
- Each scenario runs from a fresh deep copy of inputs. `patient` selects a patient variant by key. `repositoryPatients` is the exact synthetic repository membership for that summary scenario (variants selected/missing/alert represent the same ID and must not be combined into one repository). Apply `patientOverrides` to that selected graph before retrieval. `authorityLocations` references the top-level lookup array; `authorityLocationsOverride` replaces it, including an explicitly empty list. No other variant is implicitly in the repository.
- `history` resolves an entire stored array. `reverseInput` reverses that whole array before the service call, never the observed output. `ClientId` supplies the requested patient. `scope=all-KDP` retains the source service predicate; `scope=KD03` adds the **explicit slice adapter** after source retrieval, not a claim that the legacy service only retrieved KD03.
- `clock` substitutes the single AgeResolver DateTime.Now site. Dates are wall-clock ISO timestamps without timezone conversion; use Gregorian/en-GB for the explicit `dd-MMM-yyyy` formatting observation. Death threshold precedence and all source age branches are retained. Do not use birthday-adjusted age. Missing Oracle Lookups.Age is not implemented by this contract.
- `expected` is a recursive subset of the observed object: every specified key must exist and match, including null versus empty versus dash, exact spaces, booleans and numeric values. Additional keys are permitted for inspection but do not excuse missing expected ones. Lists are exact and ordered **except** the explicit unordered-ID comparators below. Do not compare only counts or stringify unlike types into equality.
- `idsUnordered` compares the complete multiset of observed result IDs (including cardinality); `excludedIds` asserts each ID is absent. `orderedDateGroups` partitions every observed row into consecutive equal-date groups. Compare exact descending group dates and each group's complete ID multiset and cardinality. Never compare order inside a tie group. Counts must equal the complete observation count. SF-036 and SF-039 intentionally accept any permutation of IDs 1001–1003 within the first group. Recorded date and result ID are **not legacy order keys**.
- `ordering-contract` inspects the complete original `GetKdpResults` method at verified citation C022. It must report the actual ordering expression keys and absence of a tie key, not return hard-coded fixture expectations. Task 4 should bind the extracted method to that source span. SF-038 is structural source evidence in addition to the runtime date-order/tie-membership cases.
- The resource observations below are identity/argument objects, not strings generated by invented localised formats. A resource double may retain tokens and arguments; it may not pretend missing prose or punctuation was recovered.

## Operation boundaries

| Operation | Source-backed extraction / declared adaptation | Expected observations |
| --- | --- | --- |
| summary | Requested-child GetClientSummary/map; StandardNameResolver, AddressResolver, AgeResolver, CurrentStatusResolver, centre/authority lookup, ShowAlert, bounded web-summary display conditions | Fullname, NhsNumber, birth date/controlled formatting, AgeString/display/label, symbolic enum/status requests, FullAddress, School resource arguments, Organisation, ChildAlerts, ShowAlert and status-alert resource/date arguments as specified |
| name | StandardNameResolver expression | Exact concatenated value, including trailing separator |
| address | AddressResolver (not AddressModel.FullAddress) | Exact five-line/postcode assembly and trimming |
| span-text | Only null/empty/nonempty StaticSpan text branches; no DateTime-MinValue or HTML/UI execution claim | Exact text and leaveBlankIfNull behaviour |
| age | Supplied AgeResolver with injected Now | Exact AgeString; threshold death overrides Now |
| alert-setup | ShowAlert plus supplied markup/query setup predicate | Boolean conditions only, not actual dialogs/focus/events |
| results | Source service patient/ExamType.Kdp filter, complete delegate descending date expression and disclosed KD03 adapter | Count, date groups, selected-patient ID membership/exclusions |
| ordering-contract | Read-only inspection of the C022 bound complete method | One ExaminationDate descending key, no equal-date tie key |
| physical-values | Source physical lookup applied independently to each saved nullable field | Raw 1/2/3 or null and corresponding choice identity/text; no invented gender rejection |
| facets | Source nullable reason, stored repeat and physical values; seed-authored display predicates only | Recorded/Not examined, Initial/Repeat, Has concern, and no persisted aggregate status |

For `summary`, nonempty status observes `{resolver: CurrentStatusText, arguments: [rawCode]}`; absent status returns empty without lookup. GENDER member selection uses supplied enum 0/1/2/9; EnumResolver's actual rendered prose remains unavailable. `School` is either source absent-centre dash or `{resource: CodeDescriptionFormat, arguments: [code, linkedNameOrNull]}`. This does **not** assert the missing format is `code, name`; Organisation independently uses the actual String.Join separator.

Named status/centre tokens represent missing source constants and do not recover numeric codes. SYN_ACTIVE is an invented nontrigger. The web view's literal `7` is tested separately; it is not silently equated with the missing stillbirth constant. SF-020/022–024 assert the exact status-specific resource identities and dates, with DateFormatStandard as a symbolic nested formatting step before the message resource receives the date text. Task 4 must retain that nested call order. ChildAlerts preserve their original list order; each has CommunityIndexHeading and ChildAlerts(resource, text) arguments when observing markup. Query `showAlerts=false` suppresses setup only, not the model's ShowAlert or text.

`Has concern` is explicitly **intentional display/filter semantics**, not an extracted aggregate clinical status. For the KD03 slice all five fields Heart, Hips, Eyes, Testes and PhysicalGeneral are applicable; true iff any has raw value 2. Null is absent, never silently 3. Social/family fields (including DomesticViolenceConcern), severity and stored aggregate status are excluded. SF-053 retains the approved no-invented-gender-restriction quirk. Facet operations must observe their read-only input unchanged; `persistedAggregateStatus=false` means no aggregate property is added or persisted, not a new status column holding false.

## Coverage and future target data

| Seed group | Stable scenario IDs |
| --- | --- |
| G01 full mapping/formatting | SF-001, SF-003 |
| G02 missing/separators | SF-002–008 |
| G03 clock/death/status | SF-009–020 |
| G04 alerts/status/no-alert | SF-001–002, SF-020–026 |
| G05 school/Organisation | SF-001, SF-027–032 |
| G06 patient isolation | SF-001, SF-033–037, SF-040 |
| G07 zero/one/multiple | SF-034–037 |
| G08 descending dates | SF-036, SF-039 |
| G09 unspecified equal-date order | SF-036, SF-038–039 |
| G10 reason/repeat/physical | SF-041–053 |

Histories.many contains exactly 23 selected-patient KD03 rows, plus 3 sentinels. It supports three future default-10 pages, two locations, two examiners, both saved reason and repeat states, every physical raw value and null, a social-only false-concern example, inclusive contact-date boundaries 2025-02-06 and 2025-02-28, equal contact dates and an equal recorded-date pair. Recorded date/ID sorting, filters, page counts, URL handling, UI labels, routed details and bilingual state are **future Refactor tests, not implemented or executed here**. Those test expectations must be explicitly identified as seed-authorised differences rather than smuggled into Convert parity.

Task 4 still must document actual doubles/extraction, execute all 53 scenarios with positive passes, zero failures and zero skips, emit per-scenario observations, and preserve the approved 40-scenario contract. Task 6 must bind these contracts, authoring/validation source and evidence, excluding all interpreter caches. Limitations and unresolved human decisions in gaps.md remain in force.
