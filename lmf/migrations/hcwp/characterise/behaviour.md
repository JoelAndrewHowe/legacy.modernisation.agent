# KD03 add-and-read-back behaviour

## Scope and evidence

Source: repository-root `example-code/HCWP Core (pseudonymised) - single file.txt`, SHA-256 `f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2`. References below identify the original files by bundle banner and method, not invented standalone files. This is source characterisation, not executed evidence. Subsequent verification may establish **parity with extracted legacy logic**, not with the original Windows/Oracle system.

The selected patient is synthetic and already selected. Include new `KD03` recording, validation, warning/confirmation responses, saved values and persistence read-back, and selected-patient KD03 repeat recalculation. Exclude search, edits/deletes, scheduled-result entry, appointment management, recalls and real infrastructure. KD03 is the 6–8-week contact, not necessarily the first programme contact. The demonstration must offer only KD03 and reject other submissions without saving: this is the agreed scope boundary, not a rule enforced by the legacy save validator.

### Source reference key

| Key (bundle file) | Original path |
| --- | --- |
| UI (3) | `HLX.Net2008/Data Input (HLX - Child Health)/Examination-Unscheduled/Kdp/ucHLXKdpExaminationResult.cs` |
| Screen (4) | `HLX.Net2008/Data Input (HLX - Child Health)/Examination-Unscheduled/Kdp/ucHLXKdpExaminations.cs` |
| Parent (5) | `Orvex.ViewModels/KdpExaminationDelegate.cs` |
| Result (6) | `Orvex.ViewModels/KdpExaminationResultDelegate.cs` |
| TO (14) | `Orvex.Contracts/HLX.BusinessTier/Common/Model/BusinessModel/Examinations/KdpExaminationResultTO.cs` |
| Dates (23) | `Orvex.Contracts/HLX.BusinessTier/Common/Util/DateCalculation.cs` |
| Choices (24) | `Orvex.Contracts/HLX.BusinessTier/Common/Util/LookupsUtility.cs` |
| Validator (27) | `Orvex.Contracts/HLX.BusinessTier/Common/Validator/BusinessValidator/Examinations/KdpExaminationValidator.cs` |
| Display (37) | `Orvex.Business/AutoMapper/Mapping/KdpProfile.cs` |
| Measurements (42) | `Orvex.Business/Services/Business/ChildMeasurementsService.cs` |
| CRUD (43) | `Orvex.Business/Services/Business/Examinations/ExaminationsCrudManager.cs` |
| Service (44) | `Orvex.Business/Services/Business/Examinations/KdpExaminationService.cs` |
| Lookups (46) | `Orvex.Business/Services/Business/Lookups/LookupService.cs` |

## Entry and defaults

Parent `GetKdpResults` reads the patient through Service `GetKdpExamination` and orders results newest first. Service filters by patient ID and examination-description type `ExamType.Kdp` (10), not merely the KD prefix. Patient context includes birth, optional death, sex, existing results, and preschool medical consent: category 2, type 11, result `Y`.

Parent `AddNewKdpResult` warns with `NoConsentMessage` / `ChildHasNoConsentPrompt` if consent is absent, but still creates a draft. Draft defaults: selected `ClientId`, result ID 0, `ResultEnteredDate = DateTime.Now`, origin 2 (Unscheduled), reschedule `N`, three measurement-declined flags `N`, change events enabled. Code is initially null, contact date is the TO default `DateTime.MinValue`; no default physical assessment or mandatory measurement is established. TO `WithdrawConsent` and `IsRepeat` default false.

Legacy appointment prefill is identified but excluded from the bounded demonstration: Service `GetKdpOutstandingAppointments` returns past/due outstanding KD appointments newest first; Parent asks in turn and first affirmative response copies code, date and scheduled origin. The reference should use an explicitly empty outstanding-appointment fixture, not claim parity for this branch.

