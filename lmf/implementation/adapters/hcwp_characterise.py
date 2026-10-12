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
    dropdown_path, dropdown_source = find('/PopulateDropDown.cs')
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
    for name in ('LocationType', 'LocationCode', 'ExaminerKdpCode', 'ExaminerType', 'ExaminerCategory', 'ExaminerName',
                 'ReasonNotExamined', 'Consent', 'CoreComponentOffered', 'Reschedule', 'WithdrawConsent', 'Origin'):
        members += '\n' + re.search(r'        public [^\n]+ ' + name + r'\s*\{.*?\n        \}', delegate, re.S).group()
    members += '\n' + method(delegate, 'PopulateHcpDetails')
    members += '\n' + re.search(r'        public string ResultTabText =>[^\n]+', delegate).group()
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
    lifecycle_members = '\n'.join(method(lifecycle, n) for n in ('GetKdpResults', 'AddNewKdpResult', 'ConfirmCancelChanges', 'GetNewKdpExaminationResultDelegate', 'Save'))
    lifecycle_members = lifecycle_members.replace('FaultException<ValidationWarningFault>', 'ValidationWarningFault').replace('DateTime.Now', 'ReferenceClock.Now')
    put('reference/ExtractedLifecycle.cs', (ROOT / 'lifecycle-support.cs.txt').read_text().replace('__MEMBERS__', lifecycle_members))
    save_members = method(save_ui, 'SaveChanges') + '\n' + method(save_ui, 'hlxAdminTabControlKdpExamination_ChangingSelectedTab').replace('private void', 'public void')
    save_members += '\n' + '\n'.join(line for line in save_ui.splitlines() if 'private const string NewTab' in line)
    save_members += '\n' + method(save_ui, 'toolStripButtonInsert_Click').replace('private void', 'public void').replace('new UITabPage', 'new SaveTabFixture')
    save_members += '\n' + method(save_ui, 'ProcessTabsForEachExam').replace('private void', 'public void').replace('new UITabPage', 'new SaveTabFixture')
    save_members += '\n' + method(save_ui, 'SelectTabPage').replace('private void', 'public void')
    put('reference/ExtractedSaveControl.cs', (ROOT / 'save-control-support.cs.txt').read_text().replace('__MEMBERS__', save_members))
    populate_members = method(save_ui, 'Populate') + '\n' + method(save_ui, 'ProcessTabsForEachExam').replace('new UITabPage', 'new SaveTabFixture')
    put('reference/ExtractedPopulateControl.cs', (ROOT / 'populate-control-support.cs.txt').read_text().replace('__MEMBERS__', populate_members))
    content_member = method(save_ui, 'SetUpTabPageContent').replace('private void', 'public void').replace('UITabPage', 'ContentTabFixture')
    put('reference/ExtractedTabContentControl.cs', (ROOT / 'tab-content-support.cs.txt').read_text().replace('__MEMBERS__', content_member))
    setup_members = '\n'.join(method(save_ui, n).replace('private void', 'public void') for n in ('SetUpTabPages', 'SelectTabPage'))
    put('reference/ExtractedTabSetupControl.cs', (ROOT / 'tab-setup-support.cs.txt').read_text().replace('__MEMBERS__', setup_members))
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
    put('reference/ExtractedDropdownSelection.cs', '''using System.Collections.Generic;
// Storage-only items/selected-value fixture; no binding or Windows event delivery.
public class SelectionItemFixture { public object Value; }
public class SelectionDropdownFixture {
 public object SelectedValue;
 public int SelectedIndex = 999;
 public List<SelectionItemFixture> Items = new();
}
public class ExtractedDropdownSelection {
''' + method(ui, 'getSelectedIndexOfSelectedValue').replace('private int', 'public int')
        .replace('HlxDropDown', 'SelectionDropdownFixture')
        .replace('Janus.Windows.EditControls.UIComboBoxItem', 'SelectionItemFixture') + '\n}\n')
    refresh = method(ui, 'manuallyRefreshSelectedDropdownValues').replace('private void', 'public void')
    refresh_fields = sorted(set(re.findall(r'hlxDropDown\w+', refresh)))
    put('reference/ExtractedDropdownRefresh.cs', 'public class ExtractedDropdownRefresh : ExtractedDropdownSelection {\n'
        + '\n'.join(' public SelectionDropdownFixture ' + name + ' = new();' for name in refresh_fields)
        + '\n' + refresh + '\n}\n')
    put('reference/ExtractedSaveButton.cs', '''using System;
// Recording Save dispatch only; no Windows events or persistence.
public class ExtractedSaveButton {
 public int SaveCalls;
 public bool ThrowOnSave;
 public readonly InvalidOperationException Failure = new("SYNTH save failure");
 public void Save() { SaveCalls++; if (ThrowOnSave) throw Failure; }
''' + method(save_ui, 'toolStripButtonSave_Click').replace('private void', 'public void') + '\n}\n')
    put('reference/ExtractedUiLoad.cs', '''using System;
// Direct load-handler invocation only; no Windows lifecycle/event delivery.
public class ExtractedUiLoad {
 public bool setDefaultTabPage;
''' + method(save_ui, 'ucHLXKdpExaminations_Load').replace('private void', 'public void') + '\n}\n')
    dropdown_list = method(dropdown_source, 'Populate', 'UIComboBox combBox, List<LookupsSubTO> _list, bool addNullRow')
    put('reference/ExtractedDropdownList.cs', '''using System.Collections.Generic;
// Storage-only Items.Add/Clear, not Janus selection or binding.
public record DropdownRowFixture(string Description, string Code);
public record DropdownListItemFixture(string Text, object Value);
public class DropdownItemsFixture : List<DropdownListItemFixture> {
 public void Add(string text, object value) { Add(new(text, value)); }
}
public class DropdownListFixture { public DropdownItemsFixture Items = new(); }
public static class ExtractedDropdownList {
''' + dropdown_list.replace('UIComboBox', 'DropdownListFixture').replace('LookupsSubTO', 'DropdownRowFixture') + '\n}\n')
    dictionary_members = '\n'.join(method(dropdown_source, 'Populate',
        'UIComboBox combBox, Dictionary<string, ' + value_type + '> values')
        for value_type in ('byte?', 'string'))
    put('reference/ExtractedDropdownDictionary.cs', 'using System.Collections.Generic;\n'
        + 'public static class ExtractedDropdownDictionary {\n'
        + dictionary_members.replace('UIComboBox', 'DropdownListFixture') + '\n}\n')
    put('reference/ExtractedChildFocus.cs', '''// Text storage and recording Focus only; no Windows focus/event delivery.
public class FocusTextFixture {
 public string Text = "";
 public int Calls;
 public void Focus() { Calls++; }
}
public class ExtractedChildFocus {
 public FocusTextFixture hlxTextBoxExamCode = new();
''' + method(ui, 'FocusHlxTextBoxExamCode') + '\n}\n')
    child_populate = method(ui, 'Populate').replace('KdpExaminationResultDelegate', 'ChildDelegateFixture')
    child_properties = sorted(set(re.findall(r'kdpExaminationResultDelegate\.(\w+)', child_populate)) - {'DskScores'})
    child_fields = sorted(set(re.findall(r'hlxDropDown\w+', child_populate)))
    child_populate = re.sub(r'LookupsUtility\.Dsk\.(\w+)', r'"\1"', child_populate)
    put('reference/ExtractedChildPopulate.cs', '''using System.Collections.Generic;
// Recording-only binding/dropdown fixtures, not Windows binding or lookup rules.
public class ChildDelegateFixture {
 public Dictionary<string, object> Scores = new();
 public object DskScores(string key) { if (!Scores.ContainsKey(key)) Scores[key] = new object(); return Scores[key]; }
''' + '\n'.join(' public object ' + name + ' = new object();' for name in child_properties) + '''
}
public class ChildBindingFixture { public object DataSource; }
public class ChildDropdownFixture { public object InvalidValues; public object OriginalValue; public string Name; }
public class ChildPopulateCall { public string Field; public object Values; public bool? AddNull; }
public class ChildPopulateRecorder {
 public List<ChildPopulateCall> Calls = new();
 public void Populate(ChildDropdownFixture field, object values, bool? addNull = null) {
  Calls.Add(new() { Field = field.Name, Values = values, AddNull = addNull });
 }
}
public class ExtractedChildPopulate {
 public ChildDelegateFixture kdpExaminationResultDelegate;
 public ChildBindingFixture bindingSourceKdpExaminationResults = new();
 public bool dropDownsPopulated;
 public ChildPopulateRecorder PopulateDropDown = new();
 public List<object[]> Refreshes = new();
 public void manuallyRefreshSelectedDropdownValues() { Refreshes.Add(new object[] { kdpExaminationResultDelegate, bindingSourceKdpExaminationResults.DataSource, dropDownsPopulated, PopulateDropDown.Calls.Count, hlxDropDownExaminerType.InvalidValues, hlxDropDownExaminerType.OriginalValue }); }
''' + '\n'.join(' public ChildDropdownFixture ' + name + ' = new() { Name = "' + name + '" };' for name in child_fields)
        + '\n' + child_populate + '\n}\n')
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
    for name, calls in [
        ('replace', [{'rows': [{'Description': 'SYNTH first', 'Code': 'A'}, {'Description': 'SYNTH duplicate', 'Code': 'A'}], 'addNull': True},
                     {'rows': [{'Description': 'SYNTH second', 'Code': 'B'}], 'addNull': False}]),
        ('clear', [{'rows': [{'Description': '', 'Code': None}], 'addNull': False}, {'rows': [], 'addNull': False}]),
        ('empty-null', [{'rows': [], 'addNull': True}, {'rows': [], 'addNull': True}]),
    ]:
        add('KD03-dropdown-list-' + name, 'dropdown-list', {**base, 'calls': calls},
            items=[[{'text': row['Description'], 'value': row['Code']} for row in call['rows']]
                   + ([{'text': '', 'value': None}] if call['addNull'] else []) for call in calls],
            collectionSame=[True, True], sourceSame=[True, True])
    for kind in ('byte', 'string'):
        first = [{'text': ' SYNTH first ', 'value': 0 if kind == 'byte' else ''},
                 {'text': '', 'value': None},
                 {'text': 'SYNTH last', 'value': 255 if kind == 'byte' else ' verbatim '}]
        second = [{'text': 'replacement', 'value': 7 if kind == 'byte' else 'new'}]
        for name, initial_items, calls in [
            ('populate-once', [], [first, second]),
            ('preseeded', [{'text': 'SENTINEL', 'value': 'stale'}], [first, second]),
            ('empty-then-fill', [], [[], first]),
        ]:
            expected = initial_items
            snapshots = []
            for call in calls:
                if not expected:
                    expected = call
                snapshots.append(expected)
            add('KD03-dropdown-dictionary-' + kind + '-' + name, 'dropdown-dictionary',
                {**base, 'kind': kind, 'initialItems': initial_items, 'calls': calls},
                items=snapshots, collectionSame=[True, True], itemIdentitiesSame=[True, True],
                sourceSame=[True, True])
    for name, codes in [('supported', ['KD03', 'KD03']),
                        ('other-contacts', ['KD08', 'KD09', 'KD11', 'KD01', 'KD04', 'KD07', 'KD10']),
                        ('near-matches', ['KD03', 'kd03', 'KD03 ', ' KD03', 'KD030', '', None, 'UNKNOWN', 'KD03'])]:
        add('KD03-contact-classification-' + name, 'contact-classification',
            {**base, 'codes': codes}, classifications=[{
                'sixToEight': code == 'KD03',
                'fifteenOrTwentySeven': code in ('KD08', 'KD09'),
                'dsk': code in ('KD11', 'KD08', 'KD09'),
                'rsk': code in ('KD01', 'KD04', 'KD07', 'KD08', 'KD09', 'KD10')
            } for code in codes])
    for fail_first in (False, True):
        add('KD03-save-button-' + ('fault-retry' if fail_first else 'success'), 'save-button',
            {**base, 'failFirst': fail_first},
            saveCounts=[1, 2], exceptionIdentity=[fail_first, False])
    for initial in (False, True):
        add('KD03-ui-load-' + str(initial).lower(), 'ui-load',
            {**base, 'defaultStates': [initial, not initial]}, defaultStates=[False, False])
    for name, texts, counts in [('empty', ['', ''], [1, 2]),
                                ('filled', ['KD03', 'KD03'], [0, 0]),
                                ('whitespace', [' ', '\t'], [0, 0]),
                                ('cleared', ['KD03', ''], [0, 1]),
                                ('filled-after-empty', ['', 'KD03'], [1, 1])]:
        add('KD03-child-focus-' + name, 'child-focus', {**base, 'texts': texts},
            focusCounts=counts, textSame=[True, True], controlSame=[True, True])
    child_calls = re.findall(r'PopulateDropDown.Populate\((hlxDropDown\w+), kdpExaminationResultDelegate\.(\w+)(?:\("(\w+)"\))?(, true)?\);', child_populate)
    for populated in (False, True):
        add('KD03-child-populate-' + ('cached' if populated else 'fresh'), 'child-populate',
            {**base, 'populated': populated}, bindings=[True, True],
            calls=[] if populated else [{'field': field, 'source': prop + (':' + key if key else ''), 'addNull': True if null else None} for field, prop, key, null in child_calls],
            refreshes=0 if populated else 1, refreshState=True,
            metadataSame=True, populated=True)
    for mode, ids in [('unordered', [42, 99, 77]), ('ties', [77, 42, 99]), ('empty', [])]:
        add(f'KD03-get-results-{mode}', 'get-results', {**base, 'mode': mode},
            ids=ids, refreshIds=[88], calls=[1001, 2002], sameDtos=True,
            sameContext=True, lazyRanges=True, replaced=True)
    for kind in ('location', 'examiner'):
        request = 'Locations||5' if kind == 'location' else 'Examiners||18|N'
        missing = 'NoLocationTypeMessage' if kind == 'location' else 'NoExaminerTypeMessage'
        invalid = 'InvalidLocationCodeMessage' if kind == 'location' else 'InvalidHcpCodeMessage'
        invalid_prompt = 'InvalidLocationCodePrompt' if kind == 'location' else 'InvalidHcpCodePrompt'
        missing_prompt = 'NoLocationTypePrompt' if kind == 'location' else 'NoExaminerTypePrompt'
        fault_prompt = 'ErrorGettingLocationListPrompt' if kind == 'location' else 'ErrorGettingExaminerListPrompt'
        for mode, code, valid, errors, prompts, requests, cached in [
            ('empty-code', '', [True, True], [], [], [], False),
            ('null-code', None, [True, True], [], [], [], False),
            ('missing', 'MISSING', [True, True], [missing] * 2, [missing_prompt] * 2, [], False),
            ('missing-cached', 'MISSING', [False, False], [missing, invalid] * 2,
             [missing_prompt, invalid_prompt] * 2, [], True),
            ('fault-recovery', 'MISSING', [True, False], ['synthetic-lookup-fault', invalid],
             [fault_prompt, invalid_prompt], [request] * 2, True),
            ('empty-rows', 'MISSING', [False, False], [invalid] * 2,
             [invalid_prompt] * 2, [request], True),
        ]:
            category = {} if mode in ('missing', 'missing-cached', 'empty-code', 'null-code') else {'LocationType': 5, 'ExaminerCategory': '18'}
            add(f'KD03-lookup-validation-{kind}-{mode}', 'lookup-validation-lifecycle',
                {**base, **category, 'kind': kind, 'mode': mode, 'code': code}, errors,
                valid=valid, prompts=prompts, requests=requests, cached=cached)
    common_fields = {'ReasonNotExamined': 'ReasonNotExamined', 'Consent': 'Consent',
                     'CoreComponentOffered': 'CoreComponent', 'Reschedule': 'Reschedule',
                     'WithdrawConsent': 'WithdrawConsent', 'Origin': 'Origin'}
    common_initial = {'ReasonNotExamined': 'sentinel-reason', 'Consent': 'sentinel-consent',
                      'CoreComponent': 1, 'Reschedule': 'sentinel-reschedule',
                      'WithdrawConsent': False, 'Origin': 1}
    for name, current, defaults, selected in [
        ('default-then-current', '99', [True, False], ['42', '99']),
        ('current-then-default', '99', [False, True], ['99', '42']),
        ('null-current', None, [False, True], [None, '42']),
        ('detached-current', '77', [False, False], ['77', '77']),
    ]:
        add('KD03-ui-tab-select-' + name, 'ui-tab-select',
            {'current': current, 'defaults': defaults}, selected=selected,
            exactIdentity=True, currentUnchanged=True, keys=['42', '99'], setupCalls=0,
            collectionIdentities=[True] * len(defaults), orderedTabIdentities=[True] * len(defaults))
    for field, stored_field in common_fields.items():
        value = True if field == 'WithdrawConsent' else 2 if field in ('CoreComponentOffered', 'Origin') else 'synthetic-value'
        for mode, clear in [('value', False), ('cleared', True)]:
            final = (False if field == 'WithdrawConsent' else None) if clear else value
            stored = {**common_initial, stored_field: final}
            add(f'KD03-common-{field}-{mode}', 'common-recording',
                {**base, **common_initial, 'field': field, 'storedField': stored_field,
                 'value': value, 'clear': clear}, assigned=value, displayed=final,
                stored=stored, notifications=[])
    for name, summaries, counts, visibility, setup_visibility in [
        ('ordinary', [False, False], [3, 1], [True, True], [True, True]),
        ('summary-then-ordinary', [True, False], [3, 1], [False, False], [True, False]),
        ('ordinary-then-summary', [False, True], [3, 1], [True, False], [True, True]),
        ('empty-summary', [True, True], [0, 0], [False, False], [True, False]),
    ]:
        add('KD03-ui-populate-' + name, 'ui-populate',
            {'summaries': summaries, 'counts': counts},
            ids=[1001.5, 2002.5], editable=[False, True], calls=[1002, 2002],
            resultIds=[[42 + i for i in range(count)] for count in counts],
            tabCounts=counts, visible=visibility, sameDtos=[True, True],
            setups=[{'Id': ident, 'Editable': edit, 'Loads': index + 1,
                     'Results': counts[index], 'Tabs': counts[index], 'Processing': False,
                     'NavigatorVisible': setup_visibility[index]}
                    for index, (ident, edit) in enumerate([(1001.5, False), (2002.5, True)])])
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
    for name, items, selected, indices in [
        ('first-duplicate', ['5', 2, 5], [5, '2'], [0, 1]),
        ('last', [5, 2, 22], ['22', 5], [2, 0]),
        ('unknown', [5, 2], ['99', '2'], [-1, 1]),
        ('null', [5, 2], [None, 5], [-1, 0]),
        ('empty-items', [], [5, None], [-1, -1]),
        ('empty-value', ['', 2], ['', None], [0, -1]),
        ('verbatim', [' 5 ', 5], ['5', ' 5 '], [1, 0]),
    ]:
        add('KD03-dropdown-selection-' + name, 'dropdown-selection',
            {**base, 'items': items, 'selectedValues': selected}, indices=indices,
            collectionSame=[True, True], itemIdentitiesSame=[True, True], selectedValuesSame=[True, True])
    for name in ('distinct', 'missing', 'empty'):
        values = [[i, 32 - i] for i in range(33)] if name == 'distinct' else [[None, 'unknown'] for _ in range(33)]
        expected = [[i, 32 - i] for i in range(33)] if name == 'distinct' else [[-1, -1] for _ in range(33)]
        # Preserve the supplied source discrepancy, not the apparent intended wiring.
        expected[refresh_fields.index('hlxDropDownEngagement')] = expected[refresh_fields.index('hlxDropDownDomesticViolence')][:]
        add('KD03-dropdown-refresh-' + name, 'dropdown-refresh',
            {**base, 'fields': refresh_fields, 'values': values, 'emptyItems': name == 'empty'},
            indices=[[row[call] for row in expected] for call in range(2)],
            inputsSame=[True, True])
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
    for name, code, original, repeat, next_code, next_repeat in [
        ('nonrepeat-to-repeat', 'KD03', 'KD03', False, 'KD03', True),
        ('repeat-to-nonrepeat', 'KD03', 'KD03', True, 'KD03', False),
        ('changed-code', 'KD03', 'KD08', True, 'KD08', True),
        ('missing-original', 'KD03', None, True, 'KD03', True),
        ('null-code', None, 'KD03', True, None, False),
        ('empty-code', '', None, False, '', True),
    ]:
        add('KD03-tab-heading-' + name, 'tab-heading',
            {**base, 'ExaminationCode': code, 'OriginalExamCode': original, 'IsRepeat': repeat,
             'nextCode': next_code, 'nextRepeat': next_repeat},
            headings=[(code or '') + (' [synthetic recall flag]' if repeat else ''),
                      (next_code or '') + (' [synthetic recall flag]' if next_repeat else '')],
            codes=[code, next_code], repeats=[repeat, next_repeat], notifications=[])
    for kind in ('location', 'examiner'):
        invalid = 'InvalidLocationCode' if kind == 'location' else 'InvalidHcpCode'
        add('KD03-lookup-exact-' + kind, 'lookup-validation-exact',
            {**base, 'kind': kind, 'LocationType': 5, 'ExaminerCategory': '18',
             'codes': ['SYNTH', 'synth', ' SYNTH', 'SYNTH ', 'SYN', '', None, 'UNUSED', 'SYNTH']},
            [invalid + 'Message'] * 4 + (['UnusedExaminerCodeMessage'] if kind == 'examiner' else []),
            valid=[True, False, False, False, False, True, True, kind == 'location', True],
            cacheSame=[True] * 9, requests=['Locations||5' if kind == 'location' else 'Examiners||18|N'],
            prompts=[invalid + 'Prompt'] * 4 + (['UnusedExaminerCodePrompt'] if kind == 'examiner' else []))
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
    for name, existing_id, existing_code, date, blocked in [
        ('same-day-other-result', 42, 'KD03', '2025-02-19T23:59:59', True),
        ('same-day-self', 7, 'KD03', '2025-02-19T23:59:59', False),
        ('prior-day-self', 7, 'KD03', '2025-02-18', False),
        ('same-day-other-code', 42, 'KD08', '2025-02-19', False),
    ]:
        add('KD03-code-identity-' + name, 'code-selection-sequence',
            {**base, 'ExaminationCode': 'KD08', 'resultId': 7, 'responses': [True],
             'existingResult': {'id': existing_id, 'code': existing_code, 'date': date}},
            ['KdpResultAlreadyEnteredMessage'] if blocked else [],
            selected='KD08' if blocked else 'KD03', valid=not blocked, validated=not blocked,
            confirmations=[] if blocked else ['KdpResultsExamCodeChangeConfirmationMessage'],
            remainingResponses=1 if blocked else 0)
    add('KD03-code-invalid', 'code-selection', {**base, 'code': 'INVALID'},
        ['KdpInvalidExamCodeMessage'], selected='KD03', valid=False, confirmations=[])
    for name, key, matched in [('existing', '42', True), ('negative', '-42', True), ('new', '0', True),
                               ('missing-existing', '77', False), ('missing-new', '0', False),
                               ('empty', '', False), ('null-key', None, False), ('null-tab', None, False)]:
        active = matched or (key is not None and key != '')
        counts = [1, 1] if matched and key != '0' else [2, 3] if matched else [0, 0] if active and key != '0' else [1, 1]
        add('KD03-ui-tab-content-' + name, 'ui-tab-content',
            {'key': key, 'matched': matched, 'nullTab': name == 'null-tab'},
            counts=[0, 0] if name == 'null-tab' else counts,
            sentinelRetained=[not active or key == '0'] * 2 if name != 'null-tab' else [False, False],
            created=[matched, matched], exactResult=[True, True],
            currentIdentity=[True, True], childIdentity=[True, True], orderedControlsIdentities=[True, True],
            dockFill=[True, True], focusCalls=[1, 1] if matched else [0, 0])
    for name, keys, ids, default, current in [
        ('default', ['stale', 'old', 'trailing'], [42, 99], True, 1),
        ('current', ['stale', 'old'], [-142, -199], False, 1),
        ('new', ['0', 'old'], [0, 99], True, 1),
        ('null-current', ['stale', 'old'], [42, 99], False, None),
        ('empty', [], [], True, None),
    ]:
        snapshots = [[str(ids[i] + shift) if i < len(ids) and ids[i] else key
                      for i, key in enumerate(keys)] for shift in (0, 100)]
        texts = [[('SYNTH-' + str(ids[i] + shift)) if i < len(ids) and ids[i] else 'original-' + str(i)
                  for i in range(len(keys))] for shift in (0, 100)]
        selected_index = 0 if default and keys else current
        selected = [snapshot[selected_index] if selected_index is not None else None for snapshot in snapshots] if keys else []
        add('KD03-ui-tab-setup-' + name, 'ui-tab-setup',
            {'keys': keys, 'ids': ids, 'default': default, 'current': current},
            keys=snapshots, texts=texts, selected=selected,
            preparationCounts=[1, 1] if keys else [0, 0],
            controlIdentities=[True, True], controlIdentitiesAtPreparation=[True, True] if keys else [],
            resultCollectionIdentities=[True, True], resultOrderedIdentities=[True, True],
            resultCollectionIdentitiesAtPreparation=[True, True] if keys else [],
            resultOrderedIdentitiesAtPreparation=[True, True] if keys else [],
            keysAtPreparation=snapshots if keys else [], textsAtPreparation=texts if keys else [],
            selectedIdentitiesAtPreparation=[True, True] if keys else [],
            currentIdentitiesAtPreparation=[True, True] if keys else [],
            defaultStatesAtPreparation=[default, default] if keys else [],
            orderedIdentitiesAtPreparation=[True, True] if keys else [],
            collectionIdentitiesAtPreparation=[True, True] if keys else [],
            collectionIdentity=True, collectionIdentities=[True, True], orderedIdentities=[True, True], exactSelection=True,
            currentIdentities=[True, True], defaultStates=[default, default],
            currentUnchanged=True, defaultUnchanged=True)
    for name, processing, selected, page, response, initial in [
        ('processing', True, '42', '99', True, False),
        ('no-selected', False, None, '99', True, True),
        ('no-page', False, '42', None, True, False),
        ('empty-key', False, '42', '', True, False),
        ('reject', False, '42', '99', False, False),
        ('accept', False, '42', '99', True, False),
        ('accept-preserves-cancel', False, '42', '99', True, True),
    ]:
        confirms = not processing and selected is not None and bool(page)
        prepared = confirms and response
        add('KD03-tab-change-' + name, 'tab-change',
            {'processing': processing, 'selected': selected, 'page': page,
             'response': response, 'initialCancel': initial},
            cancelled=initial if processing or selected is None or prepared else True,
            confirmations=['ExamResultsConfirmCancelMessage'] if confirms else [],
            reloadCalls=[42] if prepared else [], height=55 if prepared else 99,
            prepared=[page] if prepared else [], reloadsAtPreparation=[1] if prepared else [],
            selected=selected)
    for name, selected, changed, empty, initial in [
        ('unchanged', '42', False, False, False),
        ('new-result', '0', True, False, False),
        ('negative-key', '-1', True, False, False),
        ('empty-results', '42', True, True, False),
        ('unchanged-preserves-cancel', '42', False, False, True),
    ]:
        add('KD03-tab-change-' + name, 'tab-change',
            {'processing': False, 'selected': selected, 'page': '99', 'response': False,
             'initialCancel': initial, 'changed': changed, 'emptyResults': empty},
            cancelled=initial, confirmations=[], reloadCalls=[], height=99,
            prepared=['99'], reloadsAtPreparation=[0], selected=selected)
    for name, keys, consent in [('empty', [], True), ('existing', ['42'], True),
                                ('first-new', ['0', '42'], True),
                                ('later-new', ['42', '0'], True), ('no-consent', ['42'], False)]:
        inserts = not keys or keys[0] != '0'
        final_keys = ['0'] + keys if inserts else keys
        add('KD03-ui-insert-' + name, 'ui-insert', {'keys': keys, 'hasConsentFixture': consent},
            warnings=['NoConsentMessage'] if inserts and not consent else [],
            keys=final_keys, heading='New Result' if inserts else None, defaultTab=True,
            resultIds=[0, 42] if inserts else [42], selected='42',
            resultsAtSetup=[2] if inserts else [], keysAtSetup=[final_keys] if inserts else [],
            confirmations=[], defaults=({'ClientId': 1001, 'Origin': 2, 'Reschedule': 'N'} if inserts else None))
    for name, keys, counts in [('grow-shrink', [], [3, 1]),
                               ('shrink-grow', ['42', '99', '77'], [1, 3]),
                               ('unchanged', ['42', '99'], [2, 2]),
                               ('clear', ['42', '99'], [0, 0]),
                               ('empty', [], [0, 0])]:
        snapshots = []
        current = keys[:]
        for count in counts:
            current = (current + [None] * max(0, count - len(current)))[:count]
            snapshots.append(current[:])
        add('KD03-ui-tab-count-' + name, 'ui-tab-count', {'keys': keys, 'counts': counts},
            snapshots=snapshots, retainedIdentity=True, selectedUnchanged=True,
            processingStates=[False, False], defaultTab=False, setupCalls=0, serviceCalls=0)
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
    for name, changed, response in [('accept', True, True), ('reject', True, False), ('unchanged', False, False)]:
        reload = changed and response
        add('KD03-cancel-selected-' + name, 'cancel-changes',
            {'id': 42, 'changed': changed, 'response': response, 'empty': False, 'siblingChanged': not changed},
            allowed=response if changed else True, reloadCalls=[42] if reload else [],
            height=55 if reload else 99, replaced=reload, selectedIsStored=reload, siblingUnchanged=True,
            confirmations=['ExamResultsConfirmCancelMessage'] if changed else [])
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
- `ValidateExamCodeForDuplicates` warns for same code on another date; delegate confirmation can cancel code selection. `ValidateKdpConsent` warns, not a mandatory save predicate. Extracted code-selection orchestration exercises accepting/rejecting duplicate and code-change confirmations separately and in sequence. Rejecting the duplicate prompt stops before the change prompt; accepting the duplicate but rejecting the change leaves KD08 selected and validation false; only accepting both selects KD03. Code-selection identity fixtures also prove same-calendar-day duplicate rejection despite differing times, before any confirmation; the current result is excluded from both date errors and duplicate-code warnings, and another code on that date does not block selection. Remaining Windows lifecycle behaviour is a documented limitation.
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
`{delegate_path}` ResultTabText displays ExaminationCode plus RecallFlag whenever the DTO IsRepeat is true, independently of OriginalExamCode. Extracted getter scenarios cover repeat toggles, changed/missing original codes and null/empty codes; the suffix resource is a labelled synthetic fixture. This is distinct from the original-code guard on ExamDescription, and does not establish Windows tab binding or resource prose parity.

