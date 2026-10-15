#!/usr/bin/env python3
"""Retain a fresh Convert evidence bundle; does not approve or complete the stage."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-prefix', required=True)
    args = parser.parse_args()
    prefix = args.evidence_prefix
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', prefix):
        parser.error('unsafe evidence prefix')
    names = [prefix, prefix + '-prestart', prefix + '-parity', prefix + '-parity-runtime',
             prefix + '-parity-final', prefix + '-final']
    if any((HERE / 'evidence' / n).exists() for n in names):
        parser.error('Retained evidence exists; use a fresh prefix')
    evidence = HERE / 'evidence' / prefix
    evidence.mkdir(parents=True, exist_ok=False)
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'validatorFindings': [],
              'scope': 'Convert provenance and parity evidence only; independent stage review pending',
              'commands': [], 'errors': [], 'passed': False}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', DOTNET_CLI_TELEMETRY_OPTOUT='1')

    def run(label, argv):
        result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True)
        (evidence / (label + '.log')).write_text(result.stdout + result.stderr)
        report['commands'].append({'argv': argv, 'cwd': str(ROOT), 'exitCode': result.returncode,
                                   'log': label + '.log'})
        if result.returncode:
            raise ValueError('Command failed: ' + label)
        return result.stdout

    def load(name, file):
        return json.loads((HERE / 'evidence' / name / file).read_text())

    try:
        run('working-tree-before', ['git', 'status', '--short'])
        run('prestart', [sys.executable, str(HERE / 'check-prerequisites.py'), '--evidence-prefix', prefix + '-prestart'])
        approval = json.loads(run('approval-tests', [sys.executable, str(HERE / 'test-prerequisites.py')]))
        comparator = json.loads(run('comparator-tests', [sys.executable, str(HERE / 'test-parity.py')]))
        for result in (approval, comparator):
            if result['passed'] <= 0 or result['failed'] or result['skipped']:
                raise ValueError('Nonpassing or empty isolated tests')
        report['isolatedTests'] = {'approval': approval, 'comparator': comparator}
        run('parity', [sys.executable, str(HERE / 'verify'), '--evidence-prefix', prefix + '-parity'])
        parity = load(prefix + '-parity', 'parity.json')
        if not parity['passed'] or parity['counts'] != {'required': 53, 'executed': 53, 'passed': 53, 'failed': 0, 'skipped': 0}:
            raise ValueError('Incomplete/nonpassing parity')
        report['parity'] = {'report': prefix + '-parity/parity.json',
                            'observations': prefix + '-parity/observations.json', 'counts': parity['counts']}
        # The historical one-shot preservation checker is intentionally not rerun/overwritten.
        preservation = load('task-2-build', 'port-preservation.json')
        if preservation['passed'] != 3 or preservation['failed'] or preservation['skipped']:
            raise ValueError('Nonpassing retained source preservation')
        for check in preservation['checks']:
            if sha(Path(check['source'])) != check['sourceSha256'] or sha(Path(check['target'])) != check['targetSha256']:
                raise ValueError('Source preservation identities changed')
        report['sourcePreservation'] = 'task-2-build/port-preservation.json (current identities rechecked)'
        run('final', [sys.executable, str(HERE / 'check-prerequisites.py'), '--evidence-prefix', prefix + '-final'])
        before = HERE / 'evidence' / (prefix + '-prestart') / 'input-identities.sha256'
        after = HERE / 'evidence' / (prefix + '-final') / 'input-identities.sha256'
        if before.read_bytes() != after.read_bytes():
            raise ValueError('Approved input identities changed during task')
        report['inputIntegrity'] = {'unchanged': True, 'identityManifestSha256': sha(after),
                                    'prestart': str(before.relative_to(HERE)), 'final': str(after.relative_to(HERE)),
                                    'identityCount': load(prefix + '-final', 'prerequisites.json')['identityCount'],
                                    'basis': 'Approved packet reconciles input membership, all hashes and immutable iteration-001 approval'}
        run('diff-check', ['git', 'diff', '--check', '--', str(HERE)])
        run('working-tree-after', ['git', 'status', '--short'])
        report['passed'] = True
    except Exception as error:
        report['errors'].append(repr(error))
    # Bind all retained evidence and inspectable source/docs; exclude mutable compiler caches.
    files = [p for p in HERE.iterdir() if p.is_file()] + list((HERE / 'src').glob('*.cs')) + list((HERE / 'src').glob('*.csproj'))
    for name in names:
        files += [p for p in (HERE / 'evidence' / name).glob('*') if p.is_file()]
    files += [HERE / 'evidence/task-2-build/port-preservation.json']
    identities = ''.join(f'{sha(p)}  {p.relative_to(ROOT).as_posix()}\n' for p in sorted(set(files)))
    (evidence / 'artifact-identities.sha256').write_text(identities)
    report.update(finishedAt=datetime.now(timezone.utc).isoformat(),
                  artifactManifestSha256=sha(evidence / 'artifact-identities.sha256'),
                  exitCode=0 if report['passed'] else 1)
    with (evidence / 'report.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return report['exitCode']


if __name__ == '__main__':
    sys.exit(main())