Result `Populate` sets context, resets lazy measurement/schedule data and updates descriptions. `ValidateAndSetExamCode` sets `ExamCodeValidated` before the guarded code setter. For a changed code, the setter clears hidden contact-specific fields: KD03 retains physical assessments but clears development/further-development, DSK scores and RSK scores/completed. Populating an existing TO does not itself clear hidden fields. KD03 is not a DSK, RSK or 15/27-month contact.

## Field and available-value inventory

Null/blank is distinct from a recorded `N`. Values below describe source-offered choices, not an exhaustive server-side whitelist. Unless stated otherwise, save does not require an individual field or check choice membership. TO holds raw values; Service mappings write them by convention and explicit renaming.

| Fields | Values/defaults and observable rules | Source |
| --- | --- | --- |
| `ClientId`, result/measurement IDs, `Sector` | Patient-owned; IDs generated on insertion; sector database-computed in mappings, unavailable trigger behaviour | Parent `AddNewKdpResult`; Service `InsertKdpExaminationResult`; mappings files 54/57 |
| `ExaminationCode`, `ExamDescription`, `OriginalExamCode` | Demonstration KD03 only; description from lookup; original code set on read-back; legacy lookup offers all KDP exams | Result `Is6To8WeekContact`, `UpdateExamDescription`; Service `ConfigureMappings`; Lookups `LookupExamDescriptions` |
| `ExaminationDate`, `ResultEnteredDate` | Date required on save; draft entry time is now; date setter retains existing hours/minutes/seconds when changing calendar day | Result `ExaminationDate`; TO; Validator `ValidateOnSave` |
| `Origin` | 1 Scheduled, 2 Unscheduled, 3 Movement In, 4 Amendment, 5 Not Known; default 2; enum also contains 6 Out of Pathway but offered dictionary does not | Choices `ExaminationOrigin()`; Parent |
| `ReasonNotExamined` | null/empty or SQL codes 1 Was not brought; 2 Unwell or uncooperative child; 3 Examination refused; 4 Parent / Carer not present; 5 Not required | `EXAM_NOT_EXAMINED_REASON.sql` (92); Lookups `LookupExamNotExaminedReasonKdp` selects non-null KDP descriptions |
| `Consent`, `OnwardReferralsMade` | `Y`, `N`, null; consent entry is not the patient's preschool medical consent | Choices `YesNo`; UI `Populate`; TO |
| `Reschedule`, `WithdrawConsent` | reschedule `N` by default; `Y` requires a reason; withdrawal boolean exists but ordinary add/save does not update patient consent | Parent; Validator; Service ordinary vs `SaveScheduledResult` |
| `LocationType`, `LocationCode`, `LocationName` | null type or 5 GP Surgery, 2 Clinic, 1 School, 17 At Home, 6 Hospital, 18 Telephone Contact, 22 Virtual; code/name lookup-derived; changing type clears code/name/cache | `KDP_LOCATION_TYPES.sql` (93); Result setters and `GetLocationList`; Lookups |
| `ExaminerCategory`, `ExaminerType`, `ExaminerHcpCode`, `ExaminerName` | category lookup (KDP examiner primary key), staff type and HCP code separate; category change clears type/code/name/cache; blank HCP clears name/category; used HCP supplies name/type | Result setters, `PopulateHcpDetails`, `GetExaminerList`; Lookups `GetExaminers`, `GetExaminerLookupWithPrimaryKeyAsCode` |
| `Height`, `Weight`, `HeadCircumference` | Nullable decimals; height in cm/weight in kg as BMI arithmetic establishes; exclusive ranges below; measurements need not all be supplied | Result properties; Validator; Measurements `CalculateBmi` |
| `HeightMeasurementDeclined`, `WeightMeasurementDeclined`, `HeadMeasurementDeclined` | `Y`/`N`; delegate boolean setters clear corresponding value on both true and false, raise required-state notification; required flags are UI hints, not save mandates | Result `Is*Declined`, `Is*Required`; Parent defaults; tests file 91 |
| `ReceivingBoostSchemeService`, `LookedAfterChild`, `OnChildProtectionRegister` | `Y`, `N`, `U` (Not Known), null in entry UI | Choices `YesNoUnknown`; UI `Populate` |
| `EvidenceOfXgm` | 1 XGM observed, 2 XGM disclosed, 3 XGM not present, 4 Not examined, null | Choices `EvidenceOfXgm` |
| `DomesticViolenceConcern` | 1 assessment completed, 2 assessment not completed, null | Choices `DomesticViolenceConcern` |
| `CoreComponent` (delegate `CoreComponentOffered`) | 1 Universal, 2 Enhanced, 3 Enhanced Plus, 4 Intensive, 5 Intensive Plus; entry dictionary has no blank row; TO nullable and save does not mandate it | Choices `CoreComponentOffered`; Result; Validator |
| `Heart`, `Hips`, `Eyes`, `Testes`, `PhysicalGeneral` | Each nullable byte: 1 Satisfactory, 2 Concern, 3 Not assessed, null; applicable to KD03; not individually mandatory | Choices `PhysicalAssessment6To8Weeks`; Result `Is6To8WeekContact`, `ClearDataFromHiddenFields`; UI `Populate`; TO |
| RSK/development/DSK | Not applicable to KD03; cleared on changing code to KD03, not independently rejected by save | Result `ClearDataFromHiddenFields`; Validator `NoResults` |
| BMI | Derived, not an entered field in TO; nullable unless both height and weight present; not explicitly written by ordinary service measurement mapping | Result `Bmi`; Measurements; Service `ConfigureMappings` |

