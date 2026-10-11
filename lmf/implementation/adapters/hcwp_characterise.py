#!/usr/bin/env python3
"""Source-bound HCWP Characterise adapter. Runner appends a request path."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent


def sections(text):
    return {m[1].strip(): m[2].strip() + '\n' for m in re.finditer(
        r'>>> FILE \d+/94: (.*?)   \[.*?\]\n=+\n(.*?)<<< END FILE', text, re.S)}


def method(text, name):
    match = re.search(r'        (?:public|private) (?:static )?[^\n]+\b' + name + r'\([^\n]*\)\s*\{', text)
    if not match:
        raise ValueError('Missing extracted method: ' + name)
    start = text.index('{', match.start())
    depth = 1
    end = start + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[match.start():end]


def generate(request):
    if request['Stage'] != 'characterise':
        raise ValueError('HCWP adapter only implements Characterise; Convert/Refactor are not implemented.')
    source = Path(request['Source']).read_text()
    target = Path(request['Target']).read_text()
    if not all(word in target.lower() for word in ('blazor', 'in-memory')):
        raise ValueError('Supported target description must specify Blazor and in-memory storage.')
    files = sections(source)
    if len(files) != 94:
        raise ValueError('Expected the supplied 94-file HCWP bundle.')
    def find(suffix):
        return next((k, v) for k, v in files.items() if k.endswith(suffix))
    validator_path, validator = find('/KdpExaminationValidator.cs')
    dto_path, dto = find('/KdpExaminationResultTO.cs')
    delegate_path, delegate = find('/KdpExaminationResultDelegate.cs')
    bmi_path, bmi = find('/ChildMeasurementsService.cs')
    lifecycle_path, lifecycle = find('/KdpExaminationDelegate.cs')
    out = Path(request['OutputDirectory'])
    def put(name, content):
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    def js(name, value):
        put(name, json.dumps(value, indent=2) + '\n')
    # Retain complete validator, changing only ambient clock for repeatable examples.
    put('reference/KdpExaminationValidator.cs', validator.replace('DateTime.Today', 'ReferenceClock.Today'))
    props = re.findall(r'public\s+(string|long|decimal\?|byte\?|bool|DateTime\??)\s+(\w+)\s*\{', dto)
    if not props:
        raise ValueError('Cannot extract DTO property inventory.')
    resources = sorted((set(re.findall(r'\b\w+(?:Message|Prompt)\b', validator)) | set(re.findall(r'Resources\.Resources\.(\w+)', method(lifecycle, 'AddNewKdpResult') + method(lifecycle, 'ConfirmCancelChanges'))) | {'ResultsRecordedButNotExamined'}) - {
        'errorMessage', 'kdpInvalidHeightMessage', 'kdpInvalidWeightMessage', 'kdpInvalidHeadCircumferenceMessage'})
    put('reference/Compatibility.cs', '''// Generated infrastructure substitutions; no business validation here.
namespace Orvex.TransferObjects {
 public class KdpExaminationResultTO {
''' + '\n'.join(f'  public {t} {n} {{ get; set; }}' for t, n in props) + '''
  // TransferObjectBase lock token: storage only, no concurrency infrastructure.
  public string Lock { get; set; }
  public bool EnabledPropChangeEvents { get; set; }
  // Explicit change-tracking fixture; original TransferObjectBase/Windows events are not executed.
  public bool ChangedFixture;
  public bool hasChanged() => ChangedFixture;
 }
 public class LookupsSubTO { public string Code { get; set; } public string Description { get; set; } }
}
namespace Orvex.Resources { public static class Resources {
''' + '\n'.join(f' public const string {r} = "{r}";' for r in resources) + '''
}}
namespace Orvex.Messages.Faults {
 public class ValidationFault : System.Exception {
  public ValidationFault Detail => this;
  public string Title { get; set; }
  public ValidationFault(string message) : base(message) {}
  public static ValidationFault Default(string message, string title) => new(message) { Title = title };
 }
 public class ValidationWarningFault : System.Exception {
  public ValidationWarningFault Detail => this;
  public string Title { get; set; }
  public ValidationWarningFault(string message) : base(message) {}
  public static ValidationWarningFault Default(string message, string title) => new(message) { Title = title };
 }
}
namespace Orvex.Business.Validation { public static class ReferenceClock {
 public static System.DateTime Today = new(2025, 3, 1);
 public static System.DateTime Now = new(2025, 3, 1, 12, 0, 0);
}}
''')
    put('reference/ExtractedBmi.cs', '''using System;
public class ExtractedBmi {
 // Infrastructure double: records requests, returns explicitly synthetic ranges.
 public System.Collections.Generic.List<DateTime> RangeRequests = new();
 public System.Collections.Generic.List<RangeFixture> GetExpectedRanges(string gender, DateTime birth, DateTime date) {
  RangeRequests.Add(date);
  return new() { new("Height", 40, 60) };
 }
''' + method(bmi, 'CalculateBmi') + '\n}\n')
    # Retain age-warning branch verbatim; dependency fixture supplies the schedule.
    age = method(delegate, 'CheckAgeWithinScheduleRange').replace('private void', 'public void')
    put('reference/ExtractedAge.cs', '''using System;
using System.Collections.Generic;
public class ExtractedAge {
 public DateTime dateOfBirth;
 public string ExaminationCode = "KD03";
 public Lazy<Tuple<double,double>> recommendedAgeRangeInWeeks;
 public WarningSink Messenger = new();
 const string KdpContactGivenBeforeMinAge = "KdpContactGivenBeforeMinAge";
 const string KdpContactGivenAfterMaxAge = "KdpContactGivenAfterMaxAge";
 const string KdpResultsTitle = "KdpResultsTitle", WarningPrompt = "WarningPrompt";
''' + age + '''
}
public record WarningNotificationMessage(string Message, string Title, string Prompt);
public class WarningSink {
 public List<string> Warnings = new();
 public List<string> Errors = new();
 public List<string> Confirmations = new();
 public bool ConfirmationResponse;
 public void Send(YesNoConfirmationRequiredMessage value) { Confirmations.Add(value.Message); value.Response = ConfirmationResponse; }
 public void Send(NonFatalErrorEncountered value) => Errors.Add(value.Message);
 public void Send(WarningNotificationMessage value) => Warnings.Add(value.Message);
}
public static class DateExtensions {
 // Adaptation: demonstration weeks are elapsed days / 7; original extension is unavailable.
 public static double WeeksBetween(this DateTime birth, DateTime exam) => (exam-birth).TotalDays/7;
}
''')
    put('reference/Reference.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>disable</Nullable></PropertyGroup></Project>\n')
    start = delegate.index('        public decimal BmiLowerBound')
    last = re.search(r'        public decimal\? HeadCircumference\s*\{.*?\n        \}', delegate, re.S)
    members = delegate[start:last.end()]
    members += '\n' + '\n'.join(method(delegate, n).replace('private void', 'public void') for n in ('ValidateLocationCode', 'ValidateExaminerCode', 'CheckDeviations', 'CheckBmi'))
    date_property = re.search(r'        public DateTime ExaminationDate\s*\{.*?\n        \}', delegate, re.S).group()
    members += '\n' + date_property
    code_property = re.search(r'        public string ExaminationCode\s*\{.*?\n        \}', delegate, re.S).group()
    clearing = method(delegate, 'ClearDataFromHiddenFields')
    cleared_fields = re.findall(r'^            (\w+) = null;', clearing, re.M) + re.findall(r'^                (\w+) = null;', clearing, re.M)
    for name in cleared_fields:
        members += '\n' + re.search(r'        public [^\n]+ ' + name + r'\s*\{.*?\n        \}', delegate, re.S).group()
    members += '\n' + code_property + '\n' + clearing
    members += '\n' + method(delegate, 'UpdateExamDescription') + '\n' + method(delegate, 'ResetRecommendedAgeRange')
    members += '\n' + '\n'.join(line for line in delegate.splitlines() if re.search(r'(private readonly string\[\] examCode|public bool Is(?:15Or27Month|Rsk|6To8Week|Dsk)Contact =>)', line))
    members += '\n' + method(delegate, 'ResetDeviations').replace('ChildMeasurementsRange', 'RangeFixture')
    members += '\n' + method(delegate, 'Populate')
    members += '\n' + '\n'.join(method(delegate, n) for n in ('GetDropDownUiPositionNumber', 'PrependNumericsUiLocationTypeDescriptions', 'PrependNumericsUiExaminerDescriptions', 'PrependNumericsUiReasonNotExaminedDescriptions'))
    members += '\n' + re.search(r'        private class TypeCodePosition\s*\{.*?\n        \}', delegate, re.S).group()
    for name in ('Location', 'Examiner', 'ReasonNotExamined'):
        members += '\n' + re.search(r'        List<TypeCodePosition> ' + name + r'TypeCodePositions = .*?\n        \};', delegate, re.S).group()
    members += '\n' + '\n'.join(line for line in delegate.splitlines() if 'private const string DropDownCodeDescriptionFormat' in line)
    members += '\n' + method(delegate, 'ValidateAndSetExamCode').replace('FaultException<ValidationWarningFault>', 'ValidationWarningFault').replace('FaultException<ValidationFault>', 'ValidationFault')
    symbols = sorted(set(re.findall(r'\b\w+(?:Message|Prompt|Title)\b', members)) - {'warningMessage', 'WarningNotificationMessage'})
    constants = '\n'.join(f' const string {s} = "{s}";' for s in symbols)
    put('reference/ExtractedInteractions.cs', (ROOT / 'delegate-support.cs.txt').read_text().replace('__MEMBERS__', constants + '\n' + members))
    lifecycle_members = '\n'.join(method(lifecycle, n) for n in ('AddNewKdpResult', 'ConfirmCancelChanges', 'GetNewKdpExaminationResultDelegate'))
    lifecycle_members = lifecycle_members.replace('FaultException<ValidationWarningFault>', 'ValidationWarningFault').replace('DateTime.Now', 'ReferenceClock.Now')
    put('reference/ExtractedLifecycle.cs', (ROOT / 'lifecycle-support.cs.txt').read_text().replace('__MEMBERS__', lifecycle_members))
    put('reference/Program.cs', (ROOT / 'reference-driver.cs.txt').read_text())
    put('verify.py', (ROOT / 'verify_reference.py').read_text())
    fixtures = {'today': '2025-03-01', 'dateOfBirth': '2025-01-01', 'clientId': 1001,
                'gender': 'M', 'scheduleWeeks': [6, 8], 'existingResults': [],
                'origin': 'All patient, time, schedule and identifier values are invented demonstration fixtures, not production data.'}
    js('fixtures.json', fixtures)
    base = {'ClientId': 1001, 'ExaminationCode': 'KD03', 'ExaminationDate': '2025-02-19',
            'Heart': 1, 'Hips': 2, 'Eyes': 3, 'Testes': 1, 'PhysicalGeneral': 2,
            'Height': 55, 'Weight': 4.5, 'HeadCircumference': 38}
    scenarios = []
    def add(id, operation, data, errors=None, warnings=None, **extra):
        scenarios.append({'id': id, 'given': 'A selected synthetic patient and frozen clock',
                          'when': operation, 'input': data, 'then': {'errors': errors or [], 'warnings': warnings or [], **extra}})
    add('KD03-valid', 'save', base, saved=base)
    add('KD03-physical-optional', 'save', {**base, 'Heart': None, 'Hips': None, 'Eyes': None, 'Testes': None, 'PhysicalGeneral': None}, saved={**base, 'Heart': None, 'Hips': None, 'Eyes': None, 'Testes': None, 'PhysicalGeneral': None})
    add('KD03-empty', 'save', {'ExaminationCode': 'KD03', 'ExaminationDate': '2025-02-19'}, ['NoResultsEnteredMessage'])
    add('KD03-general-alone', 'save', {'ExaminationCode': 'KD03', 'ExaminationDate': '2025-02-19', 'PhysicalGeneral': 1}, ['NoResultsEnteredMessage'])
    for id, field, value, error in [('future', 'ExaminationDate', '2025-03-02', 'FutureExamDateMessage'), ('before-birth', 'ExaminationDate', '2024-12-31', 'ExamDateBeforeDobMessage'), ('height-zero', 'Height', 0, 'InvalidHeightMessage'), ('weight-boundary', 'Weight', 1000, 'InvalidWeightMessage'), ('head-save-boundary', 'HeadCircumference', 1000, 'InvalidHeadCircumferenceMessage'), ('reschedule', 'Reschedule', 'Y', 'RescheduleOnlyIfNotExaminedMessage'), ('not-examined-conflict', 'ReasonNotExamined', '1', 'ResultsRecordedButNotExamined')]:
        add('KD03-' + id, 'save', {**base, field: value}, [error])
    not_examined = {'ExaminationCode': 'KD03', 'ExaminationDate': '2025-02-19', 'ReasonNotExamined': '1', 'Reschedule': 'Y'}
    add('KD03-not-examined', 'save', not_examined, saved=not_examined)
    for value, error in [(0, 'HeadCircumferenceMinusNumberErrorMessage'), (100, 'HeadCircumferenceInvalidFormatMessage'), (999, 'HeadCircumferenceInvalidFormatMessage'), (38, None)]:
        add('KD03-head-field-' + str(value), 'head-field', {'HeadCircumference': value}, [error] if error else [])
    add('KD03-head-save-100', 'save', {**base, 'HeadCircumference': 100}, saved={**base, 'HeadCircumference': 100})
    add('KD03-duplicate-date', 'duplicate-date', base, ['KdpResultAlreadyEnteredMessage'])
    add('KD03-duplicate-code', 'duplicate-code', base, warnings=['KdpDuplicateExamCodeMessage'])
    add('KD03-no-consent', 'consent', base, warnings=['NoConsentMessage'])
    add('KD03-age-young', 'age', {**base, 'ExaminationDate': '2025-02-05'}, warnings=['KdpContactGivenBeforeMinAge'])
    add('KD03-age-old', 'age', {**base, 'ExaminationDate': '2025-02-28'}, warnings=['KdpContactGivenAfterMaxAge'])
    add('KD03-age-boundary', 'age', {**base, 'ExaminationDate': '2025-02-12'})
    add('KD03-bmi', 'bmi', base, bmi=14.88)
    for name, code, scheduled, death in [('unscheduled', 'KD03', False, False), ('scheduled', 'KD03', True, True), ('empty-code', None, False, False)]:
        add('KD03-populate-' + name, 'populate',
            {**base, 'ExaminationCode': code, 'scheduled': scheduled, 'withDeath': death},
            sameDto=True, sameExisting=True, gender='F', birth='2024-12-01',
            death='2025-02-01' if death else None, scheduled=scheduled, unscheduled=not scheduled,
            description='Synthetic KD03' if code else None, selected=code, date='2025-02-19T00:00:00',
            rangesReset=True, lazyBeforeRead=True,
            requestsBeforeRead=0, rangeRequests=['2025-02-19T00:00:00'], scheduleRequests=[code],
            lookupDescriptions=['1 - Synthetic location', 'Unmapped', '2 - Synthetic examiner', '1 - Already prefixed', '2 - Synthetic reason'],
            notifications=['ExamDescription', 'ExamDescription'])
    for name, new_date, reset in [('same-day', '2025-02-19T23:59:59', False),
                                   ('changed-day', '2025-02-20T23:59:59', True)]:
        date = '2025-02-20T09:10:11' if reset else '2025-02-19T09:10:11'
        add('KD03-date-setter-' + name, 'date-setter',
            {**base, 'ExaminationDate': '2025-02-19T09:10:11', 'newDate': new_date},
            date=date, rangesReset=reset, lazyBeforeRead=True,
            rangeRequests=[date] if reset else [], notifications=[])
    add('KD03-weight-setter-warning', 'measurement-setter', {**base, 'newWeight': 6.1},
        weight=6.1, bmi=20.17, notifications=['Bmi', 'IsBmiOutsideRange'],
        warnings=['BmiOutsidePrescribedRangeMessage'])
    for name, current, code, validated in [('blocked', 'KD03', 'KD08', False), ('unchanged', 'KD03', 'KD03', True), ('enter', 'KD08', 'KD03', True), ('leave', 'KD03', 'KD08', True)]:
        changed = validated and current != code
        add('KD03-code-setter-' + name, 'code-setter',
            {**base, 'ExaminationCode': current, 'code': code, 'validated': validated, 'Development': 1, 'DskLocomotor': '1', 'RskEngagement': 1},
            selected=code if changed else current, heart=None if changed and code != 'KD03' else 1,
            development=None if changed and code == 'KD03' else 1,
            dsk=None if changed and code == 'KD03' else '1', rsk=None if changed and code == 'KD03' else 1,
            description=('Synthetic ' + code) if changed else None,
            rangesReset=changed, lazyBeforeRead=True, scheduleRequests=[code if changed else current],
            notifications=['ExamDescription', 'Is15Or27MonthContact', 'Is6To8WeekContact', 'IsDskContact', 'IsRskContact'] if changed else [])
    for kind in ('Height', 'Weight', 'HeadCircumference'):
        for declined in (True, False):
            add('KD03-decline-' + kind + '-' + str(declined).lower(), 'decline',
                {**base, 'measurement': kind, 'declined': declined}, value=None, flag='Y' if declined else 'N')
    for operation in ('location', 'examiner'):
        for code, valid, error in [('', True, None), ('SYNTH', True, None), ('MISSING', False, 'InvalidLocationCodeMessage' if operation == 'location' else 'InvalidHcpCodeMessage')]:
            add('KD03-' + operation + '-' + (code or 'empty'), operation, {**base, 'code': code}, [error] if error else [], valid=valid)
        add('KD03-' + operation + '-null-lookup', operation, {**base, 'code': 'MISSING', 'nullLookup': True}, valid=True)
    add('KD03-examiner-unused', 'examiner', {**base, 'code': 'UNUSED'}, ['UnusedExaminerCodeMessage'], valid=False)
    for value in (40, 50, 60):
        add('KD03-deviation-' + str(value), 'deviation', {**base, 'Height': value}, warnings=[] if value == 50 else ['OutsideExpectedRangeMessage'])
    for weight, warning in [(3.0, True), (3.025, False), (6.05, False), (6.1, True)]:
        add('KD03-bmi-warning-' + str(weight), 'bmi-warning', {**base, 'Weight': weight}, warnings=['BmiOutsidePrescribedRangeMessage'] if warning else [])
    for response in (True, False):
        for reason, current, duplicate in [('duplicate', '', True), ('change', 'OLD', False)]:
            add('KD03-confirm-' + reason + '-' + str(response).lower(), 'code-selection',
                {**base, 'ExaminationCode': current, 'duplicate': duplicate, 'response': response},
                selected='KD03' if response else current, valid=response,
                confirmations=['KdpDuplicateExamCodeMessage' if duplicate else 'KdpResultsExamCodeChangeConfirmationMessage'])
    add('KD03-code-invalid', 'code-selection', {**base, 'code': 'INVALID'},
        ['KdpInvalidExamCodeMessage'], selected='KD03', valid=False, confirmations=[])
    for consent in (True, False):
        add('KD03-new-defaults-' + str(consent).lower(), 'new-result', {'hasConsentFixture': consent},
            warnings=[] if consent else ['NoConsentMessage'],
            defaults={'ClientId': 1001, 'PkChildExaminationId': 0, 'ResultEnteredDate': '2025-03-01T12:00:00',
                      'Origin': 2, 'Reschedule': 'N', 'HeightMeasurementDeclined': 'N',
                      'WeightMeasurementDeclined': 'N', 'HeadMeasurementDeclined': 'N',
                      'EnabledPropChangeEvents': True, 'ExaminationCode': None, 'ExaminationDate': '0001-01-01T00:00:00'},
            insertedFirst=True, count=2, confirmations=[],
            context={'gender': 'F', 'birth': '2024-12-01', 'death': '2025-02-01',
                     'sameExisting': True, 'scheduled': False, 'unscheduled': True,
                     'description': None, 'notifications': ['ExamDescription'],
                     'lazyRanges': True, 'requests': 0})
    for name, id, changed, response, empty in [('accept', 42, True, True, False), ('reject', 42, True, False, False),
                                               ('unchanged', 42, False, False, False), ('new', 0, True, False, False),
                                               ('empty', 42, True, False, True)]:
        reload = changed and response and id > 0 and not empty
        prompted = changed and id > 0 and not empty
        add('KD03-cancel-' + name, 'cancel-changes', {'id': id, 'changed': changed, 'response': response, 'empty': empty},
            allowed=response if prompted else True, reloadCalls=[42] if reload else [],
            height=None if empty else (55 if reload else 99), replaced=reload,
            confirmations=['ExamResultsConfirmCancelMessage'] if prompted else [])
    js('scenarios.json', scenarios)
    put('scenarios.feature', 'Feature: Parity with extracted legacy logic\n' + '\n'.join(
        f"  Scenario: {s['id']}\n    Given {s['given']}\n    When I execute {s['when']} with the input in scenarios.json\n    Then the observation equals the approved then object\n" for s in scenarios))
    inventory = '\n'.join(f'| {n} | {t} | `{dto_path}` property `{n}` |' for t, n in props)
    put('behaviour.md', f'''# KD03 behaviour for review
Evidence means **parity with extracted legacy logic**, never parity with Windows/Oracle.
Source SHA256: {hashlib.sha256(source.encode()).hexdigest()}
Target description (input, not implementation):\n\n{target}\n
## Field inventory
The complete transfer inventory includes metadata and fields excluded from KD03; it is not a mandatory-field list.
| Field | Type | Source |
|---|---|---|
{inventory}

## Applicable rules and observable paths
- `{delegate_path}`: `ExamCode6To8WeekContact` / `Is6To8WeekContact` identifies KD03. `ClearDataFromHiddenFields` retains Heart, Hips, Eyes, Testes, PhysicalGeneral for KD03; clears development, DSK and RSK. The UI populates all five physical dropdowns. Testes label says boys; no gender enforcement appears in this delegate or validator.
- `LookupsUtility.PhysicalAssessment6To8Weeks`: null, 1 Satisfactory, 2 Concern, 3 Not assessed. No physical field is individually mandatory on save. Shared values: EvidenceOfXgm 1 observed/2 disclosed/3 not present/4 not examined/null; DomesticViolenceConcern 1 completed/2 not completed/null. Other dictionaries remain available in retained lookup source.
- `{validator_path}`: `ValidateOnSave` requires code/date, rejects future/before-birth/after-death dates, accepts null measurements, otherwise strictly 0 < height/weight/head < 1000. `NoResults` requires at least one counted result unless a reason is given. PhysicalGeneral is conspicuously NOT counted; Heart/Hips/Eyes/Testes are counted. Reason plus counted results conflicts. Reschedule Y requires reason. Exact code/date duplicate rejects.
- `ValidateHeadCircumference` field path is strictly 0 < value < 100, unlike save's 1000 upper bound. UI Validating calls the field path; service calls only save validation. Shared examples intentionally expose head=100 rejected by field but accepted by direct save. Do not harmonise.
- `ValidateExamCodeForDuplicates` warns for same code on another date; delegate confirmation can cancel code selection. `ValidateKdpConsent` warns, not a mandatory save predicate. Extracted code-selection orchestration exercises accepting/rejecting duplicate and code-change confirmations; remaining delegate lifecycle coverage is a blocking gap.
- `{delegate_path}` `CheckAgeWithinScheduleRange`: below minimum/above positive maximum warns, not rejects; recommendation comes from schedule, NOT the contact name. Demonstration range 6–8 is invented. Measurement deviation warnings use strict interior bounds; BMI warning uses prescribed limits. These database limits are unavailable.
- `{bmi_path}` `CalculateBmi`: weight/(height/100)^2, round two decimals, cap 99.99.
- `KdpExaminationDelegate.AddNewKdpResult`: new id 0; current entered time; unscheduled origin; reschedule and decline flags N. Selecting a decline flag clears its measurement. Extracted parent-delegate scenarios verify defaults, insertion order and consent warnings with no outstanding appointments. Extracted decline setters clear measurements both when checking and unchecking; lookup validation and BMI/deviation warnings now have executable examples with synthetic rows/ranges.
- SQL `EXAM_NOT_EXAMINED_REASON.sql`: KD03 descriptions for codes 1–5; `KDP_LOCATION_TYPES.sql`: UI positions map to actual type keys 5,2,1,17,6,18,22. UI position is not a stored key. Examiner descriptions/locations/used codes require lookups; do not invent mandatory values.

## Examples
See scenarios.feature and scenarios.json (same identifiers, inputs and expected errors/warnings/saved values). Saved values here are a detached dictionary clone, NOT EF/Oracle read-back. Final target must reject unsupported contacts; legacy validator accepts any nonempty code on direct save. That bounded-target guard is not a legacy business rule.
''')
    put('dependencies.md', '''# Dependency map
UI KdpResult -> KdpExaminationResultDelegate -> KdpExaminationValidator / lookup / measurement services.
KdpExaminationDelegate.Save -> KdpExaminationService.SaveKdpExaminationResult -> validator -> unit of work -> ChildExamination, ChildExaminationGiven, ChildExaminationKdp and conditional ChildMeasurement -> Commit.
Service insert assigns generated IDs; mappings retain patient association and assessment/measurement values. Reads use GetKdpExamResults / GetKdpResultTo; final persistence proof must use fresh contexts.
Save also calls ExaminationsCrudManager.UpdateRepeatFlags, UpdateAppointmentStatuses, ClearProducedRecalls. Appointment/recall processing is intentionally excluded. Repeat flags are unresolved (blocking), not silently doubled. Existing-result fixtures are preserved for duplicates. This is NOT full save-service parity.
Oracle IDs, triggers, locks, EF6 mappings, schedule, centile bands, general options, lookup services, messenger and Windows controls are unavailable infrastructure. Source files and schema are retained for inspection, not claimed executable. Editing/locking, appointments, recall, patient search and database migration are outside scope.
''')
    put('gaps.md', '''# Gaps and assumptions
## Blocking
- Extracted examination-date setter now proves same-day no-op, original time preservation on day changes and lazy deviation-range reset. Extracted measurement setters dispatch PropertyChanged to CheckBmi and verify resulting BMI warnings. Windows controls and original DTO change tracking remain unverified. Extracted Populate now verifies context assignment, scheduled/unscheduled state, lazy range resets and repeat-safe numeric lookup descriptions with synthetic lookup rows. Examination-code setter lifecycle now executes source-extracted hidden-field clearing, notifications, description and lazy schedule reset. Extracted parent methods now execute new-result defaults and cancel-changes accept/reject/reload decisions, with explicit change-tracking and reload fixtures. Code-selection duplicate and change confirmations exercise both responses. Decline setters (including unchecking), lookup validation and BMI/deviation warnings now execute extracted members; full delegate lifecycle remains unverified.
- Repeat-flag effects require an explicit reviewed scope adjustment or implementation before approval; appointment and recall processing alone were excluded in the seed.
- The missing WeeksBetween extension is adapted to elapsed days / 7. Review or recover exact legacy rounding before claiming boundary-age parity.
## Non-blocking / review assumptions
Patient 1001, male, born 2025-01-01, clock 2025-03-01 and schedule 6–8 weeks are invented fixtures. Actual schedule, examiner/location lookup rows, BMI thresholds and centile bands are absent. Interaction scenarios explicitly invent SYNTH/UNUSED lookup rows, height range 40–60 and BMI range 10–20; these are review fixtures, not recovered production limits. Null/optional is not mandatory. PhysicalGeneral omission and field/save head discrepancy remain exactly as source, not corrected.
Resource translations are absent: errors/warnings are resource identifiers, not original displayed prose. Reference save only clones accepted input and proves validator outcomes; original service transaction, entity mapping and persistence are unverified. Windows/Oracle application cannot be built from this bundle. PostgreSQL is unverified and not connected. No target or browser implementation has been generated.
''')
    put('migration-plan.md', '''# Bounded migration plan
1. Characterise: retain source identities, inspect inventory/rules, run extracted-reference scenarios. Resolve blocking coverage, repeat scope and age extension gaps with human review; do not approve current incomplete coverage by implication.
2. Approval: runner hashes source/target/reviewed artifacts and stops. Seed acceptance is not behaviour approval.
3. Convert after approval: modern .NET runtime/dependency port; retain validator/delegate structure, compatibility substitutions, same scenarios and observations. No Blazor or redesigned persistence yet.
4. Refactor after conversion parity: server-interactive Blazor and EF Core in-memory. Only KD03 selection/submission, selected synthetic patient; save then read through fresh context. Add shared failure, warning/confirmation, physical assessment, lookup/default and decline examples before approving them.
5. Gates: runner-owned nonempty tests, mechanical observation parity, build/style and browser add/read-back. Retain exact revisions/commands/diagnostics. Demonstrate lifetime-only persistence and excluded Oracle/PostgreSQL infrastructure.
''')
    put('reference/ADAPTATIONS.md', f'''# Extracted reference adaptations
- Complete `{validator_path}` retained verbatim except DateTime.Today -> ReferenceClock.Today (frozen fixture).
- DTO backing/property-change infrastructure replaced with same-named/type auto properties extracted from `{dto_path}`. No validator predicates replaced.
- Missing resource strings replaced with their symbolic names; fault wrappers replaced with Exceptions carrying those names. Aggregated numbered messages normalised only by removing numbering/newlines. Resource identifiers compared exactly in order.
- `{bmi_path}` CalculateBmi method retained verbatim in a small container.
- `{delegate_path}` CheckAgeWithinScheduleRange body retained verbatim; visibility made public; schedule Lazy reads fixture; Messenger records resource IDs. Missing WeeksBetween adapted as elapsed days / 7 (blocking review gap).
- ExtractedInteractions retains BMI/decline/measurement properties and lookup/deviation/BMI method bodies except private visibility. Notifications dispatch through a synchronous PropertyChanged event subscribed to extracted CheckBmi, mirroring the source constructor subscription (not Windows controls). ExaminationDate and ResetDeviations bodies are retained, with ChildMeasurementsRange renamed to the fixture record; GetExpectedRanges records the date and supplies invented height range 40–60. Shared examples check same-day no-op, time preservation, lazy range reset and weight-setter BMI warning dispatch. Lookup retrieval supplies synthetic rows or null; invented height range 40–60 and BMI range 10–20 do not claim database provenance. Display names use symbolic enum names. ValidateAndSetExamCode retains its body with WCF fault wrappers replaced by local exceptions carrying Detail.Title; synchronous confirmation responses are fixture-controlled and recorded. ExaminationCode, UpdateExamDescription, ClearDataFromHiddenFields, their field properties and ResetRecommendedAgeRange are source-extracted. Shared setter cases cover blocked/same-code no-ops and entering/leaving KD03, notifications, description, hidden-field clearing and lazy schedule reset. Synthetic descriptions and a recording schedule double returning 6–8 weeks replace lookups/services; Windows controls remain unverified. Populate, all three PrependNumericsUi description methods, GetDropDownUiPositionNumber and numeric position tables are source-extracted. Synthetic lookup lists replace lazy lookup-service retrieval; repeated Populate checks prefix idempotence, unmatched codes and already-prefixed descriptions. Context and lazy ranges are observed directly; Windows binding remains unverified; parent-delegate Populate integration executes through the extracted factory method. TransferObjectBase.Lock is a storage-only string substitution, not a concurrency implementation. ExamDescription accessor supplies the notification name only; observations read the DTO directly, not the source display accessor.
- `{lifecycle_path}` AddNewKdpResult and ConfirmCancelChanges bodies retained except WCF warning wrapper substitution and DateTime.Now -> ReferenceClock.Now (2025-03-01 noon). Unscheduled enum value 2 is from LookupsUtility.EXAMINATION_ORIGIN. Empty outstanding-appointment list models the excluded appointment workflow. GetNewKdpExaminationResultDelegate is source-extracted and calls extracted Populate through a synthetic dependency-injection factory. Shared new-result cases verify supplied patient context, existing-list identity, unscheduled default, description notification and lazy ranges without service requests. Windows events remain unverified; hasChanged returns an explicit fixture flag, not original change tracking. Reload double records IDs and supplies a detached stored DTO; this proves reload orchestration, not database reads. Scenarios cover accept/reject, unchanged, new and empty cancellation paths and defaults/consent/insertion order.
- reference driver dispatches operation then serialises errors/warnings/BMI and detached accepted-input clone. It is NOT the save service and does NOT prove persistence. No random IDs are generated. No business rules supplied by database doubles.
- `original/` retains unadapted source sections for independent inspection. `source-index.json` records original identity and bundle line for every one of 94 files.
- verify.py executes the C# harness and mechanically compares every scenario then object; counts are derived from actual comparison. Report includes actual observations and limitations. Target implementation is entirely separate and not generated here.
''')
    # All extracted original source is reviewed, not merely selected business methods.
    index = []
    for identity, body in files.items():
        put('reference/original/' + identity, body)
        index.append({'file': identity, 'bundleLine': source[:re.search(r'>>> FILE \d+/94: ' + re.escape(identity) + r'   \[', source).start()].count('\n') + 1,
                      'sha256': hashlib.sha256(body.encode()).hexdigest()})
    js('source-index.json', index)
    reviewed = ['behaviour.md', 'dependencies.md', 'gaps.md', 'fixtures.json', 'migration-plan.md', 'scenarios.json', 'scenarios.feature', 'source-index.json', 'verify.py']
    reviewed += sorted(str(p.relative_to(out)) for p in (out / 'reference').rglob('*') if p.is_file() and not any(part in ('bin', 'obj') for part in p.parts))
    # Original bundled tests/other projects must not compile into the standalone harness.
    put('reference/Reference.csproj', '<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><Nullable>disable</Nullable></PropertyGroup><ItemGroup><Compile Remove="original/**/*.cs" /></ItemGroup></Project>\n')
    js('stage.json', {'reviewFiles': reviewed, 'blockingGaps': ['Delegate interaction coverage incomplete', 'Repeat-flag scope unresolved', 'WeeksBetween adaptation requires review'],
                      'checks': [{'command': {'executable': sys.executable, 'arguments': ['verify.py'], 'timeoutSeconds': 600}, 'results': 'results.json'}]})


if __name__ == '__main__':
    generate(json.loads(Path(sys.argv[-1]).read_text()))