Save also calls ExaminationsCrudManager.UpdateRepeatFlags, UpdateAppointmentStatuses, ClearProducedRecalls. Appointment/recall processing is intentionally excluded. Repeat-flag recalculation for the selected patient's KD03 results is in scope. Extracted UpdateRepeatFlags proves that the requested code selects its two-character family, groups by exact code and patient, marks every earliest exact timestamp N (including ties), and later timestamps Y. KD03 calls can therefore inspect and repair flags for other exact codes in the KD family; effects on unsupported contact types are outside this slice. Shared examples also cover patient isolation, short/unmatched prefixes, local navigation repair and idempotence. Existing-result fixtures are preserved for repeat flags and duplicates. This is NOT full save-service parity.
Oracle IDs, triggers, locks, EF6 mappings, schedule, centile bands, general options, lookup services, messenger and Windows controls are unavailable infrastructure. Source files and schema are retained for inspection, not claimed executable. Editing/locking, appointments, recall, patient search and database migration are outside scope.
''')
    put('gaps.md', f'''# Gaps and assumptions
## Blocking
None for the agreed KD03 Characterise scope.

## Non-blocking / review assumptions

Extracted examination-date, measurement, Populate, examination-code, new-result, cancellation, confirmation, decline, lookup, BMI and deviation paths provide executable evidence for the scoped workflow. Full delegate and original Windows lifecycle parity is not claimed. Real Windows controls, binding/event delivery and original DTO change tracking remain unverified.

