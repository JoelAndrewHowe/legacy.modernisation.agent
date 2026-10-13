#!/usr/bin/env python3
"""Compare refactor execution with retained approved evidence, not a three-way run."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent
load = lambda p: json.loads((root / p).read_text())
sha = lambda p: hashlib.sha256((root / p).read_bytes()).hexdigest()
names = ['characterise/reference/evidence/results.json',
         'convert/evidence/results.json', 'refactor/evidence/results.json']
reports = [load(p) for p in names]
ids = [s['id'] for s in load('characterise/scenarios.json')['scenarios']]
rows = []
for report in reports:
    assert [report[k] for k in ('total', 'passed', 'failed', 'skipped')] == [40, 40, 0, 0]
    assert report['mode'] == 'verify' and report['selectedScenario'] is None
    assert [r['id'] for r in report['results']] == ids
    assert report['scenarioSha256'] == sha('characterise/scenarios.json')
    assert report['fixtureSha256'] == sha('characterise/fixtures.json')
for baseline, conversion, refactor in zip(*(r['results'] for r in reports)):
    assert refactor['status'] == 'passed' and refactor['observations'] and not refactor['differences']
    assert baseline['observations'] == conversion['observations'] == refactor['observations'], refactor['id']
    rows.append(dict(id=refactor['id'], exactRetainedObservationMatch=True))
persistence = load('refactor/evidence/persistence.json')
assert [persistence[k] for k in ('total', 'passed', 'failed', 'skipped')] == [4, 4, 0, 0]
assert sha('refactor/src/demo-fixtures.json') == sha('characterise/fixtures.json')
summary = dict(total=40, passed=40, failed=0, skipped=0, exactRetainedObservationMatches=40,
               freshUpstreamExecutions=0, persistenceChecks=4, browserVerified=False,
               newValidatorFindings=[])
output = dict(summary=summary, scenarios=rows, sha256={p: sha(p) for p in names},
              implementationSha256={str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for base in ('refactor/src', 'refactor/checks')
                  for p in sorted((root / base).rglob('*'))
                  if p.is_file() and not {'bin', 'obj'}.intersection(p.relative_to(root / base).parts)})
(root / 'refactor/evidence/architecture-comparison.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(summary))
