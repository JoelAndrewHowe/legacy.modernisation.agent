"""Pi wrapper contract tests; these doubles are not real-agent evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PiAgentTests(unittest.TestCase):
    def test_request_forwarding_isolation_and_exit_propagation(self):
        with tempfile.TemporaryDirectory(prefix='lmf pi ') as tmp:
            root = Path(tmp)
            output = root / 'output'
            output.mkdir()
            request = root / 'request.json'
            request.write_text(json.dumps({'Stage': 'characterise', 'OutputDirectory': str(output)}))
            fake = root / 'fake-pi'
            fake.write_text('#!' + sys.executable + '\n'
                'import json, os, sys\n'
                'from pathlib import Path\n'
                'Path("invocation.json").write_text(json.dumps({"args":sys.argv[1:], "cwd":os.getcwd()}))\n'
                'print("agent stdout")\n'
                'print("agent stderr", file=sys.stderr)\n'
                'sys.exit(7)\n')
            fake.chmod(0o755)
            env = dict(os.environ, LMF_PI_EXECUTABLE=str(fake),
                       LMF_PI_PROVIDER='test-provider', LMF_PI_MODEL='test-model')
            result = subprocess.run([sys.executable, str(ROOT / 'adapters/pi_agent.py'), str(request)],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(7, result.returncode)
            self.assertIn('agent stdout', result.stdout)
            self.assertIn('agent stderr', result.stderr)
            invocation = json.loads((output / 'invocation.json').read_text())
            self.assertEqual(str(output), invocation['cwd'])
            args = invocation['args']
            self.assertIn('@' + str(request), args)
            self.assertEqual('test-provider', args[args.index('--provider') + 1])
            self.assertEqual('test-model', args[args.index('--model') + 1])
            for option in ('--print', '--no-session', '--no-context-files', '--no-extensions', '--no-mcp'):
                self.assertIn(option, args)
            self.assertIn('Never approve a revision', args[-1])
            self.assertFalse((output / 'results.json').exists())

    def test_invalid_stage_and_provider_without_model_fail_before_launch(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / 'request.json'
            env = dict(os.environ, LMF_PI_EXECUTABLE='/nonexistent/pi', LMF_PI_PROVIDER='test')
            env.pop('LMF_PI_MODEL', None)
            for stage, diagnostic in [('unknown', 'Unsupported LMF stage'),
                                      ('convert', 'requires LMF_PI_MODEL')]:
                request.write_text(json.dumps({'Stage': stage, 'OutputDirectory': tmp}))
                result = subprocess.run([sys.executable, str(ROOT / 'adapters/pi_agent.py'), str(request)],
                                        env=env, capture_output=True, text=True)
                self.assertNotEqual(0, result.returncode)
                self.assertIn(diagnostic, result.stderr)


if __name__ == '__main__':
    unittest.main()
