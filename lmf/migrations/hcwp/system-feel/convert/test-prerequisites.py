#!/usr/bin/env python3
"""Isolated approval rejection tests; never mutate human-owned inputs."""
import importlib.util
import json
from pathlib import Path
import tempfile

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gate', HERE / 'check-prerequisites.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
checks = []
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    approval, manifest, review = [root / name for name in ('approval.md', 'manifest', 'review.md')]
    manifest.write_text('synthetic manifest\n')
    review.write_text('synthetic review\n')
    text = (f'- State: approved for progression to Convert\n- Reviewer: Human\n'
            f'- Approval date: 2026-10-14\n- Review revision: `{gate.digest(manifest)}`\n'
            f'- Review packet SHA-256: `{gate.digest(review)}`\n')

    def check(name, content, accepted=False):
        if approval.exists():
            approval.unlink()
        if content is not None:
            approval.write_text(content)
        try:
            gate.approval_gate(approval, manifest, review)
            actual = True
        except (OSError, ValueError):
            actual = False
        assert actual == accepted, name
        checks.append({'name': name, 'passed': True})

    check('current revision accepted', text, True)
    check('absent approval rejected', None)
    check('wrong state rejected', text.replace('approved for progression to Convert', 'pending'))
    check('missing state rejected', '\n'.join(text.splitlines()[1:]))
    check('duplicate state rejected', text + '- State: approved for progression to Convert\n')
    check('missing reviewer rejected', text.replace('- Reviewer: Human\n', ''))
    check('missing revision rejected', text.replace(f'- Review revision: `{gate.digest(manifest)}`\n', ''))
    check('unrelated digest cannot substitute revision', text.replace(gate.digest(manifest), '0' * 64) + f'Unrelated: `{gate.digest(manifest)}`\n')
    manifest.write_text('changed synthetic manifest\n')
    check('stale manifest rejected', text)
    manifest.write_text('synthetic manifest\n')
    review.write_text('changed synthetic review\n')
    check('stale review rejected', text)
print(json.dumps({'passed': len(checks), 'failed': 0, 'skipped': 0, 'checks': checks}))
