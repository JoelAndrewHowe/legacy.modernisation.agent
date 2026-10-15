#!/usr/bin/env python3
"""Negative aggregate-evidence contracts: no empty/failed/skipped success."""
import importlib.machinery
import importlib.util
import json
from pathlib import Path

loader = importlib.machinery.SourceFileLoader('slice_gate', str(Path(__file__).with_name('verify')))
spec = importlib.util.spec_from_loader(loader.name, loader)
gate = importlib.util.module_from_spec(spec)
loader.exec_module(gate)
good = dict(total=2, passed=2, failed=0, skipped=0)
checks = []
for name, value in [
    ('empty', dict(total=0, passed=0, failed=0, skipped=0)),
    ('failed', dict(good, failed=1)),
    ('skipped', dict(good, skipped=1)),
    ('incomplete', dict(good, passed=1)),
    ('missing', {}),
    ('boolean-count', dict(good, total=True)),
    ('runtime-error', dict(good, errors=['runtime unavailable'])),
]:
    try:
        gate.require_counts(value)
    except ValueError:
        checks.append(dict(name=name, status='passed'))
    else:
        raise AssertionError('Accepted invalid evidence: ' + name)
gate.require_counts(good)
checks.append(dict(name='positive', status='passed'))
legacy_good = dict(failed=0, skipped=0, checks=[
    dict(name='style', status='passed'),
    dict(name='regression', passed=40, failed=0, skipped=0),
])
for name, value in [
    ('empty-legacy', dict(legacy_good, checks=[])),
    ('legacy-hidden-failure', dict(legacy_good, checks=[dict(name='style', status='failed')])),
    ('legacy-hidden-skip', dict(legacy_good, checks=[dict(name='style', status='skipped')])),
    ('legacy-empty-suite', dict(legacy_good, checks=[dict(name='suite', passed=0, failed=0, skipped=0)])),
    ('legacy-failed-suite', dict(legacy_good, checks=[dict(name='suite', passed=1, failed=1, skipped=0)])),
    ('legacy-skipped-suite', dict(legacy_good, checks=[dict(name='suite', passed=1, failed=0, skipped=1)])),
    ('legacy-runtime-error', dict(legacy_good, runtimeErrors=['browser unavailable'])),
    ('legacy-boolean-count', dict(legacy_good, failed=False)),
    ('legacy-malformed-check', dict(legacy_good, checks=[{}])),
    ('legacy-nested-error', dict(legacy_good, checks=[dict(name='style', status='passed', errors=['error'])])),
]:
    try:
        gate.require_legacy_checks(value)
    except ValueError:
        checks.append(dict(name=name, status='passed'))
    else:
        raise AssertionError('Accepted invalid legacy evidence: ' + name)
gate.require_legacy_checks(legacy_good)
checks.append(dict(name='legacy-positive', status='passed'))
print(json.dumps(dict(total=len(checks), passed=len(checks), failed=0, skipped=0, checks=checks)))
