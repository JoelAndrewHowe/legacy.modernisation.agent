#!/usr/bin/env python3
"""Verify Refactor prerequisites without treating the Refactor target as immutable.

Characterise approved the legacy evidence and captured the then-current target as
the starting point for Refactor.  Refactor is expected to change that target.
This gate therefore protects the approval, approved packet, legacy sources and
Convert baseline while allowing the application and assembly-line configuration
to evolve.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
TARGET = HERE.parents[1]
ROOT = TARGET.parents[2]
CHARACTERISE = HERE.parent / 'characterise'
APPROVAL = HERE.parent / 'approvals/characterise-approved.md'

MUTABLE_PREFIXES = (
    'lmf/migrations/hcwp/refactor',
    'lmf/migrations/hcwp/.assembly-lines',
)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def mutable(name):
    return any(name == prefix or name.startswith(prefix + '/') for prefix in MUTABLE_PREFIXES)


def manifest(path):
    entries = {}
    for line in path.read_text().splitlines():
        expected, name = line.split('  ', 1)
        relative = Path(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('Unsafe approved path: ' + name)
        entries[name] = expected
    return entries


def main():
    report = {
        'passed': False,
        'errors': [],
        'mutableBoundaries': list(MUTABLE_PREFIXES),
        'scope': 'Current immutable inputs and approval; Refactor target/configuration are authorized mutable boundaries',
    }
    try:
        convert_gate = load('convert_prerequisites', HERE.parent / 'convert/check-prerequisites.py')
        report.update(convert_gate.approval_gate(
            APPROVAL, CHARACTERISE / 'review-files.sha256', CHARACTERISE / 'review.md'))

        reviewed = manifest(CHARACTERISE / 'review-files.sha256')
        immutable_reviewed = {name: expected for name, expected in reviewed.items() if not mutable(name)}
        for name, expected in immutable_reviewed.items():
            path = ROOT / name
            if not path.is_file() or digest(path) != expected:
                raise ValueError('Approved immutable packet entry changed: ' + name)

        inventory = load('characterise_inventory', CHARACTERISE / 'inventory-inputs.py')
        saved = json.loads((CHARACTERISE / 'input-membership.json').read_text())
        current = inventory.enumerate_inputs()
        immutable_saved = {name: value for name, value in saved.items() if not mutable(name)}
        immutable_current = {name: value for name, value in current.items() if not mutable(name)}
        if immutable_saved != immutable_current:
            changed = sorted(set(immutable_saved) ^ set(immutable_current))
            changed += sorted(name for name in set(immutable_saved) & set(immutable_current)
                              if immutable_saved[name] != immutable_current[name])
            raise ValueError('Approved immutable input membership or bytes changed: ' + ', '.join(changed[:10]))

        report.update(
            immutableInventoryEntries=len(immutable_saved),
            immutableReviewEntries=len(immutable_reviewed),
            mutableInventoryEntries=len(saved) - len(immutable_saved),
            mutableReviewEntries=len(reviewed) - len(immutable_reviewed),
            passed=True,
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        report['errors'].append(str(error))
    print(json.dumps(report))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
