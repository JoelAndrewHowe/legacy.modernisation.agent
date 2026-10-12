"""Generated final assembly: approved parity, EF read-back and real browser gates."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'adapters'))
from hcwp_characterise import generate

BUNDLE = ROOT.parents[1] / 'example-code/HCWP Core (pseudonymised) - single file.txt'


class RefactorTests(unittest.TestCase):
    def test_final_application_and_failed_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            target = workspace / 'target.md'
            target.write_text('Blazor with EF Core in-memory persistence')
            generate({'Stage': 'characterise', 'Source': str(BUNDLE), 'Target': str(target),
                      'OutputDirectory': str(workspace / 'characterise')})
            for stage in ('convert', 'refactor'):
                generate({'Stage': stage, 'Workspace': str(workspace), 'OutputDirectory': str(workspace / stage),
                          'ApprovedRevision': 'isolated-test-approval'})
            final = workspace / 'refactor'
            def verify(success):
                run = subprocess.run([sys.executable, str(final / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(success, run.returncode == 0, run.stdout + run.stderr)
            verify(True)
            report = json.loads((final / 'parity-report.json').read_text())
            self.assertEqual(371, len(report['scenarios']))
            self.assertTrue(all(row['matches'] for row in report['scenarios']))
            self.assertEqual(4, report['persistence']['passed'])
            self.assertEqual(6, report['browser']['passed'])
            self.assertTrue((final / 'browser.png').exists())
            # A target calculation mismatch identifies scenario-level differences.
            bmi = final / 'app/Legacy/ExtractedBmi.cs'
            original = bmi.read_text()
            bmi.write_text(original.replace(')), 2)', ')), 1)'))
            verify(False)
            report = json.loads((final / 'parity-report.json').read_text())
            self.assertTrue(any(not row['matches'] for row in report['scenarios']))
            self.assertGreater(json.loads((final / 'results.json').read_text())['failed'], 0)
            bmi.write_text(original)
            # No browser fallback: executable failure removes prior successful results.
            browser = final / 'browser.py'
            original_browser = browser.read_text()
            browser.write_text('raise RuntimeError("deliberately unavailable browser")\n')
            verify(False)
            self.assertFalse((final / 'results.json').exists())
            self.assertFalse((final / 'browser-report.json').exists())
            browser.write_text(original_browser)
            # A real persistence defect is not hidden by kernel parity.
            service = final / 'app/RecordingService.cs'
            original_service = service.read_text()
            service.write_text(original_service.replace('dto.HeadCircumference.Value);', '35);'))
            verify(False)
            self.assertFalse((final / 'results.json').exists())
            self.assertGreater(json.loads((final / 'persistence-report.json').read_text())['failed'], 0)
            service.write_text(original_service)
            verify(True)
            # Changed approved inputs fail before build and invalidate success evidence.
            (final / 'scenarios.json').write_text('[]')
            verify(False)
            self.assertFalse((final / 'results.json').exists())
            self.assertFalse((final / 'parity-report.json').exists())


if __name__ == '__main__':
    unittest.main()
