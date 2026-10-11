#!/usr/bin/env python3
"""Real bundle / extracted C# integration, not a coding-agent success double."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT.parents[1] / 'example-code/HCWP Core (pseudonymised) - single file.txt'


class CharacteriseTests(unittest.TestCase):
    def test_source_extraction_gate_and_blocked_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            target = directory / 'target.md'
            target.write_text('Modern .NET server-interactive Blazor and EF Core in-memory storage.')
            config = directory / 'agent.json'
            config.write_text(json.dumps({'command': {'executable': sys.executable,
                'arguments': [str(ROOT / 'adapters/hcwp_characterise.py')]}}))
            workspace = directory / 'migration'
            def cli(*args):
                return subprocess.run([str(ROOT / 'lmf'), *args], capture_output=True, text=True)
            run = cli('characterise', '--workspace', str(workspace), '--source', str(BUNDLE),
                      '--target', str(target), '--agent', str(config), '--repairs', '0')
            self.assertEqual(0, run.returncode, run.stderr)
            state = json.loads((workspace / 'state.json').read_text())
            self.assertEqual('awaiting-approval', state['Status'])
            self.assertFalse((workspace / 'convert').exists())
            stage = workspace / 'characterise'
            contract = json.loads((stage / 'stage.json').read_text())
            self.assertTrue(contract['blockingGaps'])
            self.assertIn('reference/ADAPTATIONS.md', contract['reviewFiles'])
            index = json.loads((stage / 'source-index.json').read_text())
            self.assertEqual(94, len(index))
            for item in index:
                self.assertIn(item['file'], BUNDLE.read_text().splitlines()[item['bundleLine'] - 1])
            report = json.loads((stage / 'reference-report.json').read_text())
            self.assertGreater(len(report['scenarios']), 20)
            self.assertTrue(all(row['matches'] for row in report['scenarios']))
            rows = {row['id']: row['actual'] for row in report['scenarios']}
            for name, category in [('changed', 2), ('same', 5), ('null', None)]:
                self.assertEqual({'category': category, 'code': '', 'name': '', 'cacheCleared': True,
                    'refreshedCodes': None if category is None else ['NEW'],
                    'requests': [] if category is None else [f'Locations||{category}'],
                    'notifications': [], 'errors': ['NoLocationTypeMessage'] if category is None else [],
                    'warnings': []}, rows['KD03-location-category-' + name])
            for name, code, description in [('matched', 'SYNTH', 'Synthetic location description'),
                                             ('unknown', 'MISSING', None), ('empty', '', ''),
                                             ('null', None, ''), ('no-cache', 'SYNTH', None)]:
                self.assertEqual({'code': code, 'name': description, 'sameCache': True,
                    'requests': [], 'notifications': [], 'errors': [], 'warnings': []},
                    rows['KD03-location-code-' + name])
            self.assertIn('LocationType/LocationCode setters are source-extracted unchanged',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for name, category in [('changed', '19'), ('same', '18'), ('null', None)]:
                self.assertEqual({'category': category, 'type': '', 'code': '', 'name': '',
                    'cacheCleared': True, 'refreshedCodes': None if category is None else ['NEW'],
                    'requests': [] if category is None else [f'Examiners||{category}|N'],
                    'notifications': [], 'errors': ['NoExaminerTypeMessage'] if category is None else [],
                    'warnings': []}, rows['KD03-examiner-category-' + name])
            for name, code, category, examiner_type, description, cleared in [
                ('matched', 'SYNTH', '18', 'SYNTH-TYPE', 'Synthetic HCP', False),
                ('unused', 'UNUSED', '18', None, None, False),
                ('unknown', 'MISSING', '18', None, None, False),
                ('empty', '', '', '', '', True), ('null', '', '', '', '', True)]:
                self.assertEqual({'code': code, 'category': category, 'type': examiner_type,
                    'name': description, 'cacheCleared': cleared, 'requests': [],
                    'notifications': [], 'errors': [], 'warnings': []}, rows['KD03-examiner-code-' + name])
            self.assertIn('PopulateHcpDetails are source-extracted unchanged',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for kind in ('location', 'examiner'):
                for mode in ('missing', 'cached', 'retrieved', 'fault'):
                    row = rows[f'KD03-lookup-retrieval-{kind}-{mode}']
                    self.assertEqual(None if mode in ('missing', 'fault') else ['SYNTH', 'UNUSED'] if kind == 'location' else ['SYNTH'], row['codes'])
                    request = 'Locations||5' if kind == 'location' else 'Examiners||18|N'
                    self.assertEqual([] if mode in ('missing', 'cached') else [request] * (2 if mode == 'fault' else 1), row['requests'])
                    self.assertEqual(mode in ('cached', 'retrieved'), row['sameRows'])
                    self.assertEqual(2 if mode in ('missing', 'fault') else 0, len(row['prompts']))
            self.assertIn('GetUsedExaminerList', (stage / 'reference/ExtractedInteractions.cs').read_text())
            self.assertIn('returns unfiltered synthetic', (stage / 'reference/ADAPTATIONS.md').read_text())
            for name, stored, displayed in [
                ('nonrepeat', 'Synthetic contact', 'Synthetic contact'),
                ('repeat-original-code', 'Synthetic contact', 'Synthetic contact [synthetic recall text]'),
                ('repeat-changed-code', 'Synthetic contact', 'Synthetic contact'),
                ('repeat-missing-original', 'Synthetic contact', 'Synthetic contact'),
                ('repeat-null-description', None, ' [synthetic recall text]'),
            ]:
                self.assertEqual({'stored': stored, 'displayed': displayed, 'errors': [], 'warnings': []},
                                 rows['KD03-description-' + name])
            for outcome in ('success', 'optimistic-lock', 'fault'):
                self.assertEqual({'allowed': outcome == 'success', 'calls': 1,
                    'sameContext': True, 'sameResult': True, 'unrelatedUnchanged': True,
                    'prompts': [] if outcome == 'success' else ['ExamResultsErrorSavingPrompt'],
                    'errors': [] if outcome == 'success' else ['synthetic-' + outcome],
                    'warnings': []}, rows['KD03-parent-save-' + outcome])
            self.assertIn('public bool Save(long kdpChildExaminationId)',
                          (stage / 'reference/ExtractedLifecycle.cs').read_text())
            self.assertIn('not validation, transactions, mapping or persistence',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            self.assertEqual({'weeks': 8, 'errors': [], 'warnings': []}, rows['KD03-weeks-truncation-positive'])
            self.assertEqual({'weeks': 0, 'errors': [], 'warnings': []}, rows['KD03-weeks-truncation-negative'])
            self.assertEqual([], rows['KD03-age-upper-fractional-day']['warnings'])
            self.assertEqual(['KdpContactGivenAfterMaxAge'], rows['KD03-age-after-upper-day']['warnings'])
            self.assertNotIn('WeeksBetween adaptation requires review', contract['blockingGaps'])
            self.assertIn('Repeat-flag scope unresolved', contract['blockingGaps'])
            self.assertIn('DateCalculation.cs', (stage / 'reference/ADAPTATIONS.md').read_text())
            for name in ('family-and-date-ties', 'local-navigation-repair', 'short-prefix', 'unmatched-prefix'):
                flags = ['Y', 'Y', 'N', 'Y', 'N', 'Y', 'Y'] if name == 'unmatched-prefix' else ['N', 'N', 'Y', 'N', 'Y', 'Y', 'Y']
                self.assertEqual({'flags': flags, 'navigationRestored': True, 'idempotent': True,
                    'errors': [], 'warnings': []}, rows['KD03-repeat-' + name])
                # Other-patient KD03 must retain its original Y even though its
                # timestamp precedes every selected-patient KD03 timestamp.
                self.assertEqual('Y', rows['KD03-repeat-' + name]['flags'][5])
            self.assertIn('ExaminationsCrudManager.cs', (stage / 'reference/ADAPTATIONS.md').read_text())
            self.assertIn('KD03 calls can therefore mutate existing KD08 flags', (stage / 'dependencies.md').read_text())
            for field, error in [('Height', 'InvalidHeightMessage'), ('Weight', 'InvalidWeightMessage'), ('HeadCirc', 'HeadCircumferenceInvalidFormatMessage')]:
                for name in ('valid', 'invalid', 'empty', 'empty-preserves-cancel'):
                    self.assertEqual({'cancelled': name in ('invalid', 'empty-preserves-cancel'),
                        'errors': [error] if name == 'invalid' else [], 'warnings': []}, rows[f'KD03-control-{field}-{name}'])
            self.assertEqual({'cancelled': False, 'errors': [], 'warnings': ['OutsideExpectedRangeMessage']}, rows['KD03-control-Height-warning'])
            for name, error, warning in [('valid', None, None), ('future', 'FutureExamDateMessage', None), ('before-birth', 'ExamDateBeforeDobMessage', None), ('after-death', 'ExamDateAfterDeathMessage', None), ('duplicate', 'KdpResultAlreadyEnteredMessage', None), ('young', None, 'KdpContactGivenBeforeMinAge'), ('old', None, 'KdpContactGivenAfterMaxAge'), ('empty', None, None), ('empty-preserves-cancel', None, None)]:
                self.assertEqual({'cancelled': bool(error) or name == 'empty-preserves-cancel',
                    'errors': [error] if error else [], 'warnings': [warning] if warning else []}, rows['KD03-date-control-' + name])
            for name, selected, cancelled, errors, confirmations, lookups in [
                ('valid', 'KD03', False, [], [], 0),
                ('invalid-cancel-lookup', '', True, ['KdpInvalidExamCodeMessage'], [], 1),
                ('invalid-select-lookup', 'KD03', True, ['KdpInvalidExamCodeMessage'], [], 1),
                ('invalid-lookup-result', '', True, ['KdpInvalidExamCodeMessage'] * 2, [], 1),
                ('change-accept', 'KD03', False, [], ['KdpResultsExamCodeChangeConfirmationMessage'], 0),
                ('change-reject', 'KD08', True, [], ['KdpResultsExamCodeChangeConfirmationMessage'], 1),
                ('button-select', 'KD03', True, [], [], 1),
                ('button-cancel', 'KD08', True, [], [], 1),
            ]:
                self.assertEqual({'selected': selected, 'cancelled': cancelled, 'errors': errors,
                    'warnings': [], 'confirmations': confirmations, 'lookupRequests': lookups,
                    'lookupCodes': [['KD03', 'KD08']] if lookups else []}, rows['KD03-code-control-' + name])
            self.assertIn('ShowFormLookup message doubles', (stage / 'reference/ADAPTATIONS.md').read_text())
            self.assertIn('Text/DateTime-only double', (stage / 'gaps.md').read_text())
            self.assertIn('Text/Value-only control doubles', (stage / 'gaps.md').read_text())
            self.assertEqual(['HeadCircumferenceInvalidFormatMessage'], rows['KD03-head-field-100']['errors'])
            self.assertEqual(100, rows['KD03-head-save-100']['saved']['HeadCircumference'])
            self.assertEqual(['NoResultsEnteredMessage'], rows['KD03-general-alone']['errors'])
            for name, date, reset in [('same-day', '2025-02-19T09:10:11', False),
                                      ('changed-day', '2025-02-20T09:10:11', True)]:
                self.assertEqual({'date': date, 'rangesReset': reset, 'lazyBeforeRead': True,
                    'rangeRequests': [date] if reset else [], 'notifications': [],
                    'errors': [], 'warnings': []}, rows['KD03-date-setter-' + name])
            self.assertEqual({'weight': 6.1, 'bmi': 20.17,
                'notifications': ['Bmi', 'IsBmiOutsideRange'], 'errors': [],
                'warnings': ['BmiOutsidePrescribedRangeMessage']}, rows['KD03-weight-setter-warning'])
            for name in ('blocked', 'unchanged', 'enter', 'leave'):
                row = rows['KD03-code-setter-' + name]
                changed = name in ('enter', 'leave')
                self.assertEqual('KD08' if name == 'leave' else 'KD03', row['selected'])
                self.assertEqual(changed, row['rangesReset'])
                self.assertTrue(row['lazyBeforeRead'])
                self.assertEqual([row['selected']], row['scheduleRequests'])
                self.assertEqual(None if name == 'leave' else 1, row['heart'])
                self.assertEqual(None if name == 'enter' else 1, row['development'])
                self.assertEqual(None if name == 'enter' else '1', row['dsk'])
                self.assertEqual(None if name == 'enter' else 1, row['rsk'])
                self.assertEqual('Synthetic ' + row['selected'] if changed else None, row['description'])
                self.assertEqual(['ExamDescription', 'Is15Or27MonthContact', 'Is6To8WeekContact', 'IsDskContact', 'IsRskContact'] if changed else [], row['notifications'])
            for field, value, bmi, outside in [
                ('Height', 40, 28.12, True), ('Height', 55, 14.88, False), ('Height', None, None, False),
                ('Weight', 3, 9.92, True), ('Weight', 4.5, 14.88, False), ('Weight', None, None, False),
                ('HeadCircumference', 40, 14.88, False), ('HeadCircumference', None, 14.88, False),
            ]:
                notifications = ['HeadCircumference'] if field == 'HeadCircumference' else ['Bmi', 'IsBmiOutsideRange']
                self.assertEqual({'value': value, 'bmi': bmi, 'outside': outside,
                    'notifications': notifications * 2, 'errors': [],
                    'warnings': ['BmiOutsidePrescribedRangeMessage'] * 2 if outside else []},
                    rows[f'KD03-assignment-{field}-{value}'])
            for kind in ('Height', 'Weight', 'HeadCircumference'):
                for declined, flag in [('true', 'Y'), ('false', 'N')]:
                    notifications = ['Is' + kind + 'Required'] + (['HeadCircumference'] if kind == 'HeadCircumference' else ['Bmi', 'IsBmiOutsideRange'])
                    self.assertEqual({'value': None, 'flag': flag, 'required': declined == 'false',
                        'notifications': notifications, 'errors': [], 'warnings': []}, rows[f'KD03-decline-{kind}-{declined}'])
            self.assertFalse(rows['KD03-examiner-unused']['valid'])
            self.assertEqual(['UnusedExaminerCodeMessage'], rows['KD03-examiner-unused']['errors'])
            for kind, maximum, stored_key in [('LOCATON_TYPE', 7, 22), ('EXAMINER_TYPE', 12, 28), ('REASON_NOT_EXAMINED', 5, 5)]:
                for label in ['first', 'last', 'empty', 'text', 'decimal', 'overflow', 'whitespace']:
                    self.assertEqual({'errors': [], 'warnings': [], 'valid': True},
                                     rows['KD03-numeric-descriptor-' + kind + '-' + label])
                for label in ['zero', 'negative', 'above']:
                    self.assertEqual({'errors': [], 'warnings': [], 'valid': False},
                                     rows['KD03-numeric-descriptor-' + kind + '-' + label])
                self.assertEqual(stored_key <= maximum, rows['KD03-numeric-descriptor-' + kind + '-stored-key']['valid'])
            for kind, maximum, stored_key in [('LOCATON_TYPE', 7, '22'), ('EXAMINER_TYPE', 12, '28'), ('REASON_NOT_EXAMINED', 5, '5')]:
                for label, text, accepted in [('first', '1', True), ('last', str(maximum), True),
                        ('zero', '0', False), ('negative', '-1', False), ('above', str(maximum + 1), False),
                        ('stored-key', stored_key, int(stored_key) <= maximum), ('empty', '', True),
                        ('text', 'unknown', True), ('decimal', '1.5', True), ('overflow', '2147483648', True),
                        ('whitespace', ' 1 ', True)]:
                    self.assertEqual({'errors': [], 'warnings': [], 'text': text if accepted else '', 'cancelled': False},
                                     rows['KD03-dropdown-' + kind + '-' + label])
            for cancelled in (False, True):
                self.assertEqual({'errors': [], 'warnings': [], 'text': ' 999 ', 'cancelled': cancelled},
                                 rows['KD03-dropdown-examiner-cancel-' + str(cancelled).lower()])
            dropdown_source = (stage / 'reference/ExtractedDropdownControls.cs').read_text()
            self.assertIn('ValidateExaminerTypeInput(object sender, CancelEventArgs e)', dropdown_source)
            self.assertIn('ValidateExaminerTypeInput(object sender, EventArgs e)', dropdown_source)
            self.assertIn('public bool ValidateNumericDescriptorEntered', (stage / 'reference/ExtractedInteractions.cs').read_text())
            self.assertTrue(rows['KD03-location-null-lookup']['valid'])
            self.assertTrue(rows['KD03-examiner-null-lookup']['valid'])
            for name in ('missing-height', 'missing-date', 'equal-band', 'reversed-band'):
                warning = name in ('equal-band', 'reversed-band')
                self.assertEqual(warning, rows['KD03-deviation-guard-' + name]['rangeRead'])
                self.assertEqual(['OutsideExpectedRangeMessage'] if warning else [], rows['KD03-deviation-guard-' + name]['warnings'])
            for name in ('bmi-outside', 'unrelated', 'range-property', 'empty-property', 'null-property', 'missing-height', 'missing-weight', 'bmi-inside'):
                self.assertEqual(name in ('bmi-outside', 'bmi-inside'), rows['KD03-bmi-event-' + name]['rangeRead'])
                self.assertEqual(['BmiOutsidePrescribedRangeMessage'] if name == 'bmi-outside' else [], rows['KD03-bmi-event-' + name]['warnings'])
            self.assertEqual([], rows['KD03-deviation-50']['warnings'])
            for boundary in (40, 60):
                self.assertEqual(['OutsideExpectedRangeMessage'], rows[f'KD03-deviation-{boundary}']['warnings'])
            self.assertEqual(['BmiOutsidePrescribedRangeMessage'], rows['KD03-bmi-warning-3.0']['warnings'])
            self.assertEqual([], rows['KD03-bmi-warning-3.025']['warnings'])
            self.assertEqual([], rows['KD03-bmi-warning-6.05']['warnings'])
            self.assertEqual(['BmiOutsidePrescribedRangeMessage'], rows['KD03-bmi-warning-6.1']['warnings'])
            for reason, original, message in [('duplicate', '', 'KdpDuplicateExamCodeMessage'), ('change', 'OLD', 'KdpResultsExamCodeChangeConfirmationMessage')]:
                for response in (True, False):
                    row = rows[f'KD03-confirm-{reason}-{str(response).lower()}']
                    self.assertEqual(response, row['valid'])
                    self.assertEqual('KD03' if response else original, row['selected'])
                    self.assertEqual([message], row['confirmations'])
                    self.assertEqual([], row['errors'])
            self.assertEqual(['KdpInvalidExamCodeMessage'], rows['KD03-code-invalid']['errors'])
            self.assertFalse(rows['KD03-code-invalid']['valid'])
            self.assertEqual([], rows['KD03-code-invalid']['confirmations'])
            for consent in (True, False):
                row = rows[f'KD03-new-defaults-{str(consent).lower()}']
                self.assertEqual({'ClientId': 1001, 'PkChildExaminationId': 0,
                    'ResultEnteredDate': '2025-03-01T12:00:00', 'Origin': 2, 'Reschedule': 'N',
                    'HeightMeasurementDeclined': 'N', 'WeightMeasurementDeclined': 'N',
                    'HeadMeasurementDeclined': 'N', 'EnabledPropChangeEvents': True,
                    'ExaminationCode': None, 'ExaminationDate': '0001-01-01T00:00:00'}, row['defaults'])
                self.assertEqual({'gender': 'F', 'birth': '2024-12-01', 'death': '2025-02-01',
                    'sameExisting': True, 'scheduled': False, 'unscheduled': True,
                    'description': None, 'notifications': ['ExamDescription'],
                    'lazyRanges': True, 'requests': 0}, row['context'])
                self.assertTrue(row['insertedFirst'])
                self.assertEqual(2, row['count'])
                self.assertEqual([] if consent else ['NoConsentMessage'], row['warnings'])
                self.assertEqual([], row['confirmations'])
            for name in ('accept', 'reject', 'unchanged', 'new', 'empty'):
                row = rows[f'KD03-cancel-{name}']
                self.assertEqual(name != 'reject', row['allowed'])
                self.assertEqual([42] if name == 'accept' else [], row['reloadCalls'])
                self.assertEqual(name == 'accept', row['replaced'])
                self.assertEqual(None if name == 'empty' else (55 if name == 'accept' else 99), row['height'])
                self.assertEqual(['ExamResultsConfirmCancelMessage'] if name in ('accept', 'reject') else [], row['confirmations'])
            for name in ('unscheduled', 'scheduled', 'empty-code'):
                row = rows['KD03-populate-' + name]
                # Populate starts with a distinct KD08/2000 sentinel DTO.
                self.assertTrue(row['sameDto'])
                self.assertEqual(None if name == 'empty-code' else 'KD03', row['selected'])
                self.assertEqual('2025-02-19T00:00:00', row['date'])
                self.assertTrue(row['sameExisting'])
                self.assertEqual('F', row['gender'])
                self.assertEqual('2024-12-01', row['birth'])
                self.assertEqual('2025-02-01' if name == 'scheduled' else None, row['death'])
                self.assertEqual(name == 'scheduled', row['scheduled'])
                self.assertEqual(name != 'scheduled', row['unscheduled'])
                self.assertEqual(None if name == 'empty-code' else 'Synthetic KD03', row['description'])
                self.assertTrue(row['rangesReset'])
                self.assertTrue(row['lazyBeforeRead'])
                self.assertEqual(0, row['requestsBeforeRead'])
                self.assertEqual(['2025-02-19T00:00:00'], row['rangeRequests'])
                self.assertEqual([None if name == 'empty-code' else 'KD03'], row['scheduleRequests'])
                # Both an already-prefixed and an unprefixed mapped reason survive
                # two Populate calls with exactly one numeric prefix.
                self.assertEqual(['1 - Synthetic location', 'Unmapped', '2 - Synthetic examiner', '1 - Already prefixed', '2 - Synthetic reason'], row['lookupDescriptions'])
                self.assertEqual(['ExamDescription', 'ExamDescription'], row['notifications'])
                self.assertEqual([], row['errors'])
                self.assertEqual([], row['warnings'])
            adaptations = (stage / 'reference/ADAPTATIONS.md').read_text()
            self.assertIn('hasChanged returns an explicit fixture flag', adaptations)
            self.assertIn('GetNewKdpExaminationResultDelegate is source-extracted', adaptations)
            self.assertIn('ExaminationDate and ResetDeviations bodies are retained', adaptations)
            self.assertIn('ClearDataFromHiddenFields', adaptations)
            self.assertIn('numeric position tables are source-extracted', adaptations)
            self.assertIn('parent-delegate Populate integration executes', adaptations)
            self.assertIn('recording schedule double', adaptations)
            self.assertIn('PropertyChanged event subscribed to extracted CheckBmi', adaptations)
            approve = cli('approve', '--workspace', str(workspace), '--revision', state['Revision'])
            self.assertNotEqual(0, approve.returncode)
            self.assertIn('blocking gaps', approve.stderr)
            # Regression evidence: each validator's proposed omission must fail
            # the shared Populate scenarios, not merely a harness-local assertion.
            extracted = stage / 'reference/ExtractedInteractions.cs'
            original = extracted.read_text()
            for omitted in ('KdpExaminationResultTo = kdpExaminationResultTo;',
                            'PrependNumericsUiReasonNotExaminedDescriptions();'):
                self.assertEqual(1, original.count(omitted))
                try:
                    extracted.write_text(original.replace(omitted, '// mutation: omitted'))
                    mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                    self.assertNotEqual(0, mutant.returncode, mutant.stdout + mutant.stderr)
                    mutant_report = json.loads((stage / 'reference-report.json').read_text())
                    failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                    expected = {'KD03-populate-unscheduled', 'KD03-populate-scheduled',
                                'KD03-populate-empty-code'}
                    if omitted == 'KdpExaminationResultTo = kdpExaminationResultTo;':
                        expected.update({'KD03-new-defaults-true', 'KD03-new-defaults-false'})
                    self.assertEqual(expected, failures)
                finally:
                    extracted.write_text(original)
            # A same-code unused row precedes the used row: dropping the source
            # used-code predicate must change both selection and unused rejection.
            used_filter = 'ex.UsedCode == HLXBoolean.True && '
            self.assertEqual(1, original.count(used_filter))
            try:
                extracted.write_text(original.replace(used_filter, ''))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-examiner-code-matched', 'KD03-examiner-code-unused'}, failures)
            finally:
                extracted.write_text(original)
            # Removing only the local-query client filter must break isolation;
            # keep the database-query filter intact to catch the specific finding.
            extracted_repeat = stage / 'reference/ExtractedRepeatFlags.cs'
            original_repeat = extracted_repeat.read_text()
            local_filter = 'where exam.ChildExamination.ClientId == clientId && '
            self.assertEqual(1, original_repeat.count(local_filter))
            try:
                extracted_repeat.write_text(original_repeat.replace(local_filter, 'where '))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-repeat-family-and-date-ties',
                    'KD03-repeat-local-navigation-repair', 'KD03-repeat-short-prefix'}, failures)
                for row in mutant_report['scenarios']:
                    if row['id'] in failures:
                        self.assertEqual('N', row['actual']['flags'][5])
            finally:
                extracted_repeat.write_text(original_repeat)
            # Verification must execute and compare, not merely return counts.
            scenarios = json.loads((stage / 'scenarios.json').read_text())
            next(s for s in scenarios if s['id'] == 'KD03-valid')['then']['saved']['Heart'] = 3
            (stage / 'scenarios.json').write_text(json.dumps(scenarios))
            check = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
            self.assertNotEqual(0, check.returncode)
            self.assertEqual(1, json.loads((stage / 'results.json').read_text())['failed'])
            report = json.loads((stage / 'reference-report.json').read_text())
            self.assertFalse(next(row for row in report['scenarios'] if row['id'] == 'KD03-valid')['matches'])

    def test_adapter_rejects_unsupported_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / 'request.json'
            request.write_text(json.dumps({'Stage': 'convert'}))
            run = subprocess.run([sys.executable, str(ROOT / 'adapters/hcwp_characterise.py'), str(request)], capture_output=True, text=True)
            self.assertNotEqual(0, run.returncode)
            self.assertIn('only implements Characterise', run.stderr)


if __name__ == '__main__':
    unittest.main()