Repeat-flag recalculation for the selected patient's KD03 results is included. Existing shared scenarios cover patient isolation, exact-code grouping, date ordering and ties, local navigation repair and idempotence. The in-memory repository fixture does not establish EF6/Oracle loading, transaction or concurrency parity. Appointment and recall processing remain excluded.

Recovered `{dates_path}` DaysBetween/WeeksBetween truncates elapsed days toward zero before division by 7. Both bodies are extracted unchanged; fractional-day and negative-interval scenarios protect that behaviour.

Measurement assignment scenarios execute each retained Height/Weight/HeadCircumference setter twice, including unchanged and null values. They observe DTO values, calculated BMI, range status, ordered notifications and repeated warning dispatch. Decline scenarios also observe required-state and ordered notifications on both checking and unchecking; either action clears the measurement. These are synchronous delegate observations, not Windows event/binding evidence.

Child-control Populate is retained with its delegate type renamed to a recording fixture and Dsk enum arguments represented by symbolic strings. Fresh/cached shared cases call it twice with distinct delegate objects: DataSource and delegate rebind on every call, while ordered dropdown setup, examiner metadata and refresh happen only on the first uncached call. Lookup properties are opaque synthetic objects; the recorder observes exact supplied references and nullable add-null arguments but does not populate controls or implement lookup rules. Refresh records setup-time binding/flag/count/metadata, not Windows selection delivery; separately extracted refresh logic remains independently tested. Full Windows binding and delegate lifecycle remain documented limitations.

