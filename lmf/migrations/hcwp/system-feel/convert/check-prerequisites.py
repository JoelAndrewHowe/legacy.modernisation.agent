#!/usr/bin/env python3
"""Read-only approval/input gate. Evidence is exclusive-create; never rebaseline."""
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
PACKET = ROOT / 'lmf/migrations/hcwp/system-feel/characterise'
APPROVAL = ROOT / 'lmf/migrations/hcwp/system-feel/approvals/characterise-approved.md'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def approval_gate(approval, manifest, review):
    text = approval.read_text()
    for field, pattern in (
        ('State', r'approved for progression to Convert'),
        ('Reviewer', r'\S.*'),
        ('Approval date', r'\d{4}-\d{2}-\d{2}'),
        ('Review revision', r'`[a-f0-9]{64}`'),
        ('Review packet SHA-256', r'`[a-f0-9]{64}`'),
    ):
        values = re.findall(r'^- ' + re.escape(field) + r': (.*)$', text, re.M)
        if len(values) != 1 or not re.fullmatch(pattern, values[0]):
            raise ValueError('Absent or malformed approval field: ' + field)
        if field == 'Review revision' and values[0] != '`' + digest(manifest) + '`':
            raise ValueError('Stale approval: review manifest revision changed')
        if field == 'Review packet SHA-256' and values[0] != '`' + digest(review) + '`':
            raise ValueError('Stale approval: review document changed')
    return {'approvalSha256': digest(approval), 'reviewManifestSha256': digest(manifest),
            'reviewSha256': digest(review)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-prefix', required=True)
    args = parser.parse_args()
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', args.evidence_prefix):
        parser.error('unsafe evidence prefix')
    evidence = HERE / 'evidence' / args.evidence_prefix
    evidence.mkdir(parents=True, exist_ok=False)
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'passed': False,
              'errors': [], 'commands': [], 'validatorFindings': [],
              'scope': 'Prerequisites only; no conversion or parity execution'}
    try:
        report.update(approval_gate(APPROVAL, PACKET / 'review-files.sha256', PACKET / 'review.md'))
        # Approved helper reconciles all input membership/digests, baseline approval,
        # all review entries and passing current-source reference evidence. No capture.
        command = ['python3', str(PACKET / 'assemble-review.py')]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
        with (evidence / 'packet-verification.log').open('x') as stream:
            stream.write(result.stdout + result.stderr)
        report['commands'].append({'argv': command, 'cwd': str(ROOT),
                                   'exitCode': result.returncode, 'log': 'packet-verification.log'})
        if result.returncode:
            raise ValueError('Approved packet/input gate failed; see packet-verification.log')
        report['packetVerification'] = json.loads(result.stdout)
        # Record exact currently opened input bytes, including the approval and manifest.
        identities = {}
        for line in (PACKET / 'review-files.sha256').read_text().splitlines():
            expected, name = line.split('  ', 1)
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('Unsafe reviewed path: ' + name)
            identities[name] = digest(ROOT / path)
            if identities[name] != expected:
                raise ValueError('Reviewed input changed: ' + name)
        for path in (APPROVAL, PACKET / 'review-files.sha256'):
            identities[path.relative_to(ROOT).as_posix()] = digest(path)
        with (evidence / 'input-identities.sha256').open('x') as stream:
            stream.write(''.join(f'{h}  {p}\n' for p, h in sorted(identities.items())))
        # Reject approval drift during the check too.
        if approval_gate(APPROVAL, PACKET / 'review-files.sha256', PACKET / 'review.md') != {
            k: report[k] for k in ('approvalSha256', 'reviewManifestSha256', 'reviewSha256')
        }:
            raise ValueError('Approval changed during verification')
        report['identityCount'] = len(identities)
        report['passed'] = True
    except (OSError, ValueError, KeyError) as error:
        report['errors'].append(str(error))
    report['finishedAt'] = datetime.now(timezone.utc).isoformat()
    report['exitCode'] = 0 if report['passed'] else 1
    with (evidence / 'prerequisites.json').open('x') as stream:
        stream.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return report['exitCode']


if __name__ == '__main__':
    sys.exit(main())
