# KD03 dependency map

References use original bundle-file banners in `example-code/HCWP Core (pseudonymised) - single file.txt`. Full rule-source paths and method references are indexed in `behaviour.md`. No executable substitutions have been implemented yet; the proposed boundaries below must be recorded against actual files when the reference is built.

## Included path and boundaries

```text
Selected synthetic patient
  -> ucHLXKdpExaminations / ucHLXKdpExaminationResult (files 4 / 3)
  -> KdpExaminationDelegate (5), KdpExaminationResultDelegate (6)
     -> KdpExaminationValidator (27)
     -> IMessenger / messages (29, 32–35)
     -> ILookupService / LookupService (21 / 46)
     -> IChildMeasurementsService / ChildMeasurementsService (19 / 42)
     -> IKdpExaminationService / KdpExaminationService (20 / 44)
        -> AutoMapper + mappings / transfer objects
        -> IUnitOfWork, IRepository (31 / 30)
        -> insert parent + given + KDP + optional measurement
        -> ExaminationsCrudManager.UpdateRepeatFlags (43)
        -> [excluded appointment/recall calls]
        -> Commit
  -> fresh service read -> mapped result -> display
```

| Dependency | Source-backed responsibility | Reference boundary / evidence limitation |
| --- | --- | --- |
| Windows presentation | File 3 UI field Validating events cancel on false; dictionary dropdowns; BMI colour converter file 1; file 4 new/save/repopulate tabs | Headless adapter must invoke named delegate/validator paths explicitly, not pretend WinForms/Janus control event order is tested. Designers, binding definitions and custom controls missing. |
| Parent delegate | File 5 `GetKdpResults`, `AddNewKdpResult`, `Save`: patient association, defaults, consent warning, fault-to-message handling | Preserve included creation/save/read behaviour; use empty outstanding appointments to bound prefill. |
| Result delegate | File 6: field setters, applicability, validation/confirmations, BMI/deviation/age warnings, lookup handling | Retain logic wherever practical; track every extraction/compatibility change; no invented mandatory fields or fixed age limit. |
| Transfer objects / change tracking | File 14 result TO, file 15 `Orvex.Contracts/HLX.BusinessTier/Common/Model/BusinessModel/Examinations/KdpExaminationTO.cs`, file 11 `Orvex.Contracts/HLX.BusinessTier/Common/Model/AbstractTO.cs`, file 8 `Orvex.ViewModels/ViewModelBase.cs` | Dictionary defaults, events, lock generation, clean read-back; missing ITO/MonitoringList/validation support may require minimal compatibility shells. Preserve business-value observations; do not claim exhaustive identity/event/locking parity. |
| Validator | File 27 ordered checks, aggregated save errors, counted-results predicate | Must not replace business rules with a lookup/persistence double. Keep field/save head limits separate and omissions in `NoResults`. |
| Messenger / faults / resources | File 29 IMessenger; files 32–35 message containers; WCF FaultException catches | Deterministic recording messenger with supplied confirmation responses; fault classes, message bases and resources missing. Report resource keys and message category, not fabricated exact original prose/localisation. |
| Lookup service | File 46: all KDP descriptions, KDP examiner categories, location types/reasons, used/active HCP and locations | Reuse SQL seed choices from files 92/93; operational KD03 description, HCP and location rows synthetic. Stored-procedure results may be doubles, not invented validator rules. |
| Measurement service | File 42 BMI arithmetic/cap, prescribed BMI options, centile-band aggregation | Preserve arithmetic and range algorithm. Supply explicit synthetic options/bands by age/gender; live data and centile view unavailable. |
| Date/schedule | File 23 whole-day age; file 44 `GetAgeRangeFromExamSchedule`, file 41 `Orvex.Business/RepositoryExtensions.cs` active filtering | Schedule rows synthetic. Missing `IActiveDateRange`/`ActiveDateRange` implementation leaves exact active-date endpoint semantics unverified; select an unambiguously active fixture. Do not implement patient-specific schedule selection from misleading contract comment. |
| Save/read service | File 44 validation before insert, optional measurement, repeat recalculation, commit and TO mapping | Preserve bounded method extraction; excluded side effects explicitly removed/no-op. Fresh read must reconstruct from persisted entities, not return draft. No claim of full save-service parity. |
| AutoMapper | File 44 `ConfigureMappings`, file 37 display `KdpProfile`; files 38/40 bool/string resolvers; file 36 `Orvex.Business/AutoMapper/AutoMapperExtensions.cs`, file 48 `Orvex.Business/Util/EfMapperExtensions.cs`, file 26 `Orvex.Contracts/HLX.BusinessTier/Common/Util/UnitOfWorkTransferObjectExtensions.cs` | Explicit mapping or compatible library may be needed. Inventory substitutions; same-name convention mappings are business data semantics, not arbitrary echo copying. Display dictionary/YesNo/BMI resolvers partly absent. |
| IDs | File 47 `Orvex.Business/UnitOfWorkSequenceExtensions.cs`: CHILD_EXAMINATION_ID_SEQ and CHILD_MEASUREMENT_ID_SEQ | Deterministic synthetic sequence provider; distinct IDs, parent links and measurement presence observable. Not Oracle sequence timing/rollback parity. |
| Time | Parent uses DateTime.Now; validator DateTime.Today; Result schedule active query now | Pin a synthetic clock consistently when executing; document exact sites adapted and values. Service injected GetCurrentDateTime is used for excluded scheduled withdrawal, not all clocks. |