Source discrepancy: `{ui_path}` manuallyRefreshSelectedDropdownValues assigns Engagement.SelectedIndex from DomesticViolence's selection rather than Engagement's. Three extracted orchestration scenarios preserve this wiring across repeated calls (distinct indices, null/unknown values, empty lists). This is UI refresh evidence, not a new recording rule; any correction requires reviewed behavioural adjustment. The storage-only dropdown doubles do not establish Windows binding or automatic event delivery.

GetKdpResults is source-extracted: shared cases check descending examination timestamps, stable equal-date ordering, empty lists and a second patient refresh replacing stale delegates. Recording GetKdpExamination returns explicit synthetic context/list objects without sorting; DTO identity, patient context, existing-list identity and lazy ranges are observed after source Populate. Real service retrieval, Windows binding and persistence remain unverified.

Lookup validation lifecycle scenarios invoke retained ValidateLocationCode/ValidateExaminerCode twice: null/empty codes bypass even missing-category prompts; missing categories with no cache accept unknown codes but report errors, whereas stale cached rows still reject them; a service fault accepts the first unknown code, then successful retry rejects it; empty retrieved rows reject and remain cached. These are source-observed permissive validation outcomes, not evidence that save is safe during dependency failure. Explicit synthetic rows/faults and direct invocation do not establish Windows binding or service/persistence parity.

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
1. Characterise: retain source identities, inspect inventory/rules, run extracted-reference scenarios. The agreed KD03 scenarios must pass; remaining Windows lifecycle and excluded-infrastructure limitations are non-blocking when documented. Repeat-flag scope is agreed in the seed. Stop awaiting explicit human approval of this generated revision.
2. Approval: runner hashes source/target/reviewed artifacts and stops. Seed acceptance is not behaviour approval.
3. Convert after approval: modern .NET runtime/dependency port; retain validator/delegate structure, compatibility substitutions, same scenarios and observations. No Blazor or redesigned persistence yet.
4. Refactor after conversion parity: server-interactive Blazor and EF Core in-memory. Only KD03 selection/submission, selected synthetic patient; save then read through fresh context. Add shared failure, warning/confirmation, physical assessment, lookup/default and decline examples before approving them.
5. Gates: runner-owned nonempty tests, mechanical observation parity, build/style and browser add/read-back. Retain exact revisions/commands/diagnostics. Demonstrate lifetime-only persistence and excluded Oracle/PostgreSQL infrastructure.
''')
    put('reference/ADAPTATIONS.md', f'''# Extracted reference adaptations

