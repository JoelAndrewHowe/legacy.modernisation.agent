#!/usr/bin/env python3
"""Runner-executed mechanical Convert parity gate; no agent-authored success."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def verify(root):
    # Evidence belongs only to this invocation, including failures before comparison.
    for name in ('results.json', 'parity-report.json'):
        (root / name).unlink(missing_ok=True)
    reference = root.parent / 'characterise'
    manifest = json.loads((root / 'port-manifest.json').read_text())
    for name in ('scenarios.json', 'fixtures.json'):
        if (root / name).read_bytes() != (reference / name).read_bytes():
            raise ValueError('Approved input differs: ' + name)
    scenarios = json.loads((reference / 'scenarios.json').read_text())
    ids = [s['id'] for s in scenarios]
    if not ids or len(set(ids)) != len(ids):
        raise ValueError('Nonempty unique scenario identities required')
    commands = []
    observations = []
    for stage, project in [('reference', reference / 'reference/Reference.csproj'),
                           ('converted', root / 'converted/Converted.csproj')]:
        destination = root / (stage + '-observations.json')
        destination.unlink(missing_ok=True)
        command = ['dotnet', 'run', '--project', str(project), '--',
                   str(reference / 'scenarios.json'), str(reference / 'fixtures.json'), str(destination)]
        commands.append(command)
        subprocess.run(command, cwd=root, check=True)
        actual = json.loads(destination.read_text())
        if [row['id'] for row in actual] != ids:
            raise ValueError(stage + ' observation identity/order mismatch')
        observations.append(actual)
    rows = []
    for scenario, baseline, converted in zip(scenarios, *observations):
        expected = scenario['then']
        rows.append({'id': scenario['id'], 'expected': expected,
                     'reference': baseline['observation'], 'converted': converted['observation'],
                     'matches': expected == baseline['observation'] == converted['observation']})
    failed = sum(not r['matches'] for r in rows)
    report = {'stage': 'convert', 'approvedRevision': manifest['approvedRevision'],
              'evidence': 'parity with extracted legacy logic', 'commands': commands,
              'scenarioRevision': hashlib.sha256((reference / 'scenarios.json').read_bytes()).hexdigest(),
              'scenarios': rows, 'limitations': ['No original Windows/Oracle verification',
              'No live services or persistence read-back', 'No Blazor/browser verification; Refactor pending']}
    (root / 'parity-report.json').write_text(json.dumps(report, indent=2) + '\n')
    (root / 'results.json').write_text(json.dumps({'passed': len(rows) - failed, 'failed': failed, 'skipped': 0}) + '\n')
    print(f'Passed: {len(rows) - failed}; Failed: {failed}; Skipped: 0')
    return 1 if failed else 0


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    sys.exit(verify(root))
