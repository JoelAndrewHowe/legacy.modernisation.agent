#!/usr/bin/env python3
"""Check disclosed port deltas only, not behavioural parity."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent / 'characterise/reference'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def normalise(text):
    return '\n'.join(line for line in text.splitlines() if not line.startswith('//') and line != 'namespace Hcwp.SystemFeel.Converted;')

pairs = [('Legacy.cs', 'PatientSummaryAndResults.cs'), ('Compatibility.cs', 'Compatibility.cs'), ('Program.cs', 'ObservationAdapter.cs')]
checks = []
for original, converted in pairs:
    source, target = REFERENCE / original, HERE / 'src' / converted
    a, b = normalise(source.read_text()), normalise(target.read_text())
    if original == 'Program.cs':
        # Only the entry-point signature and pre-observation approval gate differ.
        start = b.index('    public static void Main(string[] args) {')
        end = b.index('        CultureInfo.CurrentCulture', start)
        b = b[:start] + '    public static void Main() {\n' + b[end:]
    checks.append({'source': str(source), 'target': str(target),
                   'sourceSha256': digest(source), 'targetSha256': digest(target),
                   'identicalAfterDeclaredAdaptations': a == b})
report = {'scope': 'Source preservation, not executable scenario parity', 'checks': checks,
          'passed': sum(c['identicalAfterDeclaredAdaptations'] for c in checks),
          'failed': sum(not c['identicalAfterDeclaredAdaptations'] for c in checks), 'skipped': 0}
with (HERE / 'evidence/task-2-build/port-preservation.json').open('x') as stream:
    stream.write(json.dumps(report, indent=2) + '\n')
print(json.dumps(report))
raise SystemExit(1 if report['failed'] else 0)