- `{ui_path}` child-control Populate retains its body with KdpExaminationResultDelegate renamed to ChildDelegateFixture and LookupsUtility.Dsk enum arguments replaced by their symbolic strings. Opaque synthetic lookup objects and a recording PopulateDropDown substitute observe all 33 ordered calls, exact first-delegate lookup references and add-null flags; they do not implement list population or business rules. Two shared cases (fresh/cached) invoke twice with distinct delegates, verifying that binding/delegate assignment precede the cache guard, setup/metadata/refresh occur once only on an uncached control, and second-call rebinding does not replace the first examiner metadata. Refresh records binding, setup count, metadata and populated flag at dispatch; it does not deliver Windows events. Mutations guarding rebinding or removing the cache guard fail both cases. This is orchestration evidence only; full Windows binding and child/delegate integration parity remain documented limitations.
- `{ui_path}` manuallyRefreshSelectedDropdownValues retains its body with public visibility. A separate harness reuses the extracted selection helper and supplies storage-only dropdowns. Three shared scenarios invoke twice with distinct per-control indices, null/unknown values and empty lists; all 33 destination indices and unchanged control/item/value references are observed. Engagement reads DomesticViolence's selected index in the supplied source; this discrepancy is preserved and explicitly tested, not corrected. Synthetic 33-item lists are not lookup data. SelectedIndex assignment does not simulate Windows binding, selection events or automatic refresh delivery; those remain documented limitations.

