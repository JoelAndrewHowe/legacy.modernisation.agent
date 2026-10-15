#!/usr/bin/env python3
"""Review fresh Convert evidence; never marks plan tasks or approves Refactor."""
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
PACKET = HERE.parent / 'characterise'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def equal(a, b):
    """JSON equality with exact types, keys, list lengths and ordering."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-prefix', required=True)
    args = parser.parse_args()
    prefix = args.evidence_prefix
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', prefix):
        parser.error('unsafe evidence prefix')
    bundle = prefix + '-bundle'
    names = [prefix] + [bundle + suffix for suffix in
                        ('', '-prestart', '-parity', '-parity-runtime', '-parity-final', '-final')]
    if any((HERE / 'evidence' / name).exists() for name in names):
        parser.error('Retained evidence exists; use a fresh prefix')
    out = HERE / 'evidence' / prefix
    out.mkdir(parents=True, exist_ok=False)
    result = {'startedAt': datetime.now(timezone.utc).isoformat(), 'validatorFindings': [],
              'scope': 'Doer mechanical Convert review; no task marking or human approval',
              'checks': [], 'commands': [], 'errors': [], 'passed': False}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', DOTNET_CLI_TELEMETRY_OPTOUT='1')

    def check(name, condition):
        result['checks'].append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise ValueError(name)

    def run(name, argv, expected=0):
        proc = subprocess.run(argv, cwd=ROOT, env=env, input='', capture_output=True, text=True)
        (out / (name + '.log')).write_text(proc.stdout + proc.stderr)
        result['commands'].append({'argv': argv, 'cwd': str(ROOT), 'exitCode': proc.returncode})
        check(name, proc.returncode == expected)
        return proc

    def load(name, file):
        return json.loads((HERE / 'evidence' / name / file).read_text())

    try:
        run('fresh-report', [sys.executable, str(HERE / 'produce-report.py'), '--evidence-prefix', bundle])
        report = load(bundle, 'report.json')
        check('report passes without errors', report['passed'] is True and not report['errors'])
        for kind, count in [('approval', 10), ('comparator', 11)]:
            tests = report['isolatedTests'][kind]
            check(kind + ' test counts', tests['passed'] == count and tests['failed'] == tests['skipped'] == 0)
        manifest = HERE / 'evidence' / bundle / 'artifact-identities.sha256'
        check('report binds artifact manifest', sha(manifest) == report['artifactManifestSha256'])
        entries = manifest.read_text().splitlines()
        check('artifact manifest nonempty', bool(entries))
        seen = set()
        for entry in entries:
            digest, name = entry.split('  ', 1)
            path = Path(name)
            if path.is_absolute() or '..' in path.parts or name in seen or sha(ROOT / path) != digest:
                raise ValueError('Invalid artifact identity: ' + name)
            seen.add(name)
        check('all artifact identities current', True)
        result['artifactCount'] = len(entries)
        for suffix in ('-prestart', '-parity', '-parity-runtime', '-parity-final', '-final'):
            gate = load(bundle + suffix, 'prerequisites.json')
            check('approval/input gate ' + suffix, gate['passed'] is True and not gate['errors'] and gate['identityCount'] > 0)
        before = HERE / 'evidence' / (bundle + '-prestart') / 'input-identities.sha256'
        after = HERE / 'evidence' / (bundle + '-final') / 'input-identities.sha256'
        check('immutable inputs unchanged', before.read_bytes() == after.read_bytes())
        result['inputIdentityCount'] = len(after.read_text().splitlines())
        build = load(bundle + '-parity', 'build.json')
        check('fresh nonincremental build', build['passed'] is True and build['exitCode'] == 0 and '--no-incremental' in build['command'])
        check('current binary identity', build['binarySha256'] == sha(HERE / 'src/bin/Release/net10.0/Converted.dll'))
        for name, digest in build['sourceSha256'].items():
            check('build source ' + name, sha(HERE / name) == digest)
        preservation = load('task-2-build', 'port-preservation.json')
        check('port preservation counts', preservation['passed'] == 3 and preservation['failed'] == preservation['skipped'] == 0)
        for item in preservation['checks']:
            check('preserved source ' + Path(item['target']).name,
                  item['identicalAfterDeclaredAdaptations'] is True and
                  sha(Path(item['source'])) == item['sourceSha256'] and sha(Path(item['target'])) == item['targetSha256'])
        parity = load(bundle + '-parity', 'parity.json')
        check('complete parity counts', parity['passed'] is True and not parity['errors'] and parity['counts'] ==
              {'required': 53, 'executed': 53, 'passed': 53, 'failed': 0, 'skipped': 0})
        cases = json.loads((PACKET / 'scenarios.json').read_text())['scenarios']
        reference = json.loads((PACKET / 'task-6-final-reference-observations.json').read_text())
        observations = load(bundle + '-parity', 'observations.json')
        check('exact scenario membership and order', len(cases) == 53 and
              [s['id'] for s in cases] == [s['id'] for s in reference] == [s['id'] for s in observations])
        for case, ref, obs in zip(cases, reference, observations):
            check('exact observation ' + case['id'], obs['passed'] is True and not obs['failures'] and
                  ref['passed'] is True and not ref['failures'] and
                  equal(case['expected'], obs['expected']) and equal(case['expected'], ref['expected']) and
                  equal(ref['observed'], obs['reference']) and equal(ref['observed'], obs['converted']))
        run('runtime-missing-gate-rejected', ['dotnet', str(HERE / 'src/bin/Release/net10.0/Converted.dll')], 2)
        # Snapshot *all* retained bundle files, including the non-self-hashed report.
        retained = {p: sha(p) for name in names[1:] for p in (HERE / 'evidence' / name).rglob('*') if p.is_file()}
        run('evidence-reuse-rejected', [sys.executable, str(HERE / 'produce-report.py'), '--evidence-prefix', bundle], 2)
        current = {p: sha(p) for name in names[1:] for p in (HERE / 'evidence' / name).rglob('*') if p.is_file()}
        check('reuse preserves every retained file', retained == current)
        result['retainedFileCount'] = len(retained)
        run('diff-check', ['git', 'diff', '--check', '--', str(HERE)])
        result['passed'] = True
    except Exception as error:
        result['errors'].append(repr(error))
    result.update(finishedAt=datetime.now(timezone.utc).isoformat(),
                  bundle=bundle, exitCode=0 if result['passed'] else 1)
    with (out / 'review.json').open('x') as stream:
        stream.write(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))
    return result['exitCode']


if __name__ == '__main__':
    sys.exit(main())
