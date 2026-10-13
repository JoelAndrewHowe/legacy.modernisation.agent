#!/usr/bin/env python3
"""Inspect retained upstream evidence; never rebuild or modify approved inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parent.parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda name: json.loads((root / name).read_text())
revision = sha(root / 'characterise/review-files.sha256')
approval = (root / 'approvals/characterise-approved.md').read_text()
assert 'State: approved for progression to Convert' in approval
assert f'`{revision}`' in approval, 'Missing or stale human approval'
subprocess.run(['sha256sum', '--check', 'characterise/review-files.sha256'],
               cwd=root, check=True, capture_output=True)
inventory_count = len((root / 'characterise/review-files.sha256').read_text().splitlines())
pinned = {
    '../../docs/vision.md': 'a5280da556de24f8d6d9254df5b1bdd22ace59c7fc0a5ac64b9485dd71483444',
    '../../iterations/001-characterise-and-migrate-hcwp.md': '73c53da335f85625dd0ce180d69eec64a21431f9ab8247a58520e0dfbd3addcd',
    '../../../example-code/HCWP Core (pseudonymised) - single file.txt': 'f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2',
}
for name, expected in pinned.items():
    assert sha(root / name) == expected, f'Changed approved input: {name}'
audit = subprocess.run(['python3', str(root / 'convert/audit-port')],
                       check=True, capture_output=True, text=True)
ids = [s['id'] for s in load('characterise/scenarios.json')['scenarios']]
assert len(ids) == 40 and len(set(ids)) == 40
assert all(s['required'] for s in load('characterise/scenarios.json')['scenarios'])
report_names = ['characterise/reference/evidence/results.json',
                'convert/evidence/reference-results.json', 'convert/evidence/results.json']
reports = [load(name) for name in report_names]
for report in reports:
    assert report['mode'] == 'verify' and report['selectedScenario'] is None
    assert [report[k] for k in ('total', 'passed', 'failed', 'skipped')] == [40, 40, 0, 0]
    assert [r['id'] for r in report['results']] == ids
    assert report['sourceSha256'] == pinned['../../../example-code/HCWP Core (pseudonymised) - single file.txt']
    for key, name in [('fixtureSha256', 'fixtures.json'), ('scenarioSha256', 'scenarios.json')]:
        assert report[key] == sha(root / 'characterise' / name)
    for result in report['results']:
        assert result['status'] == 'passed' and result['observations'] and not result['differences']
comparison = load('convert/evidence/scenario-comparison.json')
identity = comparison['identity']
assert identity['approvedRevision'] == revision
assert identity['approvedResultsSha256'] == sha(root / report_names[0])
for name, digest in identity['evidenceSha256'].items():
    assert sha(root / 'convert/evidence' / name) == digest, f'Changed evidence: {name}'
for name, digest in identity['referenceCopiedFiles'].items():
    assert sha(root / 'characterise/reference' / name) == digest
assert [s['id'] for s in comparison['scenarios']] == ids
for row, baseline, reference, converted in zip(comparison['scenarios'], *(r['results'] for r in reports)):
    assert baseline['observations'] == reference['observations'] == converted['observations'], row['id']
    assert row == dict(id=row['id'], reference='passed', conversion='passed',
                       exactObservationMatch=True, approvedBaselineMatch=True)
summary = comparison['summary']
assert [summary[k] for k in ('total', 'passed', 'failed', 'skipped', 'exactObservationMatches')] == [40, 40, 0, 0, 40]
assert summary['omitted'] == []
v01 = [f'KD03-{n:03}' for n in (*range(4, 12), 14, 15, 32)]
assert summary['v01Checked'] == v01
for report in reports:
    for result in report['results']:
        if result['id'] in v01:
            o = result['observations']
            assert o['validatorPrompt'] == 'ValidationErrorsPrompt'
            assert o['savePrompt'] == 'ExamResultsErrorSavingPrompt'
            assert o['parentNotification'] == dict(type='NonFatalErrorEncountered', kind='Error',
                title='KdpResultsTitle', prompt='ExamResultsErrorSavingPrompt')
            assert not o['saved'] and o['storeUnchanged']
for name, report in zip(['reference-full-suite.jsonl', 'full-suite.jsonl'], reports[1:]):
    lines = [json.loads(line) for line in (root / 'convert/evidence' / name).read_text().splitlines()]
    assert lines[:-1] == report['results'], f'Incomplete stdout: {name}'
    assert lines[-1] == dict(total=40, passed=40, failed=0, skipped=0)
for name in ('build.log', 'reference-build.log'):
    log = (root / 'convert/evidence' / name).read_text()
    assert 'Build succeeded.' in log and '0 Warning(s)' in log and '0 Error(s)' in log
hash_names = report_names + ['approvals/characterise-approved.md', 'convert/source-provenance.json',
    'convert/evidence/scenario-comparison.json', 'convert/run-approved-scenarios', 'convert/verify',
    'convert/audit-port', 'characterise/fixtures.json', 'characterise/scenarios.json']
print(json.dumps(dict(approvalCurrent=True, approvedRevision=revision,
    reviewedFilesMatched=inventory_count, conversionProvenance=json.loads(audit.stdout),
    retainedScenarioCount=40, exactObservationMatches=40, failed=0, skipped=0,
    v01Checked=v01, freshScenarioExecutions=0, newValidatorFindings=[],
    sha256={name: sha(root / name) for name in hash_names} | pinned), indent=2))