Testes carries a boys label in `Orvex.Contracts/HLX.BusinessTier/Common/DomainModel/KdpExamResultModel.cs` (10), but supplied delegate contains no gender-specific applicability/rejection rule. No designer/bindings are supplied: do not invent mandatory male-only logic or claim observed Windows visibility.

## Validation paths and observations

Message resources/fault implementations are missing. Resource identifiers below are observable semantic identities; exact original/localised prose and titles are unverified. Field failures send `NonFatalErrorEncountered` and return false; warnings use `WarningNotificationMessage`; confirmations use `YesNoConfirmationRequiredMessage` with an explicit response. They do not all behave like save validation.

### Code/date field validation

Result `ValidateAndSetExamCode` calls, in order:
1. Validator `ValidateExamCodeForDate`: another ID with exact same code and calendar day is an error `KdpResultAlreadyEnteredMessage` / `DuplicateExamCodePrompt` (time-of-day ignored).
2. `ValidateNewExamCode`: nonempty code absent from supplied lookup is an error `KdpInvalidExamCodeMessage` / `InvalidExamCodePrompt`. Empty code passes field validation, but fails save.
3. For a changed code, `ValidateExamCodeForDuplicates`: same code on any other result yields confirmation `KdpDuplicateExamCodeMessage` / `DuplicateExamCodePrompt`. No response returns false, retaining old code; yes permits setting code. Warning exception exits the try block; it is not a save error.
4. If an existing nonempty code is changing, a separate code-change confirmation can reject the change. New KD03 drafts have no old code.

Result `ValidateExaminationDate` calls date validation then same-code/day validation, then age warning. Date validation rejects future calendar dates (`FutureExamDateMessage`), timestamps before birth (`ExamDateBeforeDobMessage`), or after death (`ExamDateAfterDeathMessage`), all with `InvalidExamDatePrompt`. Birth/death comparisons use full DateTime, not just the day; equality passes. Duplicate result excludes the same result ID. Parent save catches service faults as a nonfatal save error and returns false.

### Measurements and warnings

Validator field height/weight accept null or strictly `0 < value < 1000`; otherwise `InvalidHeightMessage`/`InvalidHeightPrompt` or weight equivalents. Head field validation requires strictly `0 < value < 100`: <=0 produces `HeadCircumferenceMinusNumberErrorMessage`, >=100 produces `HeadCircumferenceInvalidFormatMessage`, with `InvalidHeadCircumferencePrompt`. Its additional 0–1000 check is unreachable for accepted values.

**Contradiction retained:** save validates nullable head circumference solely as `0 < value < 1000`, using `InvalidHeadCircumferenceMessage`. Thus 100 or 150 fails the head field path but is accepted by save if other fields are valid. Null skips field validation in UI and is accepted by save. Do not choose a single harmonised range.

