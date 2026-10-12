#!/usr/bin/env python3
"""Fail-closed runner-executed Refactor gates, including real browser execution."""
import hashlib
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request


def verify(root):
    for name in ('results.json', 'parity-report.json', 'persistence-report.json', 'browser-report.json', 'browser.png'):
        (root / name).unlink(missing_ok=True)
    reference = root.parent / 'characterise'
    for name in ('scenarios.json', 'fixtures.json'):
        if (root / name).read_bytes() != (reference / name).read_bytes():
            raise ValueError('Approved input differs: ' + name)
    commands = []
    def run(command, log):
        commands.append(command)
        with (root / log).open('w') as output:
            subprocess.run(command, cwd=root, stdout=output, stderr=subprocess.STDOUT, check=True, timeout=240)
    project = root / 'app/Hcwp.csproj'
    run(['dotnet', 'build', str(project)], 'build.log')
    # Check newly introduced C# formatting; approved legacy structure is deliberately retained.
    run(['dotnet', 'format', 'whitespace', str(project), '--no-restore', '--verify-no-changes', '--include',
         'app/Program.cs', 'app/RecordingService.cs', 'app/PersistenceChecks.cs'], 'style.log')
    scenarios = json.loads((root / 'scenarios.json').read_text())
    ids = [row['id'] for row in scenarios]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Nonempty unique scenario identities required')
    observations = []
    for stage, target in [('reference', reference / 'reference/Reference.csproj'), ('refactored', project)]:
        destination = root / (stage + '-observations.json')
        destination.unlink(missing_ok=True)
        run(['dotnet', 'run', '--project', str(target), '--', str(root / 'scenarios.json'), str(root / 'fixtures.json'), str(destination)], stage + '.log')
        actual = json.loads(destination.read_text())
        if [row['id'] for row in actual] != ids:
            raise ValueError(stage + ' scenario identity/order mismatch')
        observations.append(actual)
    rows = [{'id': scenario['id'], 'expected': scenario['then'], 'reference': baseline['observation'],
             'refactored': target['observation'], 'matches': scenario['then'] == baseline['observation'] == target['observation']}
            for scenario, baseline, target in zip(scenarios, *observations)]
    failed = sum(not row['matches'] for row in rows)
    report = {'stage': 'refactor', 'approvedRevision': json.loads((root / 'refactor-manifest.json').read_text())['approvedRevision'],
              'scenarioRevision': hashlib.sha256((root / 'scenarios.json').read_bytes()).hexdigest(), 'commands': commands,
              'evidence': 'parity with extracted legacy logic', 'scenarios': rows,
              'limitations': ['No original Windows/Oracle parity', 'No real services/clinical lookups',
                              'Temporary EF Core in-memory storage; no PostgreSQL', 'Appointments/recalls excluded', 'No real-agent run']}
    (root / 'parity-report.json').write_text(json.dumps(report, indent=2) + '\n')
    if failed:
        (root / 'results.json').write_text(json.dumps({'passed': len(rows) - failed, 'failed': failed, 'skipped': 0}))
        return 1
    run(['dotnet', 'run', '--no-build', '--project', str(project), '--', '--persistence-check', str(root / 'persistence-report.json')], 'persistence.log')
    persistence = json.loads((root / 'persistence-report.json').read_text())
    if persistence['passed'] <= 0 or persistence['failed'] or persistence['skipped']:
        raise ValueError('Persistence gate failed')
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    url = f'http://127.0.0.1:{port}'
    command = ['dotnet', 'run', '--no-build', '--project', str(project), '--', '--urls', url]
    commands.append(command)
    with (root / 'server.log').open('w') as log:
        server = subprocess.Popen(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(100):
                if server.poll() is not None:
                    raise ValueError('Browser server exited; see server.log')
                try:
                    with urllib.request.urlopen(url, timeout=1):
                        break
                except OSError:
                    time.sleep(0.2)
            else:
                raise ValueError('Browser server did not start')
            run([sys.executable, str(root / 'browser.py'), url, str(root)], 'browser.log')
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait()
    browser = json.loads((root / 'browser-report.json').read_text())
    if browser['passed'] <= 0 or browser['failed'] or browser['skipped']:
        raise ValueError('Browser gate failed')
    report['persistence'] = persistence
    report['browser'] = browser
    report['commands'] = commands
    (root / 'parity-report.json').write_text(json.dumps(report, indent=2) + '\n')
    counts = {'passed': len(rows) + persistence['passed'] + browser['passed'], 'failed': 0, 'skipped': 0}
    (root / 'results.json').write_text(json.dumps(counts) + '\n')
    print(json.dumps(counts))
    return 0


if __name__ == '__main__':
    sys.exit(verify(Path(__file__).resolve().parent))
