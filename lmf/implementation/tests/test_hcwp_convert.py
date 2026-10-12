"""Convert port and mechanical mismatch gate on the supplied HCWP suite."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'adapters'))
from hcwp_characterise import generate

BUNDLE = ROOT.parents[1] / 'example-code/HCWP Core (pseudonymised) - single file.txt'


class ConvertTests(unittest.TestCase):
    def test_standalone_port_and_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            reference = workspace / 'characterise'
            target = workspace / 'target.md'
            target.write_text('Blazor with EF Core in-memory persistence')
            generate({'Stage': 'characterise', 'Source': str(BUNDLE), 'Target': str(target),
                      'OutputDirectory': str(reference)})
            converted = workspace / 'convert'
            converted.mkdir()
            generate({'Stage': 'convert', 'Workspace': str(workspace),
                      'OutputDirectory': str(converted), 'ApprovedRevision': 'isolated-test-approval'})
            def verify(code):
                result = subprocess.run([sys.executable, str(converted / 'verify.py')], capture_output=True, text=True)
                self.assertEqual(code, result.returncode, result.stdout + result.stderr)
            verify(0)
            report = json.loads((converted / 'parity-report.json').read_text())
            scenarios = json.loads((reference / 'scenarios.json').read_text())
            self.assertEqual(len(scenarios), len(report['scenarios']))
            self.assertTrue(all(r['matches'] for r in report['scenarios']))
            for source in (reference / 'reference').glob('*.cs'):
                self.assertEqual(source.read_bytes(), (converted / 'converted' / source.name).read_bytes())
            # A changed calculation must produce scenario-level differences, not pass counts.
            bmi = converted / 'converted/ExtractedBmi.cs'
            original_bmi = bmi.read_text()
            self.assertIn(')), 2)', original_bmi)
            bmi.write_text(original_bmi.replace(')), 2)', ')), 1)'))
            verify(1)
            mismatch = json.loads((converted / 'parity-report.json').read_text())
            self.assertTrue(any(not row['matches'] for row in mismatch['scenarios']))
            self.assertGreater(json.loads((converted / 'results.json').read_text())['failed'], 0)
            bmi.write_text(original_bmi)
            verify(0)
            # Malformed target observations must not leave stale successful evidence.
            driver = converted / 'converted/Program.cs'
            text = driver.read_text()
            self.assertIn('"observation"', text)
            driver.write_text(text.replace('"observation"', '"broken-observation"'))
            verify(1)
            self.assertFalse((converted / 'results.json').exists())
            self.assertFalse((converted / 'parity-report.json').exists())
            shutil.copyfile(reference / 'reference/Program.cs', driver)
            verify(0)
            # Build failures also invalidate the preceding successful parity report.
            driver.write_text(text + '\nthis is not valid C#;\n')
            verify(1)
            self.assertFalse((converted / 'results.json').exists())
            self.assertFalse((converted / 'parity-report.json').exists())
            driver.write_text(text)
            verify(0)
            scenarios[0]['then']['deliberateMismatch'] = True
            (converted / 'scenarios.json').write_text(json.dumps(scenarios))
            verify(1)
            self.assertFalse((converted / 'results.json').exists())
            self.assertFalse((converted / 'parity-report.json').exists())


if __name__ == '__main__':
    unittest.main()