Result `CheckDeviations` runs for valid nonnull height/weight and a non-MinValue current contact date. Measurements `GetExpectedRanges` selects bands by whole-day age and gender, groups by measurement type, sets lower = minimum of band `Upper`, upper = maximum of band `Lower` (preserve these apparently reversed names). Only strict interior values with lower < upper avoid `OutsideExpectedRangeMessage`; equal bounds/endpoints or missing-type default zero range warn. Warning does not reject recording. No head-deviation call occurs in supplied delegate.

BMI = `Math.Round(weight / ((height / 100) * (height / 100)), 2)` using decimal arithmetic/default midpoint-to-even rounding, capped above at 99.99. Result height/weight setters notify BMI changes; outside prescribed bounds (strictly below/above, endpoints accepted) gives `BmiOutsidePrescribedRangeMessage` / `OutsidePrescribedRangePrompt` and `IsBmiOutsideRange = true` (UI colours label red). Zero height can divide by zero before field validation if setters are called in an unfortunate order: actual control sequencing unverified, not a new mandatory rule.

Age: Dates `WeeksBetween` uses integer-truncated total days divided by 7. Result `CheckAgeWithinScheduleRange` obtains Service schedule data. Service takes first active row matching code, with no patient/schedule ID filter despite contract commentary; null minimum converts to 0, null maximum to double.MaxValue, absent row yields null. If a range exists and maximum >0, strict below/above warns `KdpContactGivenBeforeMinAge` or `KdpContactGivenAfterMaxAge`; endpoints accepted and save still allowed. No enforced 6–8-week window is inferred from the name.

Location/examiner field helpers accept blank codes; nonblank codes validate against lookup lists. Unknown location gives `InvalidLocationCodeMessage`; unknown HCP `InvalidHcpCodeMessage`; unused HCP (`UsedCode == N`) `UnusedExaminerCodeMessage`. Missing type/category or lookup fault sends an error but leaves a null list, and validators then return true: preserve this permissive quirk, not a save guarantee. HCP name population assumes a list has been loaded, another unavailable-control-order limitation. Numeric descriptors validate UI positions, not stored codes (location 1–7, examiner 1–12, reason 1–5); unparseable text passes. Constructor marks examiner categories other than 18,19,26,28 as invalid for the custom UI; save does not enforce that list.

### Save validation (ordered, aggregated)

Validator `ValidateOnSave` appends numbered errors in this order, then throws one `ValidationFault` / `ValidationErrorsPrompt` if any:

1. Missing/empty code: `NoExamCodeMessage` (no code-lookup membership check here).
2. Missing date (exact MinValue): `NoExamDateMessage`; otherwise first applicable future / before-birth / after-death error.
3. Height exclusive 0–1000 (null accepted).
4. Weight exclusive 0–1000 (null accepted).
5. Head exclusive 0–1000 (null accepted, unlike field path).
6. If reason absent: reschedule `Y` errors `RescheduleOnlyIfNotExaminedMessage`; then no counted results errors `NoResultsEnteredMessage`.
7. If reason present and counted results exist: `ResultsRecordedButNotExamined`.
8. Other ID, exact same code and calendar day: `KdpResultAlreadyEnteredMessage`.

`NoResults` counts height, weight, head, domestic violence, evidence, heart, hips, eyes, testes; nonempty receiving-boost, looked-after, child-protection, onward-referral strings; also RSK/development/DSK fields although these are hidden for KD03. `PhysicalGeneral`, `CoreComponent`, consent, origin, location, examiner, declined flags and withdrawal are **not** counted. Therefore physical-general-only fails with no reason, yet physical general may accompany a reason without the conflicting-results error. `N`/`U` shared result strings count as recorded results. Declining all measurements alone is not sufficient. Save does not require consent `Y`, complete physical assessment, any specific measurement, or a prescribed age window.

## Save and persistence read-back

