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
            for name, counts, sentinel, matched in [
                ('existing', [1, 1], False, True), ('new', [2, 3], True, True),
                ('missing-existing', [0, 0], False, False), ('missing-new', [1, 1], True, False),
                ('empty', [1, 1], True, False), ('null-key', [1, 1], True, False),
                ('null-tab', [0, 0], False, False),
            ]:
                self.assertEqual({'counts': counts, 'sentinelRetained': [sentinel] * 2,
                    'created': [matched] * 2, 'exactResult': [True, True],
                    'currentIdentity': [True, True], 'childIdentity': [True, True],
                    'orderedControlsIdentities': [True, True],
                    'dockFill': [True, True], 'focusCalls': [1 if matched else 0] * 2,
                    'errors': [], 'warnings': []}, rows['KD03-ui-tab-content-' + name])
            for name, keys, texts, selected in [
                ('default', [['42', '99'], ['142', '199']], [['SYNTH-42', 'SYNTH-99'], ['SYNTH-142', 'SYNTH-199']], ['42', '142']),
                ('current', [['42', '99'], ['142', '199']], [['SYNTH-42', 'SYNTH-99'], ['SYNTH-142', 'SYNTH-199']], ['99', '199']),
                ('new', [['0', '99'], ['0', '199']], [['original-0', 'SYNTH-99'], ['original-0', 'SYNTH-199']], ['0', '0']),
                ('null-current', [['42', '99'], ['142', '199']], [['SYNTH-42', 'SYNTH-99'], ['SYNTH-142', 'SYNTH-199']], [None, None]),
                ('empty', [[], []], [[], []], []),
            ]:
                self.assertEqual({'keys': keys, 'texts': texts, 'selected': selected,
                    'keysAtPreparation': keys if name != 'empty' else [],
                    'textsAtPreparation': texts if name != 'empty' else [],
                    'orderedIdentitiesAtPreparation': [True, True] if name != 'empty' else [],
                    'collectionIdentity': True, 'collectionIdentities': [True, True], 'orderedIdentities': [True, True],
                    'exactSelection': True, 'currentIdentities': [True, True],
                    'defaultStates': [name != 'current' and name != 'null-current'] * 2,
                    'currentUnchanged': True, 'defaultUnchanged': True,
                    'errors': [], 'warnings': []}, rows['KD03-ui-tab-setup-' + name])
            self.assertIn('ResultTabText calculation/resource/recall prose is not verified',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for name, selected in [('default-then-current', ['42', '99']),
                                   ('current-then-default', ['99', '42']),
                                   ('null-current', [None, '42']),
                                   ('detached-current', ['77', '77'])]:
                self.assertEqual({'selected': selected, 'exactIdentity': True,
                    'currentUnchanged': True, 'keys': ['42', '99'], 'setupCalls': 0,
                    'collectionIdentities': [True, True], 'orderedTabIdentities': [True, True],
                    'errors': [], 'warnings': []}, rows['KD03-ui-tab-select-' + name])
            self.assertIn('SelectTabPage is source-extracted',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for mode, ids in [('unordered', [42, 99, 77]), ('ties', [77, 42, 99]), ('empty', [])]:
                self.assertEqual({'errors': [], 'warnings': [], 'ids': ids, 'refreshIds': [88],
                    'calls': [1001, 2002], 'sameDtos': True, 'sameContext': True,
                    'lazyRanges': True, 'replaced': True}, rows[f'KD03-get-results-{mode}'])
            for name, snapshots in [('grow-shrink', [[None, None, None], [None]]),
                                     ('shrink-grow', [['42'], ['42', None, None]]),
                                     ('unchanged', [['42', '99'], ['42', '99']]),
                                     ('clear', [[], []]), ('empty', [[], []])]:
                self.assertEqual({'snapshots': snapshots, 'retainedIdentity': True,
                    'selectedUnchanged': True, 'processingStates': [False, False],
                    'defaultTab': False, 'setupCalls': 0, 'serviceCalls': 0,
                    'errors': [], 'warnings': []}, rows['KD03-ui-tab-count-' + name])
            self.assertIn('full Populate orchestration remains unverified',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for kind in ('location', 'examiner'):
                request = 'Locations||5' if kind == 'location' else 'Examiners||18|N'
                missing = 'NoLocationTypeMessage' if kind == 'location' else 'NoExaminerTypeMessage'
                missing_prompt = 'NoLocationTypePrompt' if kind == 'location' else 'NoExaminerTypePrompt'
                fault_prompt = 'ErrorGettingLocationListPrompt' if kind == 'location' else 'ErrorGettingExaminerListPrompt'
                invalid = 'InvalidLocationCodeMessage' if kind == 'location' else 'InvalidHcpCodeMessage'
                invalid_prompt = 'InvalidLocationCodePrompt' if kind == 'location' else 'InvalidHcpCodePrompt'
                for mode, valid, errors, prompts, requests, cached in [
                    ('empty-code', [True, True], [], [], [], False),
                    ('null-code', [True, True], [], [], [], False),
                    ('missing', [True, True], [missing] * 2, [missing_prompt] * 2, [], False),
                    ('missing-cached', [False, False], [missing, invalid] * 2,
                     [missing_prompt, invalid_prompt] * 2, [], True),
                    ('fault-recovery', [True, False], ['synthetic-lookup-fault', invalid],
                     [fault_prompt, invalid_prompt], [request] * 2, True),
                    ('empty-rows', [False, False], [invalid] * 2,
                     [invalid_prompt] * 2, [request], True),
                ]:
                    self.assertEqual({'valid': valid, 'errors': errors, 'warnings': [],
                        'prompts': prompts, 'requests': requests, 'cached': cached},
                        rows[f'KD03-lookup-validation-{kind}-{mode}'])
            self.assertIn('not evidence that save is safe during dependency failure',
                          (stage / 'gaps.md').read_text())
            common_initial = {'ReasonNotExamined': 'sentinel-reason', 'Consent': 'sentinel-consent',
                              'CoreComponent': 1, 'Reschedule': 'sentinel-reschedule',
                              'WithdrawConsent': False, 'Origin': 1}
            for field, stored_field in [('ReasonNotExamined', 'ReasonNotExamined'), ('Consent', 'Consent'),
                                        ('CoreComponentOffered', 'CoreComponent'), ('Reschedule', 'Reschedule'),
                                        ('WithdrawConsent', 'WithdrawConsent'), ('Origin', 'Origin')]:
                value = True if field == 'WithdrawConsent' else 2 if field in ('CoreComponentOffered', 'Origin') else 'synthetic-value'
                for mode, clear in [('value', False), ('cleared', True)]:
                    final = (False if field == 'WithdrawConsent' else None) if clear else value
                    self.assertEqual({'assigned': value, 'displayed': final,
                        'stored': {**common_initial, stored_field: final},
                        'notifications': [], 'errors': [], 'warnings': []},
                        rows[f'KD03-common-{field}-{mode}'])
            self.assertIn('CoreComponentOffered maps to DTO CoreComponent',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
            for field in ('Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral'):
                for mode, clear, reason in [('value', False, False), ('cleared', True, False),
                                           ('reason', False, True), ('cleared-reason', True, True)]:
                    counted = not clear and field != 'PhysicalGeneral'
                    errors = (['ResultsRecordedButNotExamined'] if counted else []) if reason else ([] if counted else ['NoResultsEnteredMessage'])
                    self.assertEqual({'assigned': 2, 'displayed': None if clear else 2,
                        'stored': {name: 2 if name == field and not clear else None
                                   for name in ('Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral')},
                        'notifications': [], 'accepted': not errors, 'errors': errors, 'warnings': []},
                        rows[f'KD03-physical-{field}-{mode}'])
            self.assertIn('no Windows binding, assessment lookup delivery',
                          (stage / 'reference/ADAPTATIONS.md').read_text())
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
            for name, keys, consent in [('empty', [], True), ('existing', ['42'], True),
                                       ('first-new', ['0', '42'], True),
                                       ('later-new', ['42', '0'], True), ('no-consent', ['42'], False)]:
                inserts = not keys or keys[0] != '0'
                final_keys = ['0'] + keys if inserts else keys
                self.assertEqual({'keys': final_keys, 'heading': 'New Result' if inserts else None,
                    'defaultTab': True, 'resultIds': [0, 42] if inserts else [42], 'selected': '42',
                    'resultsAtSetup': [2] if inserts else [], 'keysAtSetup': [final_keys] if inserts else [],
                    'confirmations': [], 'defaults': {'ClientId': 1001, 'Origin': 2, 'Reschedule': 'N'} if inserts else None,
                    'errors': [], 'warnings': ['NoConsentMessage'] if inserts and not consent else []},
                    rows['KD03-ui-insert-' + name])
            self.assertIn('first-tab-only duplicate guard', (stage / 'reference/ADAPTATIONS.md').read_text())
            for name, cancelled, confirms, prepared, selected in [
                ('processing', False, False, False, '42'),
                ('no-selected', True, False, False, None),
                ('no-page', True, False, False, '42'),
                ('empty-key', True, False, False, '42'),
                ('reject', True, True, False, '42'),
                ('accept', False, True, True, '42'),
                ('accept-preserves-cancel', True, True, True, '42'),
            ]:
                self.assertEqual({'cancelled': cancelled,
                    'confirmations': ['ExamResultsConfirmCancelMessage'] if confirms else [],
                    'reloadCalls': [42] if prepared else [], 'height': 55 if prepared else 99,
                    'prepared': ['99'] if prepared else [], 'reloadsAtPreparation': [1] if prepared else [],
                    'selected': selected, 'errors': [], 'warnings': []}, rows['KD03-tab-change-' + name])
            for name, selected, cancelled in [
                ('unchanged', '42', False), ('new-result', '0', False),
                ('negative-key', '-1', False), ('empty-results', '42', False),
                ('unchanged-preserves-cancel', '42', True),
            ]:
                self.assertEqual({'cancelled': cancelled, 'confirmations': [], 'reloadCalls': [],
                    'height': 99, 'prepared': ['99'], 'reloadsAtPreparation': [0],
                    'selected': selected, 'errors': [], 'warnings': []}, rows['KD03-tab-change-' + name])
            self.assertIn('bypasses confirmation/reload', (stage / 'reference/ADAPTATIONS.md').read_text())
            self.assertIn('ChangingSelectedTab', (stage / 'reference/ExtractedSaveControl.cs').read_text())
            self.assertIn('not Windows control construction', (stage / 'reference/ADAPTATIONS.md').read_text())
            for outcome in ('success', 'optimistic-lock', 'fault', 'no-tab'):
                success = outcome == 'success'
                self.assertEqual({'allowed': success, 'calls': 0 if outcome == 'no-tab' else 1,
                    'sameContext': outcome != 'no-tab', 'sameResult': outcome != 'no-tab',
                    'currentIsSelected': True, 'defaultTab': not success,
                    'refreshes': [{'Id': 1001, 'Editable': False, 'SaveCalls': 1, 'DefaultTab': True}] if success else [],
                    'prompts': [] if outcome in ('success', 'no-tab') else ['ExamResultsErrorSavingPrompt'],
                    'errors': [] if outcome in ('success', 'no-tab') else ['synthetic-' + outcome],
                    'warnings': []}, rows['KD03-ui-save-' + outcome])
            self.assertIn('public bool SaveChanges()', (stage / 'reference/ExtractedSaveControl.cs').read_text())
            self.assertIn('Populate is a recording refresh double', (stage / 'reference/ADAPTATIONS.md').read_text())
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
            for name, accepted, prompts, remaining in [
                ('reject-duplicate', False, ['KdpDuplicateExamCodeMessage'], 1),
                ('reject-change', False, ['KdpDuplicateExamCodeMessage', 'KdpResultsExamCodeChangeConfirmationMessage'], 0),
                ('accept-both', True, ['KdpDuplicateExamCodeMessage', 'KdpResultsExamCodeChangeConfirmationMessage'], 0),
            ]:
                self.assertEqual({'valid': accepted, 'validated': accepted,
                    'selected': 'KD03' if accepted else 'KD08', 'confirmations': prompts,
                    'remainingResponses': remaining, 'errors': [], 'warnings': []},
                    rows['KD03-confirm-sequence-' + name])
            for name in ('same-day-other-result', 'same-day-self', 'prior-day-self', 'same-day-other-code'):
                blocked = name == 'same-day-other-result'
                self.assertEqual({'valid': not blocked, 'validated': not blocked,
                    'selected': 'KD08' if blocked else 'KD03',
                    'confirmations': [] if blocked else ['KdpResultsExamCodeChangeConfirmationMessage'],
                    'remainingResponses': 1 if blocked else 0,
                    'errors': ['KdpResultAlreadyEnteredMessage'] if blocked else [], 'warnings': []},
                    rows['KD03-code-identity-' + name])
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
            for name in ('accept', 'reject', 'unchanged'):
                self.assertEqual({'allowed': name != 'reject', 'reloadCalls': [42] if name == 'accept' else [],
                    'height': 55 if name == 'accept' else 99, 'replaced': name == 'accept',
                    'selectedIsStored': name == 'accept', 'siblingUnchanged': True,
                    'confirmations': [] if name == 'unchanged' else ['ExamResultsConfirmCancelMessage'],
                    'errors': [], 'warnings': []}, rows['KD03-cancel-selected-' + name])
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
                        expected.update({'KD03-new-defaults-true', 'KD03-new-defaults-false',
                                         'KD03-ui-insert-empty', 'KD03-ui-insert-existing',
                                         'KD03-ui-insert-later-new', 'KD03-ui-insert-no-consent',
                                         'KD03-get-results-unordered', 'KD03-get-results-ties',
                                         'KD03-get-results-empty'})
                    self.assertEqual(expected, failures)
                finally:
                    extracted.write_text(original)
            # Skipping validation's lookup retrieval must lose fault/retry and
            # empty-row rejection evidence, not merely a service-double assertion.
            retrieval_call = '            GetLocationList();'
            self.assertEqual(1, original.count(retrieval_call))
            try:
                extracted.write_text(original.replace(retrieval_call, '// mutation: skipped validation retrieval'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios']
                            if not row['matches'] and row['id'].startswith('KD03-lookup-validation-')}
                self.assertEqual({f'KD03-lookup-validation-location-{mode}' for mode in
                                  ('missing', 'missing-cached', 'fault-recovery', 'empty-rows')}, failures)
            finally:
                extracted.write_text(original)
            # A wrong DTO destination must be caught even when the getter is unchanged.
            core_assignment = 'set { KdpExaminationResultTo.CoreComponent = value; }'
            self.assertEqual(1, original.count(core_assignment))
            try:
                extracted.write_text(original.replace(core_assignment,
                    'set { KdpExaminationResultTo.Origin = value; }'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-common-CoreComponentOffered-value',
                    'KD03-common-CoreComponentOffered-cleared'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted.write_text(original)
            # Rejected confirmations and date faults must invalidate a previously valid selection.
            reset_validation = 'ExamCodeValidated = false;'
            self.assertEqual(1, original.count(reset_validation))
            try:
                extracted.write_text(original.replace(reset_validation, '// mutation: omitted validation reset'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-confirm-sequence-reject-duplicate',
                    'KD03-confirm-sequence-reject-change',
                    'KD03-code-identity-same-day-other-result'}, failures)
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
            # Unchanged tab transitions must not prompt/reload merely because a
            # selected result exists. Retain guards and mutate only change detection.
            extracted_lifecycle = stage / 'reference/ExtractedLifecycle.cs'
            original_lifecycle = extracted_lifecycle.read_text()
            order_clause = '.OrderByDescending(it => it.ExaminationDate)'
            self.assertEqual(1, original_lifecycle.count(order_clause))
            try:
                extracted_lifecycle.write_text(original_lifecycle.replace(order_clause, ''))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertIn('KD03-get-results-unordered', failures)
                self.assertTrue({'KD03-get-results-ties', 'KD03-get-results-empty'}.isdisjoint(failures))
            finally:
                extracted_lifecycle.write_text(original_lifecycle)
            selected_lookup = 'var kdpExamResultDelegate = KdpExaminationResultDelegates.Single(er => er.PkChildExaminationId == kdpChildExaminationId);'
            self.assertEqual(1, original_lifecycle.count(selected_lookup))
            try:
                extracted_lifecycle.write_text(original_lifecycle.replace(selected_lookup,
                    'var kdpExamResultDelegate = KdpExaminationResultDelegates.First();'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertTrue({'KD03-cancel-selected-accept', 'KD03-cancel-selected-reject',
                    'KD03-cancel-selected-unchanged'}.issubset(failures))
            finally:
                extracted_lifecycle.write_text(original_lifecycle)
            changed_guard = 'kdpExamResultDelegate.KdpExaminationResultTo.hasChanged()'
            self.assertEqual(1, original_lifecycle.count(changed_guard))
            try:
                extracted_lifecycle.write_text(original_lifecycle.replace(changed_guard, 'true'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertTrue({'KD03-tab-change-unchanged',
                    'KD03-tab-change-unchanged-preserves-cancel'}.issubset(failures))
                self.assertTrue({'KD03-tab-change-new-result', 'KD03-tab-change-negative-key',
                    'KD03-tab-change-empty-results'}.isdisjoint(failures))
            finally:
                extracted_lifecycle.write_text(original_lifecycle)
            # Save success must refresh, rather than merely report service dispatch.
            extracted_save_control = stage / 'reference/ExtractedSaveControl.cs'
            original_save_control = extracted_save_control.read_text()
            # Same-key replacement followed by restoration must fail even though
            # the final ordered keys and object references match the original list.
            selection_method = 'public void SelectTabPage()'
            self.assertEqual(1, original_save_control.count(selection_method))
            selection_mutation = '''public void SelectTabPage()
        {
            var tabs = hlxAdminTabControlKdpExamination.TabPages;
            if (selectionOriginalTab == null) {
                selectionOriginalTab = tabs[1];
                tabs[1] = new SaveTabFixture(selectionOriginalTab.Key);
            } else {
                tabs[1] = selectionOriginalTab;
            }
            OriginalSelectTabPage();
        }
        private SaveTabFixture selectionOriginalTab;
        public void OriginalSelectTabPage()'''
            try:
                extracted_save_control.write_text(original_save_control.replace(selection_method, selection_mutation))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                for row in mutant_report['scenarios']:
                    if row['id'].startswith('KD03-ui-tab-select-'):
                        self.assertFalse(row['matches'])
                        self.assertEqual([False, True], row['actual']['orderedTabIdentities'])
                        self.assertEqual(['42', '99'], row['actual']['keys'])
            finally:
                extracted_save_control.write_text(original_save_control)
            extracted_content = stage / 'reference/ExtractedTabContentControl.cs'
            original_content = extracted_content.read_text()
            self.assertEqual(1, original_content.count('if (tabKey != 0)'))
            try:
                extracted_content.write_text(original_content.replace('if (tabKey != 0)', 'if (true)'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-tab-content-new', 'KD03-ui-tab-content-missing-new'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted_content.write_text(original_content)
            # Replace the accumulated child without changing count, sentinel,
            # newest child or any other previously observed property.
            content_add = 'tab.Controls.Add(UcHlxKdpExaminationResult);'
            self.assertEqual(1, original_content.count(content_add))
            try:
                extracted_content.write_text(original_content.replace(content_add, '''
                    if (tabKey == 0 && tab.Controls.Count > 1)
                        tab.Controls[1] = new ucHLXKdpExaminationResult();
                    ''' + content_add))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-tab-content-new'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
                actual = next(row['actual'] for row in mutant_report['scenarios']
                    if row['id'] == 'KD03-ui-tab-content-new')
                self.assertEqual([True, False], actual['orderedControlsIdentities'])
                self.assertEqual(rows['KD03-ui-tab-content-new'],
                    {**actual, 'orderedControlsIdentities': [True, True]})
            finally:
                extracted_content.write_text(original_content)
            extracted_setup = stage / 'reference/ExtractedTabSetupControl.cs'
            original_setup = extracted_setup.read_text()
            # Collection replacement/restoration preserves every tab object and
            # final collection identity, but must fail the per-call observation.
            setup_method = 'public void SetUpTabPages()'
            self.assertEqual(1, original_setup.count(setup_method))
            setup_mutation = '''public void SetUpTabPages()
        {
            if (setupOriginalCollection == null) {
                setupOriginalCollection = hlxAdminTabControlKdpExamination.TabPages;
                hlxAdminTabControlKdpExamination.TabPages = new(setupOriginalCollection);
            } else {
                hlxAdminTabControlKdpExamination.TabPages = setupOriginalCollection;
            }
            OriginalSetUpTabPages();
        }
        private List<SaveTabFixture> setupOriginalCollection;
        public void OriginalSetUpTabPages()'''
            try:
                extracted_setup.write_text(original_setup.replace(setup_method, setup_mutation))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-ui-tab-setup-' + name for name in
                    ('default', 'current', 'new', 'null-current', 'empty')}, failures)
                for row in mutant_report['scenarios']:
                    if row['id'] in failures:
                        self.assertEqual([False, True], row['actual']['collectionIdentities'])
                        self.assertTrue(row['actual']['collectionIdentity'])
                        self.assertEqual([True, True], row['actual']['orderedIdentities'])
            finally:
                extracted_setup.write_text(original_setup)
            # Intermediate current-tab replacement and flag toggling must not
            # escape detection when restored before the second source call.
            state_mutation = '''public void SetUpTabPages()
        {
            if (setupStateCalls++ == 0) {
                setupSavedCurrent = currentTab;
                setupSavedDefault = setDefaultTabPage;
                OriginalSetUpTabPages();
                currentTab = new SaveTabFixture(currentTab?.Key);
                setDefaultTabPage = !setDefaultTabPage;
            } else {
                currentTab = setupSavedCurrent;
                setDefaultTabPage = setupSavedDefault;
                OriginalSetUpTabPages();
            }
        }
        private int setupStateCalls;
        private SaveTabFixture setupSavedCurrent;
        private bool setupSavedDefault;
        public void OriginalSetUpTabPages()'''
            try:
                extracted_setup.write_text(original_setup.replace(setup_method, state_mutation))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-ui-tab-setup-' + name for name in
                    ('default', 'current', 'new', 'null-current', 'empty')}, failures)
                for row in mutant_report['scenarios']:
                    if row['id'] in failures:
                        self.assertEqual([False, True], row['actual']['currentIdentities'])
                        self.assertNotEqual(*row['actual']['defaultStates'])
                        self.assertTrue(row['actual']['currentUnchanged'])
                        self.assertTrue(row['actual']['defaultUnchanged'])
                        self.assertTrue(row['actual']['exactSelection'])
            finally:
                extracted_setup.write_text(original_setup)
            # A nonselected tab may be replaced during dispatch and restored
            # before return without changing any existing post-call observation.
            dispatch_mutation = '''public void SetUpTabPages()
        {
            if (hlxAdminTabControlKdpExamination.TabPages.Count == 0) {
                OriginalSetUpTabPages();
                return;
            }
            var index = setDefaultTabPage || currentTab == null ? 1 : 0;
            var original = hlxAdminTabControlKdpExamination.TabPages[index];
            var replacement = new SaveTabFixture(original.Key) { Text = original.Text };
            hlxAdminTabControlKdpExamination.TabPages[index] = replacement;
            OriginalSetUpTabPages();
            original.Key = replacement.Key;
            original.Text = replacement.Text;
            hlxAdminTabControlKdpExamination.TabPages[index] = original;
        }
        public void OriginalSetUpTabPages()'''
            try:
                extracted_setup.write_text(original_setup.replace(setup_method, dispatch_mutation))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                failures = {row['id'] for row in mutant_report['scenarios'] if not row['matches']}
                self.assertEqual({'KD03-ui-tab-setup-' + name for name in
                    ('default', 'current', 'new', 'null-current')}, failures)
                for row in mutant_report['scenarios']:
                    if row['id'] in failures:
                        actual = row['actual']
                        self.assertEqual([False, False], actual['orderedIdentitiesAtPreparation'])
                        self.assertEqual(rows[row['id']],
                            {**actual, 'orderedIdentitiesAtPreparation': [True, True]})
            finally:
                extracted_setup.write_text(original_setup)
            zero_guard = 'PkChildExaminationId != NewExamNumber'
            self.assertEqual(1, original_setup.count(zero_guard))
            try:
                extracted_setup.write_text(original_setup.replace(zero_guard, 'PkChildExaminationId >= NewExamNumber'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-tab-setup-new'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted_setup.write_text(original_setup)
            tail_removal = 'TabPages.RemoveAt(hlxAdminTabControlKdpExamination.TabPages.Count - 1);'
            self.assertEqual(1, original_save_control.count(tail_removal))
            try:
                extracted_save_control.write_text(original_save_control.replace(tail_removal, 'TabPages.RemoveAt(0);'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-tab-count-grow-shrink', 'KD03-ui-tab-count-shrink-grow'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted_save_control.write_text(original_save_control)
            insert_call = '            kdpExaminationDelegate.AddNewKdpResult();'
            self.assertEqual(1, original_save_control.count(insert_call))
            try:
                extracted_save_control.write_text(original_save_control.replace(insert_call, '// mutation: omitted new result'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-insert-empty', 'KD03-ui-insert-existing',
                                  'KD03-ui-insert-later-new', 'KD03-ui-insert-no-consent'},
                                 {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted_save_control.write_text(original_save_control)
            refresh_call = 'Populate(ID, Editable);'
            self.assertEqual(1, original_save_control.count(refresh_call))
            try:
                extracted_save_control.write_text(original_save_control.replace(refresh_call, '// mutation: omitted UI refresh'))
                mutant = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(1, mutant.returncode, mutant.stdout + mutant.stderr)
                mutant_report = json.loads((stage / 'reference-report.json').read_text())
                self.assertEqual({'KD03-ui-save-success'},
                    {row['id'] for row in mutant_report['scenarios'] if not row['matches']})
            finally:
                extracted_save_control.write_text(original_save_control)
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
