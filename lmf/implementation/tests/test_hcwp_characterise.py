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
            for field, error in [('Height', 'InvalidHeightMessage'), ('Weight', 'InvalidWeightMessage'), ('HeadCirc', 'HeadCircumferenceInvalidFormatMessage')]:
                for name in ('valid', 'invalid', 'empty', 'empty-preserves-cancel'):
                    self.assertEqual({'cancelled': name in ('invalid', 'empty-preserves-cancel'),
                        'errors': [error] if name == 'invalid' else [], 'warnings': []}, rows[f'KD03-control-{field}-{name}'])
            self.assertEqual({'cancelled': False, 'errors': [], 'warnings': ['OutsideExpectedRangeMessage']}, rows['KD03-control-Height-warning'])
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
            for kind in ('Height', 'Weight', 'HeadCircumference'):
                for declined, flag in [('true', 'Y'), ('false', 'N')]:
                    self.assertEqual({'value': None, 'flag': flag, 'errors': [], 'warnings': []}, rows[f'KD03-decline-{kind}-{declined}'])
            self.assertFalse(rows['KD03-examiner-unused']['valid'])
            self.assertEqual(['UnusedExaminerCodeMessage'], rows['KD03-examiner-unused']['errors'])
            self.assertTrue(rows['KD03-location-null-lookup']['valid'])
            self.assertTrue(rows['KD03-examiner-null-lookup']['valid'])
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
