#!/usr/bin/env python3
"""Execute extracted C#, then compare actual observations to reviewed scenarios."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parent
scenarios = json.loads((root / 'scenarios.json').read_text())
if not scenarios or len({s['id'] for s in scenarios}) != len(scenarios):
    raise ValueError('Scenario suite must be nonempty with unique identifiers')
command = ['dotnet', 'run', '--project', str(root / 'reference/Reference.csproj'), '--',
           str(root / 'scenarios.json'), str(root / 'fixtures.json'), str(root / 'observations.json')]
(root / 'observations.json').unlink(missing_ok=True)
subprocess.run(command, cwd=root, check=True)
actual = json.loads((root / 'observations.json').read_text())
if len(actual) != len(scenarios) or [a['id'] for a in actual] != [s['id'] for s in scenarios]:
    raise ValueError('Observation scenario identity/order mismatch')
rows = [{'id': s['id'], 'expected': s['then'], 'actual': a['observation'],
         'matches': s['then'] == a['observation']} for s, a in zip(scenarios, actual)]
failed = sum(not r['matches'] for r in rows)
(root / 'results.json').write_text(json.dumps({'passed': len(rows) - failed, 'failed': failed, 'skipped': 0}) + '\n')
(root / 'reference-report.json').write_text(json.dumps({
    'stage': 'characterise', 'evidence': 'parity with extracted legacy logic',
    'scenarioRevision': hashlib.sha256((root / 'scenarios.json').read_bytes()).hexdigest(),
    'command': command, 'scenarios': rows,
    'limitations': ['Validator/calculation/age subset only', 'No original Windows/Oracle verification',
                    'No persistence verification', 'Delegate interactions and repeat flags unresolved',
                    'WeeksBetween adaptation requires review', 'No target/browser verification']}, indent=2) + '\n')
print(f'Passed: {len(rows) - failed}; Failed: {failed}; Skipped: 0')
sys.exit(1 if failed else 0)