- `{ui_path}`: examination-date handler is retained with public visibility and a Text/DateTime-only fixture. Delegate ValidateExaminationDate and CheckAgeWithinScheduleRange execute extracted bodies with local ValidationFault substitution; synthetic date/death/existing-result fixtures and 6–8-week schedule exercise errors and warnings. WeeksBetween and DaysBetween are recovered unchanged from `{dates_path}`; no original Windows event delivery is claimed.
- `{ui_path}`: Height, Weight and HeadCirc Validating method bodies are retained, changing only private visibility for direct invocation. Text/Value-only ControlFixture replaces proprietary numeric controls; CancelEventArgs is the runtime type. Delegate ValidateHeight/ValidateWeight/ValidateHeadCircumference bodies are extracted with local ValidationFault replacing WCF wrappers. Invented height 40–60 and weight 3–6 bands supply deviation dependencies. Shared cases assert invalid cancellation, empty-input bypass with incoming cancellation retained, and warning-only acceptance. No Windows binding, event loop, focus or layout parity is claimed.
- Complete `{validator_path}` retained verbatim except DateTime.Today -> ReferenceClock.Today (frozen fixture).
- `{ui_path}` getSelectedIndexOfSelectedValue is retained with public visibility and proprietary dropdown/item types renamed to storage-only SelectionDropdownFixture/SelectionItemFixture. Seven shared scenarios invoke twice, covering first duplicate match, mixed integer/string values compared through ToString, final item, missing/null/empty selections, empty items and verbatim whitespace. Indices and unchanged collection/item/selected-value references are observed per call. This does not execute manuallyRefreshSelectedDropdownValues or establish Windows binding/event delivery; null item values are not covered (the source dereferences Value).
- DTO backing/property-change infrastructure replaced with same-named/type auto properties extracted from `{dto_path}`. No validator predicates replaced.
- Missing resource strings replaced with their symbolic names; fault wrappers replaced with Exceptions carrying those names. Aggregated numbered messages normalised only by removing numbering/newlines. Resource identifiers compared exactly in order.
- `{bmi_path}` CalculateBmi method retained verbatim in a small container.
- `{delegate_path}` CheckAgeWithinScheduleRange body retained verbatim; visibility made public; schedule Lazy reads fixture; Messenger records resource IDs. DaysBetween/WeeksBetween bodies recovered from `{dates_path}` and retained verbatim in ExtractedDateCalculation.cs; only the containing namespace/class is replaced. Truncation toward zero, including negative fractional days, is executable.
- Warning guard scenarios directly invoke extracted CheckDeviations/CheckBmi with runtime PropertyChangedEventArgs, observing lazy range access for null measurements, minimum dates, equal/reversed synthetic bands and unrelated/empty/null property names. No Windows event delivery or database range provenance is claimed.
- ExtractedInteractions retains BMI/decline/measurement properties and lookup/deviation/BMI method bodies except private visibility. Notifications dispatch through a synchronous PropertyChanged event subscribed to extracted CheckBmi, mirroring the source constructor subscription (not Windows controls). ExaminationDate and ResetDeviations bodies are retained, with ChildMeasurementsRange renamed to the fixture record; GetExpectedRanges records the date and supplies invented height range 40–60. Shared examples check same-day no-op, time preservation, lazy range reset and weight-setter BMI warning dispatch. Lookup retrieval supplies synthetic rows or null; invented height range 40–60 and BMI range 10–20 do not claim database provenance. Display names use symbolic enum names. ValidateAndSetExamCode retains its body with WCF fault wrappers replaced by local exceptions carrying Detail.Title; synchronous confirmation responses are fixture-controlled and recorded. A queued-response double models distinct answers to successive duplicate/code-change prompts; it does not decide whether to prompt. Shared sequence cases observe prompt order, unconsumed responses, selected code and validation state. Explicit synthetic result IDs (current 7, other 42) and dates exercise same-day/different-time rejection, self exclusion on the same/prior day and other-code isolation; fixture rows are supplied directly, not fetched from persistence. ExaminationCode, UpdateExamDescription, ClearDataFromHiddenFields, their field properties and ResetRecommendedAgeRange are source-extracted. Shared setter cases cover blocked/same-code no-ops and entering/leaving KD03, notifications, description, hidden-field clearing and lazy schedule reset. Synthetic descriptions and a recording schedule double returning 6–8 weeks replace lookups/services; Windows controls remain unverified. Populate, all three PrependNumericsUi description methods, GetDropDownUiPositionNumber and numeric position tables are source-extracted. Synthetic lookup lists replace lazy lookup-service retrieval; repeated Populate checks prefix idempotence, unmatched codes and already-prefixed descriptions. Context and lazy ranges are observed directly; Windows binding remains unverified; parent-delegate Populate integration executes through the extracted factory method. TransferObjectBase.Lock is a storage-only string substitution, not a concurrency implementation. ExamDescription getter/setter are source-extracted; shared cases verify the stored description is unchanged while display appends the explicitly synthetic RecallText suffix only when IsRepeat is true and the current code equals OriginalExamCode (including null-description concatenation). ResultTabText expression is also source-extracted: six shared heading cases observe successive DTO code/repeat changes, including different/missing OriginalExamCode and null/empty code concatenation. Unlike ExamDescription, its repeat suffix does not depend on OriginalExamCode. RecallFlag is explicitly synthetic, not recovered resource prose; these standalone getter scenarios do not replace the synthetic ResultTabText labels in the SetUpTabPages double. Original resource prose and Windows binding remain unverified.
- Heart/Hips/Eyes/Testes/PhysicalGeneral properties are retained in the source-extracted hidden-field property set. Direct assignment twice and null clearing are followed by extracted ValidateOnSave; shared cases assert DTO values, unchanged siblings, no explicit delegate notifications and the source's PhysicalGeneral counting discrepancy. Byte value 2 and reason 1 are fixtures; no Windows binding, assessment lookup delivery, entity mapping or persistence is verified.
- Dropdown ValidateLocationTypeInput, ValidateExaminerTypeInput and ValidateReasonNotExaminedTypeInput EventArgs handlers are source-extracted with visibility changes and the delegate type qualifier renamed. A Text-only HlxDropDown sender double proves invalid integer text is cleared and accepted text remains verbatim (Trim affects validation only). The distinct empty examiner CancelEventArgs overload is retained and invoked explicitly: invalid text and incoming cancellation remain unchanged. These shared cases do not verify proprietary binding, overload wiring or Windows event delivery.
- ValidateNumericDescriptorEntered and its TYPE_OF_INPUT enum are retained verbatim alongside the source numeric position tables. Shared cases cover both position boundaries, zero/negative/out-of-range integers, stored-key versus UI-position differences, and permissive empty/nonnumeric/decimal/overflow inputs. Direct method invocation does not prove Windows key handling or binding.
- Examination-code Validating/ButtonClick handlers from `{ui_path}` and LookUpExamCode from `{delegate_path}` retain their bodies. Text-only control and ShowFormLookup message doubles replace Windows UI/dialog infrastructure, record offered codes and supply explicit fixture responses; they do not validate or select codes themselves. Source ValidateAndSetExamCode performs validation/confirmation. Validating cancellation is observed separately from the selected code, including successful fallback lookup with cancellation still true. Original Windows event delivery remains unverified.
- `{repeat_path}` UpdateRepeatFlags body is retained with internal -> public visibility only. RepositoryFixture supplies explicit preloaded query rows separately from local tracked rows; Include has no database side effects. Source local navigation repair and all repeat decisions execute unchanged. Synthetic rows include KD03 ties, a later same-day timestamp, KD08 family members, another patient and another prefix. Repeated execution observes idempotence. This is sufficient standalone repeat-logic evidence for the agreed scope, not save-service/database parity.
- `{save_ui_path}` toolStripButtonSave_Click is retained with public visibility in ExtractedSaveButton.cs. Two shared cases invoke twice with null then non-null sender/EventArgs. A recording Save double counts dispatches and optionally throws an explicit synthetic exception on the first call; observations verify exactly one Save call per invocation and propagation of the same exception object, followed by successful retry. Omission, duplicate-dispatch and exception-swallowing mutations exercise this contract. This is direct handler dispatch evidence, not execution of the real Save workflow, Windows event wiring or persistence; those remain documented limitations.
- `{save_ui_path}` ucHLXKdpExaminations_Load is retained with public visibility in ExtractedUiLoad.cs. Two shared cases invoke it twice, explicitly resetting the default-tab flag before each invocation to cover both incoming states in both orders. The source resets the flag to false regardless of sender/EventArgs; omission and toggle mutations fail both cases. This verifies direct handler execution only; Windows load-event registration/delivery and subsequent tab selection remain documented limitations.
- `{dropdown_path}` both dictionary Populate overloads are retained in ExtractedDropdownDictionary.cs with only UIComboBox renamed to the existing storage-only fixture. Six shared cases invoke each overload twice: empty controls populate once, preseeded controls preserve existing entries, and an empty first dictionary permits later population. Synthetic ordered keys include whitespace/empty text; byte values include 0/255/null and string values include empty/verbatim/null. Per-call item content, collection identity, retained item identities and unchanged input dictionary entries are observed. Removing or inverting the count guard is detected. Modern Dictionary enumeration is used, not proof of original framework ordering; Windows binding/event delivery and child integration remain unverified. Approval blockers unchanged.
- `{dropdown_path}` list Populate overload is retained in ExtractedDropdownList.cs with UIComboBox/LookupsSubTO renamed to storage-only fixtures. Three shared cases invoke twice on a sentinel-seeded control, checking replacement/clearing, ordered duplicate codes, verbatim descriptions, nullable codes and optional trailing blank/null row. Per-call item values, Items collection identity and unchanged supplied row collection/ordered row references/values are observed. Clear-omission and null-row omission mutations exercise the contract. Synthetic rows are not real lookup data; Janus selection/binding/event delivery and integration with child Populate remain unverified. Approval blockers unchanged.
- `{ui_path}` FocusHlxTextBoxExamCode is retained in ExtractedChildFocus.cs with a Text-storage/recording-Focus control double. Five shared scenarios invoke twice for empty, filled, whitespace, cleared and filled-after-empty text, asserting cumulative Focus calls and unchanged text/control identity per call. Whitespace is nonempty in the source. Guard inversion mutation detects all five scenarios. This establishes dispatch decisions only; Windows focus, binding/event delivery and full child lifecycle parity remain documented limitations.
- `{save_ui_path}` SetUpTabPageContent is retained in an independently inspectable harness with UITabPage renamed to ContentTabFixture. Eight shared scenarios invoke twice, verifying positive/negative nonzero-key clearing, zero-key accumulation, missing-result clearing, null/empty bypass, exact first matching result identity, fresh child creation, complete ordered Controls object identities after each call (retaining the first child reference for zero-key accumulation), current-tab assignment, Fill docking and focus dispatch. A mutation replacing the accumulated first child is detected despite unchanged counts, sentinel and newest-child identity. The negative key is an explicit synthetic boundary fixture, not a production identifier claim; a strict-positivity clearing-guard mutation fails only that case. The child Populate/Focus and list Controls are recording doubles, not Windows binding/control construction/layout/event delivery or full child Populate parity. These remain documented limitations.
- `{save_ui_path}` SetUpTabPages is source-extracted in a separate independently inspectable setup harness, together with SelectTabPage. Shared cases invoke twice with changed synthetic result IDs/texts, including negative nonzero IDs in the current-selection fixture (remaining negative on both calls), proving that the guard is inequality with zero rather than positivity, positional key/text assignment, zero-ID tab preservation, preservation of trailing tab keys/text when the result list is shorter than the tab list (the default-selection fixture deliberately supplies three tabs and two results on both calls), default/current/null selection, empty-list bypass, exact selected and ordered tab identities, collection identity, current-tab object identity and default-selection flag after every call and preparation after assignment. Recording snapshots also assert current-tab object identity (including null) and the fixture-derived default-selection flag at content dispatch, detecting temporary replacement/toggling restored before return. They assert selected-tab object identity (including null current selection), collection object identity and complete ordered tab object identities at every content-preparation dispatch, detecting temporary replacement of the collection or a nonselected tab even when restored before return. The recording double retains the dispatched collection reference as well as a copied ordered-tab snapshot; same-tab collection replacement cannot hide behind unchanged tab identities. Expected selection is computed from the input fixture, not the observed mutable flag; replacement/toggle then restoration is detected even when final state is unchanged. Per-call observations also retain the supplied result collection and its complete ordered row object identities; setup must not replace the collection or substitute value-equal result records, including empty-list collection replacement. Dispatch-time snapshots also retain the supplied result collection reference and complete ordered result row references, detecting temporary same-row collection replacement or value-equal row substitution restored before return. The supplied tab-control wrapper is also retained and compared by object identity after each call and at each preparation dispatch; substituting a wrapper with identical tab collection and selection is detected even if restored before return. Per-call preparation counts explicitly require exactly one content dispatch for nonempty tabs (even with null selection) and none for empty tabs; counts are not inferred from the final dispatched tab. Omission and duplicate-dispatch mutations exercise this contract. These observations cover dispatch and post-return boundaries, not every transient state within the method. TabResultFixture supplies explicit IDs and SYNTH labels only; ResultTabText calculation/resource/recall prose is not verified by this double. SetUpTabPageContent records dispatch and snapshots, not control creation or currentTab updates; Windows layout/binding/event delivery and full UI Populate remain unverified. Existing insert/save handler harnesses retain their recording SetUpTabPages double.
- `{save_ui_path}` SelectTabPage is source-extracted with public visibility only. Shared cases toggle default/current selection across repeated calls and verify exact selected tab identity, unchanged currentTab, and unchanged collection identity and ordered tab object references after every call (not merely final keys), null current selection and detached current selection. The list/key-only tab double does not simulate Windows selection events or repair stale selection; direct invocation has no setup dispatch. Windows control selection/event delivery remains unverified.
- `{save_ui_path}` Populate and ProcessTabsForEachExam also execute together in a separate UI orchestration harness with retained method bodies (UITabPage renamed to SaveTabFixture). Four shared cases call Populate twice with changed synthetic contexts, result counts and editability, including empty results and toggling IsPopulatedFromContactsSummary. Retained GetKdpResults loads and populates the supplied DTOs before tab resizing and recording setup dispatch. Observations include exact DTO references, ordered result IDs, service client IDs, per-call ID/editability/counts, and setup-time load/count/processing/visibility snapshots. Synthetic decimal IDs 1001.5 and 2002.5 expose Convert.ToInt64 midpoint-to-even rounding; the stored ID remains decimal. NavigatorFixture is storage-only: the source hides it after setup for summary calls and does not restore visibility on subsequent ordinary calls. SetUpTabPages is a recording double, not selection, child construction or Windows binding/layout/event delivery. Existing save-refresh harness retains its Populate recording double; full original UI parity remains a documented limitation.
- `{save_ui_path}` ProcessTabsForEachExam is source-extracted, with public visibility and UITabPage renamed to SaveTabFixture. Shared cases execute growth, tail removal, unchanged counts and empty lists twice with changed synthetic result counts. Assertions retain existing tab object identities, preserve selected-tab identity (even when its tab is removed), observe null keys on new tabs and processingTabs reset. List<SaveTabFixture> substitutes the Windows tab collection only; no key assignment, selection repair, event delivery, layout or binding is claimed. SetUpTabPages remains a recording double; full Populate orchestration remains unverified.
- `{save_ui_path}` toolStripButtonInsert_Click is source-extracted with public visibility and UITabPage renamed to the key/text-only SaveTabFixture. Source NewTabKey/NewTabHeading constants are retained. Shared cases invoke twice and prove default-tab reset, first-tab-only duplicate guard, insertion before existing tabs, extracted AddNewKdpResult defaults/consent warning and setup after result insertion. SetUpTabPages records keys and result count only; it does not construct/bind Windows tabs or select them. The later-new fixture intentionally reveals that a new tab outside position zero does not block insertion. Windows delivery, tab layout and persistence remain unverified.
- `{save_ui_path}` ChangingSelectedTab handler is source-extracted with public visibility only. TabCancelEventArgs/Page and selected tabs are key-only doubles; SetUpTabPageContent records destination and reload count, not Windows control construction. Shared cases cover processing/no-selection guards, null/empty destination, rejected/accepted cancellation and incoming cancellation preservation. Extracted ConfirmCancelChanges reloads selected result 42 before preparation of destination 99; hasChanged is an explicit fixture flag. Additional scenarios supply unchanged results, changed new/nonpositive keys and an empty result list with a rejecting confirmation response: the retained source bypasses confirmation/reload and prepares destination 99, preserving incoming cancellation and selected keys. Direct invocation does not prove Windows event delivery or tab binding.
- `{save_ui_path}` SaveChanges body is source-extracted unchanged. SelectedTab/currentTab are key-only fixtures; Populate is a recording refresh double observing ID, Editable, prior service dispatch and default-tab state. Shared cases use patient ID 1001, result key 42, stale current key 99 and Editable=false to distinguish arguments/selection; successful/faulting calls run extracted parent Save. The double does not reload results or establish persistence/read-back, tab layout, event delivery or Windows binding parity.
- Selected-result cancellation scenarios place an unrelated result 77 (height 88, opposite ChangedFixture) before selected result 42 (height 99). Retained ConfirmCancelChanges selects by ID, prompts from the selected DTO only, and on acceptance replaces it with the exact reload DTO (height 55); unrelated identity/data/change state remain intact. These are synthetic loaded rows and an explicit change-tracking flag, not original DTO tracking or persistence evidence.
- `{lifecycle_path}` GetKdpResults body is source-extracted unchanged. Recording GetKdpExamination logs client IDs and returns an explicit synthetic LifecycleFixture context with unsorted DTOs (including equal-date ties) or an empty list. A second context for another synthetic patient verifies replacement, not accumulation. The double does not sort, populate or fetch persistence; retained GetKdpResults/GetNewKdpExaminationResultDelegate/Populate perform orchestration. Windows binding, service transport and persistence remain unverified.
- `{lifecycle_path}` Save body is source-extracted unchanged. A recording service double observes exact context/result identity and throws explicit synthetic generic/optimistic-lock faults; shared cases assert return value, error prompt and untouched unrelated DTO. Local FaultException types replace WCF exception transport only. This proves delegate selection and error routing, not validation, transactions, mapping or persistence in the original save service.
- ReasonNotExamined, Consent, CoreComponentOffered, Reschedule, WithdrawConsent and Origin setters/getters are source-extracted unchanged. Shared cases assign changed and unchanged values, then optionally clear nullable/string fields or reset WithdrawConsent to false. Distinct initial sibling values detect cross-field writes; CoreComponentOffered maps to DTO CoreComponent. These setters do not validate values or raise delegate notifications. Synthetic text is a storage probe, not an approved lookup value. Original DTO change tracking, Windows binding, save validation and persistence are not proved by these cases.
- Contact classification getters and original contact-code arrays are source-extracted unchanged. Three shared scenarios directly change the DTO code and observe all four flags on every step: KD03, every other listed contact, case/whitespace/prefix near-matches, empty/null/unknown codes and return to KD03. This verifies exact source applicability classification; target unsupported-contact rejection and Windows binding delivery are later-stage requirements.
- ExaminerCategory/ExaminerKdpCode/ExaminerType/ExaminerName and PopulateHcpDetails are source-extracted unchanged. Shared cases prove category assignments (changed/same/null) clear type/code/name/cache; refreshed retrieval uses the new category. HCP selection matches only UsedCode=Y, obtains Description/Type from explicitly synthetic cached rows, and leaves category unchanged for nonempty codes. Empty/null code invokes the category setter, clearing code to empty, type/name/category/cache without retrieval. LookupFixture adds a synthetic Type field for these dependencies; real lookup data and Windows binding/event delivery remain unverified.
- LocationType/LocationCode setters are source-extracted unchanged. Shared cases prove that changed, unchanged and null category assignments clear code/name/cache, and subsequent retrieval uses the assigned category rather than stale rows. Code assignments resolve exact cached descriptions, clear names for empty/null codes and yield null for unknown codes or absent cache without fetching rows. Synthetic descriptions are fixture data; Windows binding/event delivery remain unverified.
- Lookup exact-match sequences directly invoke retained ValidateLocationCode/ValidateExaminerCode nine times over SYNTH, case/leading/trailing-whitespace/prefix near-matches, empty/null, UNUSED and return to SYNTH. Per-call acceptance and exact cached collection/ordered row identities plus aggregate prompts and a single retrieval are observed. Location accepts an existing UNUSED row; examiner rejects its UsedCode=N. Case-insensitive/trimmed predicate mutations are detected. Codes are synthetic, not real lookup data; direct invocation does not establish Windows delivery, persistence or safe save during dependency failure. Approval blockers remain unchanged.
- Lookup validation lifecycle uses the same unfiltered recording lookup-service double, switching only its explicit fault flag between calls for recovery. Null/empty input, absent category, stale cached rows and empty service responses exercise unchanged validation and retrieval bodies; no validation rule is supplied by the double. Service transport, real lookup values, Windows delivery and save/persistence remain unverified.
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
    js('stage.json', {'reviewFiles': reviewed, 'blockingGaps': [],
                      'checks': [{'command': {'executable': sys.executable, 'arguments': ['verify.py'], 'timeoutSeconds': 600}, 'results': 'results.json'}]})


if __name__ == '__main__':
    generate(json.loads(Path(sys.argv[-1]).read_text()))
