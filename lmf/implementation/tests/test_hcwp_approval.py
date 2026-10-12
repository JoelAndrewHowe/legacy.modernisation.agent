"""Acceptance examples 1–2: actual extracted-reference gate, no target generation."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT.parents[1] / 'example-code/HCWP Core (pseudonymised) - single file.txt'


class HcwpApprovalTests(unittest.TestCase):
    def test_reference_verification_and_revision_bound_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / 'migration'
            target = root / 'target.md'
            target.write_text('Modern .NET server-interactive Blazor with EF Core in-memory persistence.')
            config = root / 'agent.json'
            config.write_text(json.dumps({'command': {'executable': sys.executable,
                'arguments': [str(ROOT / 'adapters/hcwp_characterise.py')]}}))

            def cli(command, *args, code=0):
                result = subprocess.run([str(ROOT / 'lmf'), command, '--workspace', str(workspace),
                    *map(str, args)], capture_output=True, text=True)
                self.assertEqual(code, result.returncode, result.stdout + result.stderr)
                return result

            def state():
                return json.loads((workspace / 'state.json').read_text())

            def no_target():
                self.assertFalse((workspace / 'convert').exists())
                self.assertFalse((workspace / 'refactor').exists())

            cli('characterise', '--source', BUNDLE, '--target', target, '--agent', config, '--repairs', '0')
            first = state()
            self.assertEqual('awaiting-approval', first['Status'])
            self.assertIsNone(first['ApprovedRevision'])
            self.assertEqual('accepted', first['Stages'][0]['Status'])
            stage = workspace / 'characterise'
            evidence = stage / 'attempts/0001'
            retained = {p.relative_to(evidence): p.read_bytes() for p in evidence.rglob('*') if p.is_file()}
            report = json.loads((stage / 'reference-report.json').read_text())
            counts = json.loads((evidence / 'results-0.json').read_text())
            scenarios = json.loads((stage / 'scenarios.json').read_text())
            self.assertEqual(len(scenarios), len(report['scenarios']))
            self.assertEqual({'passed': len(scenarios), 'failed': 0, 'skipped': 0}, counts)
            self.assertTrue(all(row['matches'] for row in report['scenarios']))
            self.assertTrue((evidence / 'check-0.command.json').is_file())
            self.assertIn('verify.py', (evidence / 'check-0.command.json').read_text())
            no_target()
            cli('resume')
            self.assertEqual(first, state())
            no_target()
            cli('approve', '--revision', 'stale', code=1)
            self.assertIsNone(state()['ApprovedRevision'])
            # This approval is a simulated operator action in an isolated test,
            # never approval of the retained demonstration workspace.
            cli('approve', '--revision', first['Revision'])
            self.assertEqual(first['Revision'], state()['ApprovedRevision'])
            behaviour = stage / 'behaviour.md'
            behaviour.write_text(behaviour.read_text() + '\nChanged reviewed behaviour.\n')
            cli('resume')
            second = state()
            self.assertEqual('awaiting-approval', second['Status'])
            self.assertIsNone(second['ApprovedRevision'])
            self.assertEqual(2, second['Stages'][0]['Attempts'])
            # Generation restores deterministic artifacts; even an identical
            # regenerated revision requires a fresh explicit approval action.
            no_target()
            self.assertTrue((stage / 'attempts/0002/results-0.json').is_file())
            for relative, contents in retained.items():
                self.assertEqual(contents, (evidence / relative).read_bytes(), str(relative))


if __name__ == '__main__':
    unittest.main()
