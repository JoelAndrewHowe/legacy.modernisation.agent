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
            self.assertEqual(['HeadCircumferenceInvalidFormatMessage'], rows['KD03-head-field-100']['errors'])
            self.assertEqual(100, rows['KD03-head-save-100']['saved']['HeadCircumference'])
            self.assertEqual(['NoResultsEnteredMessage'], rows['KD03-general-alone']['errors'])
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
            approve = cli('approve', '--workspace', str(workspace), '--revision', state['Revision'])
            self.assertNotEqual(0, approve.returncode)
            self.assertIn('blocking gaps', approve.stderr)
            # Verification must execute and compare, not merely return counts.
            scenarios = json.loads((stage / 'scenarios.json').read_text())
            scenarios[0]['then']['saved']['Heart'] = 3
            (stage / 'scenarios.json').write_text(json.dumps(scenarios))
            check = subprocess.run([sys.executable, str(stage / 'verify.py')], capture_output=True, text=True)
            self.assertNotEqual(0, check.returncode)
            self.assertEqual(1, json.loads((stage / 'results.json').read_text())['failed'])
            report = json.loads((stage / 'reference-report.json').read_text())
            self.assertFalse(report['scenarios'][0]['matches'])

    def test_adapter_rejects_unsupported_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / 'request.json'
            request.write_text(json.dumps({'Stage': 'convert'}))
            run = subprocess.run([sys.executable, str(ROOT / 'adapters/hcwp_characterise.py'), str(request)], capture_output=True, text=True)
            self.assertNotEqual(0, run.returncode)
            self.assertIn('only implements Characterise', run.stderr)


if __name__ == '__main__':
    unittest.main()
