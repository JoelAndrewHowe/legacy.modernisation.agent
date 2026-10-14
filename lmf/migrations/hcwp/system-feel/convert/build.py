#!/usr/bin/env python3
"""Approval-gated nonincremental build; not a scenario/parity runner."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-prefix', required=True)
    args = parser.parse_args()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    gate = subprocess.run([sys.executable, str(HERE / 'check-prerequisites.py'),
                           '--evidence-prefix', args.evidence_prefix],
                          capture_output=True, text=True, env=env)
    if gate.returncode:
        print(gate.stderr, file=sys.stderr)
        return gate.returncode
    evidence = HERE / 'evidence' / args.evidence_prefix
    report = {'startedAt': datetime.now(timezone.utc).isoformat(),
              'scope': 'Port build only; no parity claim', 'validatorFindings': []}
    sources = list((HERE / 'src').glob('*.cs')) + list((HERE / 'src').glob('*.csproj'))
    report['sourceSha256'] = {str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    command = ['dotnet', 'build', str(HERE / 'src/Converted.csproj'), '-c', 'Release', '--no-incremental', '--nologo']
    result = subprocess.run(command, capture_output=True, text=True, env=env)
    with (evidence / 'build.log').open('x') as stream:
        stream.write(result.stdout + result.stderr)
    report.update(command=command, exitCode=result.returncode, passed=result.returncode == 0,
                  dotnetVersion=subprocess.check_output(['dotnet', '--version'], text=True).strip(),
                  finishedAt=datetime.now(timezone.utc).isoformat())
    if result.returncode == 0:
        dll = HERE / 'src/bin/Release/net10.0/Converted.dll'
        report['binarySha256'] = hashlib.sha256(dll.read_bytes()).hexdigest()
    with (evidence / 'build.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