## Persistence schema and read relationships

Original data files: `Orvex.Data/EntityFrameworkRepository.cs` (49), `Orvex.Data/EntityFrameworkUnitOfWork.cs` (50), `Orvex.Data/HlxContext.cs` (51). Context disables initialisation, uses APPDATA1, non-Unicode strings, uppercase-underscore conventions; existing-connection constructor disables lazy loading/proxies. Repository local tracking supports repeat recalculation and navigation repair; commit calls EF6 SaveChanges. A reference repository double must distinguish committed storage from draft values and support selected-patient reads. It cannot prove Oracle constraints, transactional failure behaviour or concurrency.

| Entity / table | Original mapping and model | Important relationships / constraints |
| --- | --- | --- |
| CHILD_EXAMINATION | `Orvex.Data/Mappings/CHILD_EXAMINATIONMap.cs` (54); `Orvex.Model/CHILD_EXAMINATION.cs` (70) | Explicit sequence ID; required patient and exam-description FKs, code max 4; sector required max 2 computed; repeat string max 1. |
| CHILD_EXAMINATION_GIVEN | `Orvex.Data/Mappings/CHILD_EXAMINATION_GIVENMap.cs` (52); `Orvex.Model/CHILD_EXAMINATION_GIVEN.cs` (71) | Shared parent ID; contact date/entry time, origin, optional reason, location composite FK, HCP composite FK, examiner category; required one-character reschedule/refusal flags. |
| CHILD_EXAMINATION_KDP | `Orvex.Data/Mappings/CHILD_EXAMINATION_KDPMap.cs` (53); `Orvex.Model/CHILD_EXAMINATION_KDP.cs` (72) | Shared given ID; nullable raw physical bytes, shared result flags max 1, core component; no gender or mandatory-assessment constraint established. |
| CHILD_MEASUREMENT | `Orvex.Data/Mappings/CHILD_MEASUREMENTMap.cs` (57); `Orvex.Model/CHILD_MEASUREMENT.cs` (75) | Separate sequence ID, patient FK, optional exam FK, date; height precision (4,1), weight (6,3), head/BMI precision unspecified; sector computed. Read path expects zero/one measurement. |
| CHILD_GENERAL / CONSENTS | mappings 55/60; models 73/78 under corresponding `Orvex.Data/Mappings/` and `Orvex.Model/` names | Selected patient DOB/death/sex, medical preschool consent. Synthetic context only; no production data. |
| Lookup/context tables | mappings 56,61–65,67–69; models 74,79–83,85–86,89 | CHILD_LOCATIONS, V_DEVIATIONS_CENTILES, EXAM_NOT_EXAMINED_REASON, EXAMINATION_DESCRIPTIONS, EXAMINER, HEALTH_CARE_PROFESSIONALS, KDP_LOCATION_TYPES, PRESCHOOL_SCHEDULE_EXAMS, SYSTEM_GENERAL_OPTIONS. |

`KDP_Schema.sql` (94) reconstructs rather than dumps live schema. Do not treat inferred precision, placeholder lengths, illustrative constraints or omitted triggers as verified database behaviour. An in-memory reference does not prove EF6/Oracle storage rounding (height/weight), empty-string coercion, collation or server constraints.

## Explicitly excluded dependencies

- File 43 appointment-status updates and produced-recall clearing; `HLX_APPOINTMENT`, `CHILD_PRESCHOOL_RECALL`, `CHILD_SCHOOL_RECALL` mappings 66/58/59 and models 84/76/77. Full ordinary save calls these; removing/no-oping them is an intentional reference adaptation, not parity for those effects.
- File 7 `Orvex.ViewModels/KdpScheduledResultDelegate.cs` and Service scheduled save/withdrawal: appointment state checks, consent mutation and next-contact details are not ordinary KD03 add.
- File 45 `Orvex.Business/Services/Business/Examinations/PreschoolsManager.cs`: Oracle PRESCHOOLEXAMS procedures, recall/appointment runs, Oracle notifications, global session/sector and clinical next-due calculation.
- Oracle.ManagedDataAccess, original Windows environment, .NET Framework 4.5.1 runtime, WCF hosting, Janus/HLX controls, original AutoMapper startup configuration, EF6 Oracle provider, triggers, live production lookup/centile data, authentication/session infrastructure.
- Azure, PostgreSQL, production deployment, existing-database migration. No PostgreSQL compatibility is implied.

The independently inspectable harness, shared fixtures/scenarios and executable verification are pending later tasks. Document actual doubles and compilability adaptations there before any parity claim.
