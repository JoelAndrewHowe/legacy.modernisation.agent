#!/usr/bin/env python3
"""Capture once, or read-only verify, the repository-root-relative review packet."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
MANIFEST = HERE / 'review-files.sha256'


def digest(path):
    with path.open('rb') as stream:
        h = hashlib.sha256()
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cache(path):
    return '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo', '.pyd')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', action='store_true')
    args = parser.parse_args()
    if Path.cwd() != ROOT:
        raise ValueError('Run from repository root')
    if args.capture and MANIFEST.exists():
        raise ValueError('Retained review manifest exists; never overwrite it')
    if digest(HERE / 'input-files.sha256') != '3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a':
        raise ValueError('Bound input manifest drift')
    # Default inventory verification is stdout-only; it checks original membership,
    # all input bytes and immutable baseline approval without rewriting evidence.
    gate = subprocess.run(['python3', str(HERE / 'inventory-inputs.py')], cwd=ROOT,
                          capture_output=True, text=True)
    if gate.returncode:
        raise ValueError('Input gate failed: ' + gate.stdout + gate.stderr)
    required = ['review.md', 'input-inventory.md', 'input-membership.json',
                'source-citations.json', 'verify-source-citations.py', 'task-2-evidence.json',
                'task-6-source-citation-results.json', 'task-6-source-citation-verification.log',
                'task-6-gate-results.json', 'task-6-final-reference-results.json',
                'task-6-final-reference-observations.json', 'task-6-selftests-harness-test-results.json']
    for name in required:
        if not (HERE / name).is_file():
            raise ValueError('Missing packet artifact: ' + name)
    citations = json.loads((HERE / 'task-6-source-citation-results.json').read_text())
    if not (citations['documentCount'] == 3 and citations['uniqueCitationCount'] > 0
            and citations['resolvedCount'] == citations['uniqueCitationCount']
            and not citations['failures'] and citations['exitCode'] == 0):
        raise ValueError('Task-6 citations not passing')
    reference = json.loads((HERE / 'task-6-final-reference-results.json').read_text())
    if reference['counts'] != dict(required=53, executed=53, passed=53, failed=0, skipped=0) or reference['exitCode'] != 0 or reference['errors']:
        raise ValueError('Task-6 reference not passing')
    tests = json.loads((HERE / 'task-6-selftests-harness-test-results.json').read_text())
    if tests['passed'] != 29 or tests['failed'] or tests['exitCode']:
        raise ValueError('Task-6 self-tests not passing')
    # Verify that fresh execution evidence actually binds the still-current runtime.
    for evidence in (reference, tests):
        for name, expected in evidence['files'].items():
            if digest(ROOT / name) != expected:
                raise ValueError('Execution source/contract drift: ' + name)
    inputs = {}
    excluded_inputs = []
    for line in (HERE / 'input-files.sha256').read_text().splitlines():
        expected, name = line.split('  ', 1)
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe input path: ' + name)
        if cache(relative):
            excluded_inputs.append(name)
        else:
            inputs[name] = expected
    paths = dict(inputs)
    slice_count = 0
    for path in sorted(HERE.rglob('*')):
        relative = path.relative_to(HERE)
        if cache(relative) or 'bin' in relative.parts or 'obj' in relative.parts or path == MANIFEST:
            continue
        if path.is_symlink():
            raise ValueError('Unexpected slice symlink: ' + str(relative))
        if path.is_file():
            paths[path.relative_to(ROOT).as_posix()] = digest(path)
            slice_count += 1
    if not ((HERE / 'verify').stat().st_mode & 0o111):
        raise ValueError('verify must remain executable')
    for name, expected in paths.items():
        if digest(ROOT / name) != expected:
            raise ValueError('Packet digest mismatch: ' + name)
    text = ''.join(f'{paths[name]}  {name}\n' for name in sorted(paths))
    if args.capture:
        # No replacement or rebaseline path; exclusive creation even after preflight.
        with MANIFEST.open('x') as stream:
            stream.write(text)
    elif MANIFEST.read_text() != text:
        raise ValueError('Packet membership or bytes changed; human revision is stale')
    print(json.dumps(dict(passed=True, mode='capture' if args.capture else 'read-only',
                          inputFiles=len(inputs), excludedInputCaches=len(excluded_inputs),
                          sliceFiles=slice_count, manifestEntries=len(paths),
                          reviewSha256=digest(HERE / 'review.md'),
                          manifestSha256=digest(MANIFEST), inputGate=json.loads(gate.stdout))))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
