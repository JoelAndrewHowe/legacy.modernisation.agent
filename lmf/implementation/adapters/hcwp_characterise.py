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


def method(text, name, parameters=None):
    signature = r'[^\n]*' if parameters is None else re.escape(parameters)
    match = re.search(r'        (?:public|private) (?:static )?[^\n]+\b' + name + r'\(' + signature + r'\)\s*\{', text)
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
    ui_path, ui = find('/ucHLXKdpExaminationResult.cs')
    save_ui_path, save_ui = find('/ucHLXKdpExaminations.cs')
    dates_path, dates = find('/DateCalculation.cs')
    repeat_path, repeat_source = find('/ExaminationsCrudManager.cs')
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
    resources = sorted((set(re.findall(r'\b\w+(?:Message|Prompt)\b', validator)) | set(re.findall(r'Resources\.Resources\.(\w+)', method(lifecycle, 'AddNewKdpResult') + method(lifecycle, 'ConfirmCancelChanges') + method(lifecycle, 'Save'))) | {'ResultsRecordedButNotExamined'}) - {
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
 public List<string> ErrorPrompts = new();
 public List<string> Confirmations = new();
 public bool ConfirmationResponse;
 // Explicit per-prompt responses; empty queue preserves single-response fixtures.
 public Queue<bool> ConfirmationResponses = new();
 public string LookupResponse;
 public List<List<string>> LookupRequests = new();
 public void Send(ShowFormLookup value) { LookupRequests.Add(value.Rows.Select(row => row.Code).ToList()); value.Values = LookupResponse; }
 public void Send(YesNoConfirmationRequiredMessage value) { Confirmations.Add(value.Message); value.Response = ConfirmationResponses.Count > 0 ? ConfirmationResponses.Dequeue() : ConfirmationResponse; }
 public void Send(NonFatalErrorEncountered value) { Errors.Add(value.Message); ErrorPrompts.Add(value.Prompt); }
 public void Send(WarningNotificationMessage value) => Warnings.Add(value.Message);
}
''')
    put('reference/ExtractedDateCalculation.cs', 'using System;\npublic static class DateExtensions {\n'
        + method(dates, 'DaysBetween') + '\n' + method(dates, 'WeeksBetween') + '\n}\n')
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
    for name in ('LocationType', 'LocationCode', 'ExaminerKdpCode', 'ExaminerType', 'ExaminerCategory', 'ExaminerName'):
        members += '\n' + re.search(r'        public [^\n]+ ' + name + r'\s*\{.*?\n        \}', delegate, re.S).group()
    members += '\n' + method(delegate, 'PopulateHcpDetails')
    members += '\n' + code_property + '\n' + clearing
    members += '\n' + re.search(r'        public string ExamDescription\s*\{.*?\n        \}', delegate, re.S).group()
    members += '\n' + method(delegate, 'UpdateExamDescription') + '\n' + method(delegate, 'ResetRecommendedAgeRange')
    members += '\n' + '\n'.join(line for line in delegate.splitlines() if re.search(r'(private readonly string\[\] examCode|public bool Is(?:15Or27Month|Rsk|6To8Week|Dsk)Contact =>)', line))
    members += '\n' + method(delegate, 'ResetDeviations').replace('ChildMeasurementsRange', 'RangeFixture')
    members += '\n' + method(delegate, 'Populate')
    members += '\n' + age
    members += '\n' + '\n'.join(method(delegate, n).replace('FaultException<ValidationFault>', 'ValidationFault') for n in ('ValidateHeight', 'ValidateWeight', 'ValidateHeadCircumference', 'ValidateExaminationDate'))
    members += '\n' + '\n'.join(method(delegate, n) for n in ('GetDropDownUiPositionNumber', 'PrependNumericsUiLocationTypeDescriptions', 'PrependNumericsUiExaminerDescriptions', 'PrependNumericsUiReasonNotExaminedDescriptions'))
    members += '\n' + re.search(r'        private class TypeCodePosition\s*\{.*?\n        \}', delegate, re.S).group()
    for name in ('Location', 'Examiner', 'ReasonNotExamined'):
        members += '\n' + re.search(r'        List<TypeCodePosition> ' + name + r'TypeCodePositions = .*?\n        \};', delegate, re.S).group()
    members += '\n' + '\n'.join(line for line in delegate.splitlines() if 'private const string DropDownCodeDescriptionFormat' in line)
    members += '\n' + re.search(r'public enum TYPE_OF_INPUT[^\n]+', delegate).group()
    members += '\n' + method(delegate, 'ValidateNumericDescriptorEntered')
    members += '\n' + '\n'.join(method(delegate, n).replace('List<LookupsSubTO>', 'List<LookupFixture>') for n in ('GetLocationList', 'GetExaminerList', 'GetUsedExaminerList'))
    members += '\n' + method(delegate, 'LookUpExamCode')
    members += '\n' + method(delegate, 'ValidateAndSetExamCode').replace('FaultException<ValidationWarningFault>', 'ValidationWarningFault').replace('FaultException<ValidationFault>', 'ValidationFault')
    symbols = sorted(set(re.findall(r'\b(?:\w+(?:Message|Prompt|Title)|KdpContactGivenBeforeMinAge|KdpContactGivenAfterMaxAge)\b', members)) - {'warningMessage', 'WarningNotificationMessage'})
    constants = '\n'.join(f' const string {s} = "{s}";' for s in symbols)
    put('reference/ExtractedInteractions.cs', (ROOT / 'delegate-support.cs.txt').read_text().replace('__MEMBERS__', constants + '\n' + members))
    lifecycle_members = '\n'.join(method(lifecycle, n) for n in ('AddNewKdpResult', 'ConfirmCancelChanges', 'GetNewKdpExaminationResultDelegate', 'Save'))
    lifecycle_members = lifecycle_members.replace('FaultException<ValidationWarningFault>', 'ValidationWarningFault').replace('DateTime.Now', 'ReferenceClock.Now')
    put('reference/ExtractedLifecycle.cs', (ROOT / 'lifecycle-support.cs.txt').read_text().replace('__MEMBERS__', lifecycle_members))
    put('reference/ExtractedSaveControl.cs', (ROOT / 'save-control-support.cs.txt').read_text().replace('__MEMBERS__', method(save_ui, 'SaveChanges')))
    ui_members = '\n'.join(method(ui, 'hlxNumericEditBoxCustom' + field + '_Validating').replace('private void', 'public void') for field in ('Height', 'Weight', 'HeadCirc'))
    put('reference/ExtractedMeasurementControls.cs', '''using System;
using System.ComponentModel;
// Text/Value-only control fixtures; no Windows binding or event loop is simulated.
public class ControlFixture { public string Text; public object Value; }
public class ExtractedMeasurementControls {
 public ExtractedInteractions kdpExaminationResultDelegate;
 public ControlFixture hlxNumericEditBoxCustomHeight = new(), hlxNumericEditBoxCustomWeight = new(), hlxNumericEditBoxCustomHeadCirc = new();
''' + ui_members + '\n}\n')
    put('reference/ExtractedDateControl.cs', '''using System;
using System.ComponentModel;
// Text/DateTime-only fixture; direct invocation does not prove Windows event delivery.
public class DateControlFixture { public string Text; public DateTime Value; }
public class ExtractedDateControl {
 public ExtractedInteractions kdpExaminationResultDelegate;
 public DateControlFixture hlxDateBoxExamDate = new();
''' + method(ui, 'hlxDateBoxExamDate_Validating').replace('private void', 'public void') + '\n}\n')
    put('reference/ExtractedCodeControl.cs', '''using System;
using System.ComponentModel;
// Text-only fixture; lookup response is supplied by the synchronous message double.
public class CodeControlFixture { public string Text; }
public class ExtractedCodeControl {
 public ExtractedInteractions kdpExaminationResultDelegate;
 public CodeControlFixture hlxTextBoxExamCode = new();
''' + '\n'.join(method(ui, name).replace('private void', 'public void') for name in ('hlxTextBoxExamCode_Validating', 'hlxTextBoxExamCode_ButtonClick')) + '\n}\n')
    dropdown_members = '\n'.join(method(ui, name, 'object sender, EventArgs e').replace('private void', 'public void')
        for name in ('ValidateLocationTypeInput', 'ValidateExaminerTypeInput', 'ValidateReasonNotExaminedTypeInput'))
    dropdown_members += '\n' + method(ui, 'ValidateExaminerTypeInput', 'object sender, CancelEventArgs e').replace('private void', 'public void')
    put('reference/ExtractedDropdownControls.cs', '''using System;
using System.ComponentModel;
// Text-only sender double; no proprietary dropdown binding or event delivery.
public class HlxDropDown { public string Text; }
public class ExtractedDropdownControls {
 public ExtractedInteractions kdpExaminationResultDelegate;
''' + dropdown_members.replace('KdpExaminationResultDelegate.TYPE_OF_INPUT', 'ExtractedInteractions.TYPE_OF_INPUT') + '\n}\n')
    # Only visibility changes; query/grouping/flag decisions remain source-owned.
    repeat_member = method(repeat_source.replace('internal static void', 'public static void'), 'UpdateRepeatFlags')
    put('reference/ExtractedRepeatFlags.cs', (ROOT / 'repeat-support.cs.txt').read_text().replace('__MEMBERS__', repeat_member))
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
    for field in ('Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral'):
        for mode, clear, reason in [('value', False, None), ('cleared', True, None),
                                    ('reason', False, '1'), ('cleared-reason', True, '1')]:
            counted = not clear and field != 'PhysicalGeneral'
            errors = (['ResultsRecordedButNotExamined'] if counted else []) if reason else ([] if counted else ['NoResultsEnteredMessage'])
            stored = {name: 2 if name == field and not clear else None
                      for name in ('Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral')}
            add(f'KD03-physical-{field}-{mode}', 'physical-assessment',
                {'ClientId': 1001, 'ExaminationCode': 'KD03', 'ExaminationDate': '2025-02-19',
                 'ReasonNotExamined': reason, 'field': field, 'clear': clear}, errors,
                assigned=2, displayed=None if clear else 2, stored=stored,
                notifications=[], accepted=not errors)
    for name, category in [('changed', 2), ('same', 5), ('null', None)]:
        add('KD03-location-category-' + name, 'location-category',
            {**base, 'LocationType': 5, 'LocationCode': 'SYNTH', 'LocationName': 'Stale name', 'category': category},
            category=category, code='', name='', cacheCleared=True,
            refreshedCodes=None if category is None else ['NEW'],
            requests=[] if category is None else [f'Locations||{category}'],
            errors=['NoLocationTypeMessage'] if category is None else [],
            notifications=[])
    for name, code, description in [('matched', 'SYNTH', 'Synthetic location description'),
                                     ('unknown', 'MISSING', None), ('empty', '', ''), ('null', None, '')]:
        add('KD03-location-code-' + name, 'location-code',
            {**base, 'LocationType': 5, 'LocationName': 'Stale name', 'code': code, 'noCache': False},
            code=code, name=description, sameCache=True, requests=[], notifications=[])
    add('KD03-location-code-no-cache', 'location-code',
        {**base, 'LocationType': 5, 'LocationName': 'Stale name', 'code': 'SYNTH', 'noCache': True},
        code='SYNTH', name=None, sameCache=True, requests=[], notifications=[])
    for name, category in [('changed', '19'), ('same', '18'), ('null', None)]:
        add('KD03-examiner-category-' + name, 'examiner-category',
            {**base, 'ExaminerCategory': '18', 'ExaminerType': 'OLD', 'ExaminerHcpCode': 'SYNTH', 'ExaminerName': 'Stale name', 'category': category},
            category=category, type='', code='', name='', cacheCleared=True,
            refreshedCodes=None if category is None else ['NEW'],
            requests=[] if category is None else [f'Examiners||{category}|N'],
            errors=['NoExaminerTypeMessage'] if category is None else [], notifications=[])
    for name, code, category, examiner_type, description, cache_cleared in [
        ('matched', 'SYNTH', '18', 'SYNTH-TYPE', 'Synthetic HCP', False),
        ('unused', 'UNUSED', '18', None, None, False),
        ('unknown', 'MISSING', '18', None, None, False),
        ('empty', '', '', '', '', True), ('null', None, '', '', '', True)]:
        add('KD03-examiner-code-' + name, 'examiner-code',
            {**base, 'ExaminerCategory': '18', 'ExaminerType': 'OLD', 'ExaminerName': 'Stale name', 'code': code},
            code='' if cache_cleared else code, category=category, type=examiner_type,
            name=description, cacheCleared=cache_cleared, requests=[], notifications=[])
    for name, repeat, original, description, displayed in [
        ('nonrepeat', False, 'KD03', 'Synthetic contact', 'Synthetic contact'),
        ('repeat-original-code', True, 'KD03', 'Synthetic contact', 'Synthetic contact [synthetic recall text]'),
        ('repeat-changed-code', True, 'KD08', 'Synthetic contact', 'Synthetic contact'),
        ('repeat-missing-original', True, None, 'Synthetic contact', 'Synthetic contact'),
        ('repeat-null-description', True, 'KD03', None, ' [synthetic recall text]'),
    ]:
        add('KD03-description-' + name, 'description-accessor',
            {**base, 'IsRepeat': repeat, 'OriginalExamCode': original, 'description': description},
            displayed=displayed, stored=description)
    for kind, maximum, stored_key in [('LOCATON_TYPE', 7, '22'), ('EXAMINER_TYPE', 12, '28'), ('REASON_NOT_EXAMINED', 5, '5')]:
        for label, text, valid in [('first', '1', True), ('last', str(maximum), True),
                                   ('zero', '0', False), ('negative', '-1', False),
                                   ('above', str(maximum + 1), False),
                                   ('stored-key', stored_key, int(stored_key) <= maximum),
                                   ('empty', '', True), ('text', 'unknown', True),
                                   ('decimal', '1.5', True), ('overflow', '2147483648', True),
                                   ('whitespace', ' 1 ', True)]:
            add('KD03-numeric-descriptor-' + kind + '-' + label, 'numeric-descriptor',
                {**base, 'descriptor': text, 'kind': kind}, valid=valid)
            # Handlers trim for validation only: accepted text must remain verbatim.
            add('KD03-dropdown-' + kind + '-' + label, 'dropdown-control',
                {**base, 'descriptor': text, 'kind': kind, 'cancelOverload': False, 'initialCancel': False},
                text=text if valid else '', cancelled=False)
    for initial_cancel in (False, True):
        add('KD03-dropdown-examiner-cancel-' + str(initial_cancel).lower(), 'dropdown-control',
            {**base, 'descriptor': ' 999 ', 'kind': 'EXAMINER_TYPE', 'cancelOverload': True, 'initialCancel': initial_cancel},
            text=' 999 ', cancelled=initial_cancel)
    repeat_rows = [
        {'id': 1, 'client': 1001, 'code': 'KD03', 'date': '2025-02-19T09:00:00', 'flag': 'Y'},
        {'id': 2, 'client': 1001, 'code': 'KD03', 'date': '2025-02-19T09:00:00', 'flag': 'Y'},
        {'id': 3, 'client': 1001, 'code': 'KD03', 'date': '2025-02-19T10:00:00', 'flag': 'N'},
        {'id': 4, 'client': 1001, 'code': 'KD08', 'date': '2025-02-20', 'flag': 'Y'},
        {'id': 5, 'client': 1001, 'code': 'KD08', 'date': '2025-02-21', 'flag': 'N'},
        # Earlier than this patient's KD03 rows: losing the local client filter
        # would change this flag to N and incorrectly mark this patient's ties Y.
        {'id': 6, 'client': 1002, 'code': 'KD03', 'date': '2025-02-18', 'flag': 'Y'},
        {'id': 7, 'client': 1001, 'code': 'XX03', 'date': '2025-02-20', 'flag': 'Y'},
    ]
    for name, code, detached, flags in [
        ('family-and-date-ties', 'KD03', False, ['N', 'N', 'Y', 'N', 'Y', 'Y', 'Y']),
        ('local-navigation-repair', 'KD03', True, ['N', 'N', 'Y', 'N', 'Y', 'Y', 'Y']),
        ('short-prefix', 'K', False, ['N', 'N', 'Y', 'N', 'Y', 'Y', 'Y']),
        ('unmatched-prefix', 'ZZ03', False, ['Y', 'Y', 'N', 'Y', 'N', 'Y', 'Y']),
    ]:
        add('KD03-repeat-' + name, 'repeat-flags', {**base, 'requestedCode': code, 'rows': repeat_rows, 'detached': detached},
            flags=flags, navigationRestored=True, idempotent=True)
    for field, valid, invalid, error in [('Height', 50, 0, 'InvalidHeightMessage'), ('Weight', 4.5, 1000, 'InvalidWeightMessage'), ('HeadCirc', 38, 100, 'HeadCircumferenceInvalidFormatMessage')]:
        for name, text, value, cancelled, errs, warns in [('valid', 'value', valid, False, [], []), ('invalid', 'value', invalid, True, [error], []), ('empty', '', invalid, False, [], []), ('empty-preserves-cancel', '', invalid, True, [], [])]:
            add(f'KD03-control-{field}-{name}', 'measurement-control', {**base, 'field': field, 'text': text, 'value': value, 'initialCancel': name == 'empty-preserves-cancel'}, errs, warns, cancelled=cancelled)
    for name, date, error, warning in [('valid', '2025-02-19', None, None), ('future', '2025-03-02', 'FutureExamDateMessage', None), ('before-birth', '2024-12-31', 'ExamDateBeforeDobMessage', None), ('after-death', '2025-02-21', 'ExamDateAfterDeathMessage', None), ('duplicate', '2025-02-19', 'KdpResultAlreadyEnteredMessage', None), ('young', '2025-02-05', None, 'KdpContactGivenBeforeMinAge'), ('old', '2025-02-27', None, 'KdpContactGivenAfterMaxAge'), ('empty', '2025-03-02', None, None), ('empty-preserves-cancel', '2025-03-02', None, None)]:
        add('KD03-date-control-' + name, 'date-control', {**base, 'value': date, 'text': '' if name.startswith('empty') else date, 'initialCancel': name == 'empty-preserves-cancel', 'deathFixture': '2025-02-20' if name == 'after-death' else None, 'duplicateFixture': name == 'duplicate'}, [error] if error else [], [warning] if warning else [], cancelled=bool(error) or name == 'empty-preserves-cancel')
    for kind in ('location', 'examiner'):
        for mode in ('missing', 'cached', 'retrieved', 'fault'):
            missing = mode == 'missing'
            fault = mode == 'fault'
            requests = [] if missing or mode == 'cached' else ([('Locations||5' if kind == 'location' else 'Examiners||18|N')] * (2 if fault else 1))
            errors = [('NoLocationTypeMessage' if kind == 'location' else 'NoExaminerTypeMessage')] * 2 if missing else ['synthetic-lookup-fault'] * 2 if fault else []
            prompts = [('NoLocationTypePrompt' if kind == 'location' else 'NoExaminerTypePrompt')] * 2 if missing else [('ErrorGettingLocationListPrompt' if kind == 'location' else 'ErrorGettingExaminerListPrompt')] * 2 if fault else []
            add('KD03-lookup-retrieval-' + kind + '-' + mode, 'lookup-retrieval',
                {**base, 'kind': kind, 'mode': mode, 'LocationType': None if missing else 5, 'ExaminerCategory': None if missing else '18'},
                errors, codes=None if missing or fault else ['SYNTH', 'UNUSED'] if kind == 'location' else ['SYNTH'],
                requests=requests, prompts=prompts, sameRows=not (missing or fault))
    for name, text, lookup, response, original, selected, cancelled, error, confirmation, count in [
        ('valid', 'KD03', None, False, '', 'KD03', False, None, None, 0),
        ('invalid-cancel-lookup', 'INVALID', None, False, '', '', True, 'KdpInvalidExamCodeMessage', None, 1),
        ('invalid-select-lookup', 'INVALID', 'KD03', False, '', 'KD03', True, 'KdpInvalidExamCodeMessage', None, 1),
        ('invalid-lookup-result', 'INVALID', 'INVALID', False, '', '', True, 'KdpInvalidExamCodeMessage', None, 1),
        ('change-accept', 'KD03', None, True, 'KD08', 'KD03', False, None, 'KdpResultsExamCodeChangeConfirmationMessage', 0),
        ('change-reject', 'KD03', None, False, 'KD08', 'KD08', True, None, 'KdpResultsExamCodeChangeConfirmationMessage', 1),
        ('button-select', 'IGNORED', 'KD03', False, '', 'KD03', True, None, None, 1),
        ('button-cancel', 'IGNORED', '', False, 'KD08', 'KD08', True, None, None, 1),
    ]:
        add('KD03-code-control-' + name, 'code-control', {**base, 'ExaminationCode': original, 'text': text, 'lookup': lookup, 'response': response, 'button': name.startswith('button'), 'initialCancel': True},
            [error] * (2 if name == 'invalid-lookup-result' else 1) if error else [], selected=selected, cancelled=cancelled,
            confirmations=[confirmation] if confirmation else [], lookupRequests=count,
            lookupCodes=[['KD03', 'KD08']] if count else [])
    add('KD03-control-Height-warning', 'measurement-control', {**base, 'field': 'Height', 'text': '40', 'value': 40, 'initialCancel': False}, warnings=['OutsideExpectedRangeMessage'], cancelled=False)
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
    add('KD03-age-upper-fractional-day', 'age', {**base, 'ExaminationDate': '2025-02-26T12:00:00'})
    add('KD03-age-after-upper-day', 'age', {**base, 'ExaminationDate': '2025-02-27'}, warnings=['KdpContactGivenAfterMaxAge'])
    for name, date, weeks in [('positive', '2025-02-26T12:00:00', 8), ('negative', '2024-12-31T12:00:00', 0)]:
        add('KD03-weeks-truncation-' + name, 'weeks-between', {'ExaminationDate': date}, weeks=weeks)
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
    for field, value, bmi_value, outside in [
        ('Height', 40, 28.12, True), ('Height', 55, 14.88, False), ('Height', None, None, False),
        ('Weight', 3, 9.92, True), ('Weight', 4.5, 14.88, False), ('Weight', None, None, False),
        ('HeadCircumference', 40, 14.88, False), ('HeadCircumference', None, 14.88, False),
    ]:
        notifications = ['HeadCircumference'] if field == 'HeadCircumference' else ['Bmi', 'IsBmiOutsideRange']
        add('KD03-assignment-' + field + '-' + str(value), 'measurement-assignment',
            {**base, 'field': field, 'value': value},
            warnings=['BmiOutsidePrescribedRangeMessage'] * 2 if outside else [],
            value=value, bmi=bmi_value, outside=outside, notifications=notifications * 2)
    for kind in ('Height', 'Weight', 'HeadCircumference'):
        for declined in (True, False):
            add('KD03-decline-' + kind + '-' + str(declined).lower(), 'decline',
                {**base, 'measurement': kind, 'declined': declined}, value=None, flag='Y' if declined else 'N',
                required=not declined, notifications=['Is' + kind + 'Required'] +
                (['HeadCircumference'] if kind == 'HeadCircumference' else ['Bmi', 'IsBmiOutsideRange']))
    for operation in ('location', 'examiner'):
        for code, valid, error in [('', True, None), ('SYNTH', True, None), ('MISSING', False, 'InvalidLocationCodeMessage' if operation == 'location' else 'InvalidHcpCodeMessage')]:
            add('KD03-' + operation + '-' + (code or 'empty'), operation, {**base, 'code': code, 'LocationType': 5, 'ExaminerCategory': '18'}, [error] if error else [], valid=valid)
        add('KD03-' + operation + '-null-lookup', operation, {**base, 'code': 'MISSING', 'nullLookup': True, 'LocationType': 5, 'ExaminerCategory': '18'}, valid=True)
    add('KD03-examiner-unused', 'examiner', {**base, 'code': 'UNUSED', 'ExaminerCategory': '18'}, ['UnusedExaminerCodeMessage'], valid=False)
    for name, height, date, lower, upper, warning, read in [
        ('missing-height', None, '2025-02-19', 40, 60, False, False),
        ('missing-date', 50, '0001-01-01', 40, 60, False, False),
        ('equal-band', 50, '2025-02-19', 50, 50, True, True),
        ('reversed-band', 50, '2025-02-19', 60, 40, True, True),
    ]:
        add('KD03-deviation-guard-' + name, 'deviation-guard',
            {**base, 'Height': height, 'ExaminationDate': date, 'lower': lower, 'upper': upper},
            warnings=['OutsideExpectedRangeMessage'] if warning else [], rangeRead=read)
    for name, prop, height, weight, warning, read in [
        ('bmi-outside', 'Bmi', 55, 6.1, True, True),
        ('unrelated', 'Height', 55, 6.1, False, False),
        ('range-property', 'IsBmiOutsideRange', 55, 6.1, False, False),
        ('empty-property', '', 55, 6.1, False, False),
        ('null-property', None, 55, 6.1, False, False),
        ('missing-height', 'Bmi', None, 6.1, False, False),
        ('missing-weight', 'Bmi', 55, None, False, False),
        ('bmi-inside', 'Bmi', 55, 4.5, False, True),
    ]:
        add('KD03-bmi-event-' + name, 'bmi-event',
            {**base, 'Height': height, 'Weight': weight, 'property': prop},
            warnings=['BmiOutsidePrescribedRangeMessage'] if warning else [], rangeRead=read)
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
    for name, responses, accepted in [('reject-duplicate', [False, True], False), ('reject-change', [True, False], False), ('accept-both', [True, True], True)]:
        add('KD03-confirm-sequence-' + name, 'code-selection-sequence',
            {**base, 'ExaminationCode': 'KD08', 'duplicate': True, 'responses': responses},
            selected='KD03' if accepted else 'KD08', valid=accepted, validated=accepted,
            confirmations=['KdpDuplicateExamCodeMessage'] + (['KdpResultsExamCodeChangeConfirmationMessage'] if responses[0] else []),
            remainingResponses=0 if responses[0] else 1)
    add('KD03-code-invalid', 'code-selection', {**base, 'code': 'INVALID'},
        ['KdpInvalidExamCodeMessage'], selected='KD03', valid=False, confirmations=[])
    for outcome in ('success', 'optimistic-lock', 'fault', 'no-tab'):
        success = outcome == 'success'
        add('KD03-ui-save-' + outcome, 'ui-save', {'outcome': outcome},
            [] if outcome in ('success', 'no-tab') else ['synthetic-' + outcome],
            allowed=success, calls=0 if outcome == 'no-tab' else 1,
            sameContext=outcome != 'no-tab', sameResult=outcome != 'no-tab',
            currentIsSelected=True, defaultTab=not success,
            refreshes=[{'Id': 1001, 'Editable': False, 'SaveCalls': 1, 'DefaultTab': True}] if success else [],
            prompts=[] if outcome in ('success', 'no-tab') else ['ExamResultsErrorSavingPrompt'])
    for outcome in ('success', 'optimistic-lock', 'fault'):
        add('KD03-parent-save-' + outcome, 'parent-save', {'outcome': outcome},
            [] if outcome == 'success' else ['synthetic-' + outcome],
            allowed=outcome == 'success', calls=1, sameContext=True, sameResult=True,
            prompts=[] if outcome == 'success' else ['ExamResultsErrorSavingPrompt'],
            unrelatedUnchanged=True)
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
- `ValidateExamCodeForDuplicates` warns for same code on another date; delegate confirmation can cancel code selection. `ValidateKdpConsent` warns, not a mandatory save predicate. Extracted code-selection orchestration exercises accepting/rejecting duplicate and code-change confirmations separately and in sequence. Rejecting the duplicate prompt stops before the change prompt; accepting the duplicate but rejecting the change leaves KD08 selected and validation false; only accepting both selects KD03. Remaining delegate lifecycle coverage is a blocking gap.
- `{delegate_path}` `CheckAgeWithinScheduleRange`: below minimum/above positive maximum warns, not rejects; recommendation comes from schedule, NOT the contact name. Demonstration range 6–8 is invented. Measurement deviation warnings use strict interior bounds; null measurements or minimum dates bypass range retrieval, while equal/reversed bands warn. BMI warning uses prescribed limits and only reacts to the exact Bmi property name; missing height/weight bypass prescribed-range retrieval. Shared guard scenarios observe lazy range access as well as warnings. These database limits are unavailable.
- `{bmi_path}` `CalculateBmi`: weight/(height/100)^2, round two decimals, cap 99.99.
- `KdpExaminationDelegate.AddNewKdpResult`: new id 0; current entered time; unscheduled origin; reschedule and decline flags N. Selecting a decline flag clears its measurement. Extracted parent-delegate scenarios verify defaults, insertion order and consent warnings with no outstanding appointments. Extracted decline setters clear measurements both when checking and unchecking; lookup validation and BMI/deviation warnings now have executable examples with synthetic rows/ranges.
- SQL `EXAM_NOT_EXAMINED_REASON.sql`: KD03 descriptions for codes 1–5; `KDP_LOCATION_TYPES.sql`: UI positions map to actual type keys 5,2,1,17,6,18,22. UI position is not a stored key. Source-extracted `ValidateNumericDescriptorEntered` checks parsed integers against UI positions (location 1–7, examiner 1–12, reason 1–5); nonnumeric, empty, decimal and overflowing inputs return true, deferring code validation elsewhere. Shared scenarios retain this permissive behaviour rather than inventing stricter validation. Examiner descriptions/locations/used codes require lookups; do not invent mandatory values.

## Examples
See scenarios.feature and scenarios.json (same identifiers, inputs and expected errors/warnings/saved values). Saved values here are a detached dictionary clone, NOT EF/Oracle read-back. Final target must reject unsupported contacts; legacy validator accepts any nonempty code on direct save. That bounded-target guard is not a legacy business rule.
''')
    put('dependencies.md', '''# Dependency map
UI KdpResult -> KdpExaminationResultDelegate -> KdpExaminationValidator / lookup / measurement services.
KdpExaminationDelegate.Save -> KdpExaminationService.SaveKdpExaminationResult -> validator -> unit of work -> ChildExamination, ChildExaminationGiven, ChildExaminationKdp and conditional ChildMeasurement -> Commit.
Service insert assigns generated IDs; mappings retain patient association and assessment/measurement values. Reads use GetKdpExamResults / GetKdpResultTo; final persistence proof must use fresh contexts.
Save also calls ExaminationsCrudManager.UpdateRepeatFlags, UpdateAppointmentStatuses, ClearProducedRecalls. Appointment/recall processing is intentionally excluded. Repeat flags remain a scope decision (blocking), not silently excluded. Extracted UpdateRepeatFlags now proves that the requested code selects its two-character family, groups by exact code and patient, marks every earliest exact timestamp N (including ties), and later timestamps Y. KD03 calls can therefore mutate existing KD08 flags; same-day different times are distinct. Shared examples also cover short/unmatched prefixes, local navigation repair and idempotence. Human review must decide whether these existing-result mutations are included in the bounded add workflow. Existing-result fixtures are preserved for duplicates. This is NOT full save-service parity.
Oracle IDs, triggers, locks, EF6 mappings, schedule, centile bands, general options, lookup services, messenger and Windows controls are unavailable infrastructure. Source files and schema are retained for inspection, not claimed executable. Editing/locking, appointments, recall, patient search and database migration are outside scope.
''')
    put('gaps.md', f'''# Gaps and assumptions
## Blocking
- Extracted examination-date setter now proves same-day no-op, original time preservation on day changes and lazy deviation-range reset. Extracted measurement setters dispatch PropertyChanged to CheckBmi and verify resulting BMI warnings. Measurement validation handlers execute with control doubles; real Windows controls and original DTO change tracking remain unverified. Extracted Populate now verifies context assignment, scheduled/unscheduled state, lazy range resets and repeat-safe numeric lookup descriptions with synthetic lookup rows. Examination-code setter lifecycle now executes source-extracted hidden-field clearing, notifications, description and lazy schedule reset. Extracted parent methods now execute new-result defaults and cancel-changes accept/reject/reload decisions, with explicit change-tracking and reload fixtures. Code-selection duplicate and change confirmations exercise both responses. Decline setters (including unchecking), lookup validation and BMI/deviation warnings now execute extracted members; full delegate lifecycle remains unverified.
- Repeat-flag effects require an explicit reviewed scope adjustment or implementation before approval; appointment and recall processing alone were excluded in the seed.
- Recovered `{dates_path}` DaysBetween/WeeksBetween: elapsed days truncate toward zero before division by 7. Both bodies are extracted unchanged; fractional-day and negative-interval scenarios prevent regression to the former elapsed-days / 7 substitution.
Measurement assignment scenarios execute each retained Height/Weight/HeadCircumference setter twice, including unchanged and null values. They observe DTO values, calculated BMI, range status, ordered notifications and repeated warning dispatch. Decline scenarios also observe required-state and ordered notifications on both checking and unchecking; either action clears the measurement. These are synchronous delegate observations, not Windows event/binding evidence.

## Non-blocking / review assumptions

Lookup retrieval now executes source-extracted GetLocationList, GetExaminerList and GetUsedExaminerList: missing categories produce prompts even with cached rows, successful retrieval is cached, faults return null and retry on the next call, and examiner results filter UsedCode=Y. The recording lookup-service double returns unfiltered synthetic rows and records exact request arguments; no database or Windows dropdown binding is verified.

Repeat-flag query infrastructure is an in-memory fixture, not EF6/Oracle: explicit already-loaded database rows and local tracked rows replace Include/Repository/Local; navigation repair, filtering, grouping and flag assignment execute the retained source method. No transaction, database loading, concurrency or save-service integration parity is claimed.

Physical-assessment scenarios directly execute extracted Heart/Hips/Eyes/Testes/PhysicalGeneral setters with repeated assignment and null clearing, then extracted ValidateOnSave. Each counted field alone satisfies NoResults but conflicts with a not-examined reason; PhysicalGeneral alone does not satisfy NoResults and does not conflict with that reason. Stored sibling fields and notifications are observed. Acceptance here means validator acceptance only, not persistence or Windows binding; assessment value 2 and reason 1 are explicit fixtures.

Examination-code Validating and ButtonClick handlers and delegate LookUpExamCode are source-extracted. A Text-only control double invokes handlers directly; a synchronous ShowFormLookup message double records offered synthetic codes and supplies a fixture response (including null/empty cancellation). Scenarios verify valid selection, rejected changes, invalid codes, lookup cancellation/selection and invalid returned codes. The handler retains cancellation after a successful fallback lookup; no Windows dialog, binding or automatic event delivery is verified.
Patient 1001, male, born 2025-01-01, clock 2025-03-01 and schedule 6–8 weeks are invented fixtures. Actual schedule, examiner/location lookup rows, BMI thresholds and centile bands are absent. Interaction scenarios explicitly invent SYNTH/UNUSED lookup rows, height range 40–60 and BMI range 10–20; these are review fixtures, not recovered production limits. Null/optional is not mandatory. PhysicalGeneral omission and field/save head discrepancy remain exactly as source, not corrected.
Examination-date Validating handler and delegate ValidateExaminationDate/CheckAgeWithinScheduleRange are source-extracted. A Text/DateTime-only double invokes the handler directly; shared cases cover future/birth/death errors, duplicate dates, warning-only age acceptance, and empty-text bypass retaining incoming cancellation. The same synthetic 6–8-week schedule and source-extracted DaysBetween/WeeksBetween methods apply; Windows binding/event delivery remain unverified.

Measurement Validating handlers from `{ui_path}` and delegate ValidateHeight/ValidateWeight/ValidateHeadCircumference are source-extracted. Text/Value-only control doubles invoke handlers synchronously with CancelEventArgs and invented height 40–60/weight 3–6 deviation bands (not recovered lookup data); scenarios prove invalid-input cancellation, empty-text bypass preserving the incoming cancellation flag, and warning-only acceptance. Windows binding, automatic event delivery and designer layout remain unverified.

UI SaveChanges from `{save_ui_path}` now executes against extracted parent Save: successful dispatch refreshes the patient UI before disabling default-tab selection; service faults and absent selected tabs return false without refreshing. Refresh is a recording double, not read-back or Windows tab/binding evidence. Shared cases assert selected DTO/context identity, stale current-tab replacement, refresh arguments/order and preserved default-tab state on failure.

Parent-delegate Save now executes source-extracted selection and fault routing against a recording service double. Success and synthetic optimistic-lock/generic faults assert exact context/result identity, return value and the error-saving prompt. The double does not save data or execute service rules; this is orchestration evidence only, not service/persistence parity.

Resource translations are absent: errors/warnings are resource identifiers, not original displayed prose. Reference save only clones accepted input and proves validator outcomes; original service transaction, entity mapping and persistence are unverified. Windows/Oracle application cannot be built from this bundle. PostgreSQL is unverified and not connected. No target or browser implementation has been generated.
''')
    put('migration-plan.md', '''# Bounded migration plan
1. Characterise: retain source identities, inspect inventory/rules, run extracted-reference scenarios. Resolve blocking coverage, repeat scope gaps with human review; do not approve current incomplete coverage by implication.
2. Approval: runner hashes source/target/reviewed artifacts and stops. Seed acceptance is not behaviour approval.
3. Convert after approval: modern .NET runtime/dependency port; retain validator/delegate structure, compatibility substitutions, same scenarios and observations. No Blazor or redesigned persistence yet.
4. Refactor after conversion parity: server-interactive Blazor and EF Core in-memory. Only KD03 selection/submission, selected synthetic patient; save then read through fresh context. Add shared failure, warning/confirmation, physical assessment, lookup/default and decline examples before approving them.
5. Gates: runner-owned nonempty tests, mechanical observation parity, build/style and browser add/read-back. Retain exact revisions/commands/diagnostics. Demonstrate lifetime-only persistence and excluded Oracle/PostgreSQL infrastructure.
''')
    put('reference/ADAPTATIONS.md', f'''# Extracted reference adaptations

- `{ui_path}`: examination-date handler is retained with public visibility and a Text/DateTime-only fixture. Delegate ValidateExaminationDate and CheckAgeWithinScheduleRange execute extracted bodies with local ValidationFault substitution; synthetic date/death/existing-result fixtures and 6–8-week schedule exercise errors and warnings. WeeksBetween and DaysBetween are recovered unchanged from `{dates_path}`; no original Windows event delivery is claimed.
- `{ui_path}`: Height, Weight and HeadCirc Validating method bodies are retained, changing only private visibility for direct invocation. Text/Value-only ControlFixture replaces proprietary numeric controls; CancelEventArgs is the runtime type. Delegate ValidateHeight/ValidateWeight/ValidateHeadCircumference bodies are extracted with local ValidationFault replacing WCF wrappers. Invented height 40–60 and weight 3–6 bands supply deviation dependencies. Shared cases assert invalid cancellation, empty-input bypass with incoming cancellation retained, and warning-only acceptance. No Windows binding, event loop, focus or layout parity is claimed.
- Complete `{validator_path}` retained verbatim except DateTime.Today -> ReferenceClock.Today (frozen fixture).
- DTO backing/property-change infrastructure replaced with same-named/type auto properties extracted from `{dto_path}`. No validator predicates replaced.
- Missing resource strings replaced with their symbolic names; fault wrappers replaced with Exceptions carrying those names. Aggregated numbered messages normalised only by removing numbering/newlines. Resource identifiers compared exactly in order.
- `{bmi_path}` CalculateBmi method retained verbatim in a small container.
- `{delegate_path}` CheckAgeWithinScheduleRange body retained verbatim; visibility made public; schedule Lazy reads fixture; Messenger records resource IDs. DaysBetween/WeeksBetween bodies recovered from `{dates_path}` and retained verbatim in ExtractedDateCalculation.cs; only the containing namespace/class is replaced. Truncation toward zero, including negative fractional days, is executable.
- Warning guard scenarios directly invoke extracted CheckDeviations/CheckBmi with runtime PropertyChangedEventArgs, observing lazy range access for null measurements, minimum dates, equal/reversed synthetic bands and unrelated/empty/null property names. No Windows event delivery or database range provenance is claimed.
- ExtractedInteractions retains BMI/decline/measurement properties and lookup/deviation/BMI method bodies except private visibility. Notifications dispatch through a synchronous PropertyChanged event subscribed to extracted CheckBmi, mirroring the source constructor subscription (not Windows controls). ExaminationDate and ResetDeviations bodies are retained, with ChildMeasurementsRange renamed to the fixture record; GetExpectedRanges records the date and supplies invented height range 40–60. Shared examples check same-day no-op, time preservation, lazy range reset and weight-setter BMI warning dispatch. Lookup retrieval supplies synthetic rows or null; invented height range 40–60 and BMI range 10–20 do not claim database provenance. Display names use symbolic enum names. ValidateAndSetExamCode retains its body with WCF fault wrappers replaced by local exceptions carrying Detail.Title; synchronous confirmation responses are fixture-controlled and recorded. A queued-response double models distinct answers to successive duplicate/code-change prompts; it does not decide whether to prompt. Shared sequence cases observe prompt order, unconsumed responses, selected code and validation state. ExaminationCode, UpdateExamDescription, ClearDataFromHiddenFields, their field properties and ResetRecommendedAgeRange are source-extracted. Shared setter cases cover blocked/same-code no-ops and entering/leaving KD03, notifications, description, hidden-field clearing and lazy schedule reset. Synthetic descriptions and a recording schedule double returning 6–8 weeks replace lookups/services; Windows controls remain unverified. Populate, all three PrependNumericsUi description methods, GetDropDownUiPositionNumber and numeric position tables are source-extracted. Synthetic lookup lists replace lazy lookup-service retrieval; repeated Populate checks prefix idempotence, unmatched codes and already-prefixed descriptions. Context and lazy ranges are observed directly; Windows binding remains unverified; parent-delegate Populate integration executes through the extracted factory method. TransferObjectBase.Lock is a storage-only string substitution, not a concurrency implementation. ExamDescription getter/setter are source-extracted; shared cases verify the stored description is unchanged while display appends the explicitly synthetic RecallText suffix only when IsRepeat is true and the current code equals OriginalExamCode (including null-description concatenation). Original resource prose and Windows binding remain unverified.
- Heart/Hips/Eyes/Testes/PhysicalGeneral properties are retained in the source-extracted hidden-field property set. Direct assignment twice and null clearing are followed by extracted ValidateOnSave; shared cases assert DTO values, unchanged siblings, no explicit delegate notifications and the source's PhysicalGeneral counting discrepancy. Byte value 2 and reason 1 are fixtures; no Windows binding, assessment lookup delivery, entity mapping or persistence is verified.
- Dropdown ValidateLocationTypeInput, ValidateExaminerTypeInput and ValidateReasonNotExaminedTypeInput EventArgs handlers are source-extracted with visibility changes and the delegate type qualifier renamed. A Text-only HlxDropDown sender double proves invalid integer text is cleared and accepted text remains verbatim (Trim affects validation only). The distinct empty examiner CancelEventArgs overload is retained and invoked explicitly: invalid text and incoming cancellation remain unchanged. These shared cases do not verify proprietary binding, overload wiring or Windows event delivery.
- ValidateNumericDescriptorEntered and its TYPE_OF_INPUT enum are retained verbatim alongside the source numeric position tables. Shared cases cover both position boundaries, zero/negative/out-of-range integers, stored-key versus UI-position differences, and permissive empty/nonnumeric/decimal/overflow inputs. Direct method invocation does not prove Windows key handling or binding.
- Examination-code Validating/ButtonClick handlers from `{ui_path}` and LookUpExamCode from `{delegate_path}` retain their bodies. Text-only control and ShowFormLookup message doubles replace Windows UI/dialog infrastructure, record offered codes and supply explicit fixture responses; they do not validate or select codes themselves. Source ValidateAndSetExamCode performs validation/confirmation. Validating cancellation is observed separately from the selected code, including successful fallback lookup with cancellation still true. Original Windows event delivery remains unverified.
- `{repeat_path}` UpdateRepeatFlags body is retained with internal -> public visibility only. RepositoryFixture supplies explicit preloaded query rows separately from local tracked rows; Include has no database side effects. Source local navigation repair and all repeat decisions execute unchanged. Synthetic rows include KD03 ties, a later same-day timestamp, KD08 family members, another patient and another prefix. Repeated execution observes idempotence. This is standalone repeat-logic evidence, not save-service/database parity; scope approval remains blocked.
- `{save_ui_path}` SaveChanges body is source-extracted unchanged. SelectedTab/currentTab are key-only fixtures; Populate is a recording refresh double observing ID, Editable, prior service dispatch and default-tab state. Shared cases use patient ID 1001, result key 42, stale current key 99 and Editable=false to distinguish arguments/selection; successful/faulting calls run extracted parent Save. The double does not reload results or establish persistence/read-back, tab layout, event delivery or Windows binding parity.
- `{lifecycle_path}` Save body is source-extracted unchanged. A recording service double observes exact context/result identity and throws explicit synthetic generic/optimistic-lock faults; shared cases assert return value, error prompt and untouched unrelated DTO. Local FaultException types replace WCF exception transport only. This proves delegate selection and error routing, not validation, transactions, mapping or persistence in the original save service.
- ExaminerCategory/ExaminerKdpCode/ExaminerType/ExaminerName and PopulateHcpDetails are source-extracted unchanged. Shared cases prove category assignments (changed/same/null) clear type/code/name/cache; refreshed retrieval uses the new category. HCP selection matches only UsedCode=Y, obtains Description/Type from explicitly synthetic cached rows, and leaves category unchanged for nonempty codes. Empty/null code invokes the category setter, clearing code to empty, type/name/category/cache without retrieval. LookupFixture adds a synthetic Type field for these dependencies; real lookup data and Windows binding/event delivery remain unverified.
- LocationType/LocationCode setters are source-extracted unchanged. Shared cases prove that changed, unchanged and null category assignments clear code/name/cache, and subsequent retrieval uses the assigned category rather than stale rows. Code assignments resolve exact cached descriptions, clear names for empty/null codes and yield null for unknown codes or absent cache without fetching rows. Synthetic descriptions are fixture data; Windows binding/event delivery remain unverified.
- GetLocationList/GetExaminerList/GetUsedExaminerList bodies are source-extracted; only List<LookupsSubTO> becomes List<LookupFixture> (Code/UsedCode/Description record). Recording lookup-service double returns unfiltered synthetic SYNTH/Y and UNUSED/N rows or throws the local FaultException substitute. Shared cases invoke twice and observe missing-category prompts, cache reuse, exact service arguments, used-only filtering and retry after faults. Real lookup data, service transport and Windows binding remain unverified.
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
    js('stage.json', {'reviewFiles': reviewed, 'blockingGaps': ['Delegate interaction coverage incomplete', 'Repeat-flag scope unresolved'],
                      'checks': [{'command': {'executable': sys.executable, 'arguments': ['verify.py'], 'timeoutSeconds': 600}, 'results': 'results.json'}]})


if __name__ == '__main__':
    generate(json.loads(Path(sys.argv[-1]).read_text()))