Service `SaveKdpExaminationResult` validates before insertion, allocates examination sequence ID, inserts `ChildExamination`, `ChildExaminationGiven`, `ChildExaminationKdp` sharing ID. It creates a `ChildMeasurement` and allocates its ID only when height/weight/head has a value and measurement ID <=0. Failed validation reaches neither insertion nor commit; included unsuccessful submissions must observe no new row and unchanged repeats. Non-validation infrastructure failures/Oracle atomicity are not characterised as verified here.

`ConfigureMappings` preserves patient association and raw code/date/origin, given metadata/refusal flags, KDP fields (including all five physical assessments), and measurements. Reason string converts to nullable byte on write; empty becomes null. Most same-name properties use AutoMapper convention; boost service name maps to `ReceivingBoostScheme`. Ordinary save does not implement withdrawal-of-patient-consent; that exists only in excluded scheduled save. Insert retains draft entry timestamp; edit path overwrites it with now but is excluded.

After insertion, CRUD `UpdateRepeatFlags` loads patient results with code prefix (KD), groups by **exact** code, and compares full DateTime. Every minimum-date KD03 row is `N`; all strictly later rows `Y`. Equal earliest timestamps all remain non-repeat (no ID tie-break). Date ordering, tie behaviour, exact-code grouping, patient isolation and idempotence are the bounded required evidence; duplicate-day insertion is separately prohibited, so ties belong to existing fixtures. No further speculative repeat mutation tests are required. Unsupported-type effects of the prefix-wide algorithm are outside this slice.

The full service then updates appointment statuses and clears produced recalls before commit. Those calls are excluded dependency boundaries, so the bounded reference is not full save-service parity.

Read saved data through Service `GetKdpExaminationResult` or fresh `GetKdpExamination`, not an echo of the submitted TO. `GetKdpResultTo` maps parent, given, KDP then optional single measurement into one TO; measurement date maps over examination date (equal in ordinary insert). It generates a lock and clears change tracking. More than one measurement is unsupported by `SingleOrDefault`. Read-back includes IDs, selected patient, code/original code, date/entry date, origin, metadata/refusal flags, shared result fields, physical fields, measurement values and recalculated repeat status. Description/name values require synthetic lookup/navigation fixtures. BMI is recomputed by the delegate; do not claim service persisted it.

Screen `SaveChanges` repopulates from service on successful parent save. Parent read sorts descending by date; equal-date display order has no explicit tie-break. Result `ResultTabText` adds a recall flag for repeat; `UpdateExamDescription` and `ExamDescription` getter can both append RecallText for an original-code repeat with null lock, a possible double suffix. Exact resource text/control rendering is unverified.

## Observable examples to carry into later scenarios

These are source-derived examples, not executed scenarios or stable scenario IDs yet:

- A selected synthetic patient's KD03 with valid date, shared fields and physical assessments saves and returns those raw values via a new persistence read; a measurement row exists iff one measurement supplied.
- Missing code/date and invalid measurements return ordered save errors and save nothing.
- A valid-date heart-only record is sufficient; consent-only, core-only, general-only and declined-only records are insufficient without a not-examined reason.
- Reason 1 with no counted results, reschedule Y and optional physical general saves; reason 1 with heart=1 fails.
- Head=150 fails field validation but passes direct save with otherwise valid input; 1000 fails save.
- A later different-day KD03 triggers a duplicate-code confirmation: decline retains draft code and saves nothing in that submission; accept allows recording. Same-day duplicate errors, even if time differs.
- No patient consent, age outside an explicitly synthetic schedule, deviation endpoint, and BMI outside explicitly synthetic options warn rather than become save mandates.
- New later KD03 reads as repeat; new earlier KD03 demotes the old earliest; other patient's results unchanged. Existing earliest ties remain N; exact codes group separately; recalculation is idempotent.
- Unsupported contact submissions are rejected by the demonstration scope adapter without saving, explicitly separate from legacy validator behaviour.

Executable fixtures/scenarios/harness and results are later plan tasks; none have run in this task. See `dependencies.md` and `gaps.md` for evidence limits and review decisions.
