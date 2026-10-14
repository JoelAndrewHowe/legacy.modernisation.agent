#!/usr/bin/env python3
"""Read-only input gate; --capture creates a snapshot, default only verifies it.
Run from the repository root. Never builds or regenerates baseline evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
OUT = ROOT / 'lmf/migrations/hcwp/system-feel/characterise'
BASE = 'lmf/migrations/hcwp/'
GROUPS = [
    (1, ['lmf/docs/vision.md'], 'Immutable factory vision; trace all future stages to its principles.'),
    (2, ['lmf/iterations/002-implement-system-feel.md'], 'Current contract; Characterise only, then human approval.'),
    (3, ['lmf/iterations/001-characterise-and-migrate-hcwp.md'], 'Immutable bounded KD03 baseline contract.'),
    (4, ['example-code/patient-banner (pseudononymised).txt'], 'Input-only patient retrieval, mappings, resolvers and banner source.'),
    (5, ['example-code/HCWP Core (pseudonymised) - single file.txt'], 'Input-only KD03 legacy bundle; original file identities, not a buildable system.'),
    (6, [BASE+'characterise', BASE+'approvals/characterise-approved.md'], 'Immutable approved packet, 40 scenarios, extracted reference and revision-bound human approval.'),
    (7, [BASE+'refactor/src', BASE+'refactor/checks', BASE+'refactor/browser', BASE+'refactor/limitations-and-completion.md'], 'Existing target, regression and browser boundaries; do not modify or execute evidence-writing baseline runners.'),
    (8, ['lmf/seeds/context/nhsw-component-library.md'], 'Target-design guidance, NOT legacy behavioural evidence; does not authorise asset upgrades.'),
    (9, [BASE+'refactor/nhsw-provenance.md'], 'Existing pinned design assets/provenance; preserve current pin.'),
]
SUPPLEMENT = [BASE+'.assembly-lines', BASE+'convert', BASE+'refactor']
# Exact linked evidence named by the baseline completion, verification and parity reports.
LINKED = [BASE+p for p in [
    'refactor/parity-report.md', 'refactor/verification.md', 'refactor/full-flow.md',
    'refactor/evidence/gate-results.json', 'refactor/evidence/completion-assessment.json',
    'refactor/evidence/gate-prerequisites-before.log', 'refactor/evidence/gate-prerequisites-after.log',
    'refactor/evidence/full-flow-build.log', 'refactor/evidence/gate-style.log',
    'refactor/evidence/full-flow-model.json', 'refactor/evidence/full-flow-persistence.json',
    'refactor/evidence/full-flow-browser/results.json', 'refactor/evidence/parity/comparison.json',
    'refactor/evidence/parity/reference/results.json', 'refactor/evidence/parity/conversion/results.json',
    'refactor/evidence/parity/refactor/results.json', 'refactor/evidence/nhsw-browser/results.json',
    'convert/parity-report.md', 'convert/baseline-confirmation.md', 'convert/source-provenance.json',
    'convert/evidence/scenario-comparison.json', 'convert/evidence/results.json',
    'convert/evidence/reference-results.json', 'characterise/reference/evidence/results.json',
]]

def now():
    return datetime.now(timezone.utc).isoformat()

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1048576), b''):
            h.update(block)
    return h.hexdigest()

def enumerate_inputs():
    entries = {}
    def visit(path, ancestors=()):
        rel = path.relative_to(ROOT).as_posix()
        resolved = path.resolve(strict=True)
        entry = {}
        if path.is_symlink():
            entry = {'symlinkTarget': os.readlink(path), 'resolved': str(resolved)}
        if path.is_dir():
            if resolved in ancestors:
                raise ValueError('directory symlink cycle: '+rel)
            entries[rel] = dict(entry, kind='directory')
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                visit(child, ancestors+(resolved,))
        elif path.is_file():
            entries[rel] = dict(entry, kind='file', sha256=digest(path))
        else:
            raise ValueError('unreadable or unsupported input: '+rel)
    for rel in sorted(set(SUPPLEMENT + [p for _, paths, _ in GROUPS for p in paths])):
        visit(ROOT/rel)
    for rel in LINKED:
        if rel not in entries or entries[rel]['kind'] != 'file':
            raise ValueError('missing linked required evidence: '+rel)
    return dict(sorted(entries.items()))

def run(command, cwd, name, retain=False):
    started = now()
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    output = result.stdout+result.stderr
    if retain:
        with (OUT/name).open('x') as log:
            log.write(output)
    return {'command': ' '.join(command), 'cwd': str(cwd), 'startedAt': started,
            'finishedAt': now(), 'exitCode': result.returncode,
            'output': name if retain else output}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--results', help='Separate recheck JSON filename; default writes nothing')
    args = parser.parse_args()
    if args.results and (args.capture or Path(args.results).name != args.results
                         or not args.results.endswith('-gate-results.json')
                         or args.results == 'input-gate-results.json'):
        parser.error('--results must be a separate *-gate-results.json filename, without --capture')
    retain = args.capture or bool(args.results)
    prefix = args.results.removesuffix('-gate-results.json')+'-' if args.results else ''
    if Path.cwd().resolve() != ROOT:
        raise ValueError('run from repository root: '+str(ROOT))
    # Preflight every destination before any evidence is written, including orphan logs.
    destinations = []
    if retain:
        destinations = [OUT/(args.results or 'input-gate-results.json')] + [
            OUT/(prefix+name) for name in ('input-hash-check.log',
                                         'baseline-revision-check.log', 'baseline-hash-check.log')]
    if args.capture:
        destinations += [OUT/name for name in ('input-membership.json', 'input-files.sha256', 'input-inventory.md')]
    existing = [str(path) for path in destinations if os.path.lexists(path)]
    if existing:
        raise ValueError('refusing to overwrite retained evidence: '+', '.join(existing))
    report = {'startedAt': now(), 'seedGroups': 9, 'errors': [], 'commands': []}
    entries = enumerate_inputs()
    files = {p: e['sha256'] for p, e in entries.items() if e['kind'] == 'file'}
    report.update(files=len(files), directories=sum(e['kind']=='directory' for e in entries.values()),
                  symlinks=sum('symlinkTarget' in e for e in entries.values()))
    membership = OUT/'input-membership.json'
    manifest = OUT/'input-files.sha256'
    if args.capture:
        if membership.exists() or manifest.exists():
            raise ValueError('refusing to replace an existing input baseline; verify it instead')
        membership.write_text(json.dumps(entries, indent=2)+'\n')
        manifest.write_text(''.join(f'{h}  {p}\n' for p,h in files.items()))
    saved = json.loads(membership.read_text())
    membership_only = lambda d: {p: {k:v for k,v in e.items() if k != 'sha256'} for p,e in d.items()}
    report['membershipMatches'] = membership_only(saved) == membership_only(entries)
    report['allDigestsMatchSnapshot'] = saved == entries
    expected_manifest = ''.join(f"{e['sha256']}  {p}\n" for p,e in saved.items() if e['kind']=='file')
    report['manifestReconcilesExactly'] = manifest.read_text() == expected_manifest
    # Independent second enumeration after capture, including hidden/untracked/build files.
    report['secondEnumerationMatches'] = enumerate_inputs() == entries
    report['commands'].append(run(['sha256sum', '--check', manifest.relative_to(ROOT).as_posix()], ROOT, prefix+'input-hash-check.log', retain))
    packet = ROOT/(BASE+'characterise/review-files.sha256')
    approval = (ROOT/(BASE+'approvals/characterise-approved.md')).read_text()
    bound = re.search(r'Review revision: `([a-f0-9]{64})`', approval)
    report['approvalRevision'] = bound.group(1) if bound else None
    report['actualReviewManifestSha256'] = digest(packet)
    report['approvalRevisionMatches'] = bool(bound and bound.group(1) == digest(packet) and 'State: approved for progression to Convert' in approval)
    report['commands'].append(run(['sha256sum', 'characterise/review-files.sha256'], ROOT/BASE, prefix+'baseline-revision-check.log', retain))
    report['commands'].append(run(['sha256sum', '--check', 'characterise/review-files.sha256'], ROOT/BASE, prefix+'baseline-hash-check.log', retain))
    for key in ['membershipMatches', 'allDigestsMatchSnapshot', 'manifestReconcilesExactly', 'secondEnumerationMatches', 'approvalRevisionMatches']:
        if not report[key]:
            report['errors'].append(key+' failed')
    for command in report['commands']:
        if command['exitCode'] != 0:
            report['errors'].append(command['command']+' failed; see '+command['output'])
    report['finishedAt'] = now()
    report['passed'] = not report['errors']
    if retain:
        with (OUT/(args.results or 'input-gate-results.json')).open('x') as evidence:
            evidence.write(json.dumps(report, indent=2)+'\n')
    if args.capture:
        lines = ['# Iteration-002 verified input inventory', '',
                 'Task 1 only. No plan checkbox, approval, baseline artifact or product code changed.',
                 'No validator findings were supplied after the findings heading.', '',
                 '## Inspection scope and constraints', '',
                 'All file bytes were opened and individually hashed; all directory members (including hidden, ignored, untracked, binaries, node_modules, bin/obj and caches) are included without exclusions. This is an input identity/availability inspection, not a claim of exhaustive semantic review of every dependency file. Behaviour extraction and scenario execution remain downstream tasks.',
                 'Read the vision, both seeds, baseline approval/review, source patient-service/resolver/model sections, KD03 GetKdpResults, target application boundary, test driver/browser flow, design context/provenance, Convert parity and Refactor parity/verification/completion reports. The entire Characterise/Convert/Refactor trees supplement these inspected entry points.',
                 'Existing user modifications and untracked inputs were observed with `git status --short` from repository root and preserved. Configuration is a working-tree input, not assumed to match HEAD.', '',
                 '## Nine-of-nine reconciliation', '']
        for n, paths, role in GROUPS:
            lines += [f'### {n}. {role}']
            for p in paths:
                e = entries[p]
                if e['kind']=='file':
                    lines += [f'- `{p}` — SHA-256 `{e["sha256"]}`.']
                else:
                    count = sum(k.startswith(p+'/') and v['kind']=='file' for k,v in entries.items())
                    lines += [f'- `{p}/` — {count} recursively enumerated files; every individual path/hash is in `input-files.sha256`, full directory membership in `input-membership.json`.']
            lines += ['']
        lines += ['## Supplemental inputs', '']
        for p in SUPPLEMENT:
            count = sum(k.startswith(p+'/') and v['kind']=='file' for k,v in entries.items())
            lines += [f'- `{p}/`: {count} files, individually bound. Overlapping group-7 paths are deduplicated, not omitted.']
        lines += ['', '### Exact linked baseline evidence paths', '']+[f'- `{p}`' for p in LINKED]
        lines += ['', 'All remaining report, log, screenshot, HTML, script, configuration and disposable-tree members are also listed individually in the manifest; no directory hash substitutes for them.', '',
                  '## Symlink handling', '',
                  'Enumeration uses sorted `Path.iterdir()` recursively, resolves each entry strictly, opens each regular file in binary mode and streams SHA-256. It follows directory links with cycle detection and hashes file links through their targets. Unresolved, unreadable or unsupported entries fail. Directory membership and link targets/resolution are retained in `input-membership.json`.']
        lines += [f'- `{p}` → `{e["symlinkTarget"]}`; resolves to `{e["resolved"]}`; bytes hashed under the input path.' for p,e in entries.items() if 'symlinkTarget' in e]
        lines += ['', '## Unavailable dependencies and limitations', '',
                  '- The original Windows/Oracle/EF6 application, runtime UI/event delivery, service infrastructure and original resource prose are not available as a runnable baseline. The supplied bundles remain mandatory inputs, not omitted dependencies.',
                  '- Patient summary needs repository/unit-of-work, AutoMapper/resolvers, lookups, resource formatting, clock, access-control and related location/alert data. Exact extraction adaptations and doubles require downstream documentation; no rule is inferred from the modern UI.',
                  '- Existing target uses temporary EF Core InMemory; no Oracle, PostgreSQL, production or full-system parity claim. This task does not rerun build/browser suites or alter their retained evidence.',
                  '- NHSW context guidance pin `5322c16910fbad0335b504ce80a1d8a50fe3b683` differs intentionally from current asset provenance pin `043d882318918e2a4e8847e16fc3bfe694973c08`; guidance explicitly forbids silent asset replacement. Remote upstream/network availability was not verified and is not required for this local input gate.',
                  '- Synthetic fixtures and resource-identity fallbacks remain baseline limitations. Future Welsh copy and Organisation/Health board decisions are not resolved by the inventory.', '',
                  '## Exact enumeration/hash and gate commands', '',
                  f'Working directory for capture and recheck: `{ROOT}`.',
                  '```sh',
                  'python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py --capture',
                  'python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py',
                  'sha256sum --check lmf/migrations/hcwp/system-feel/characterise/input-files.sha256',
                  '# Independent approval checks, working directory lmf/migrations/hcwp:',
                  'sha256sum characterise/review-files.sha256',
                  'sha256sum --check characterise/review-files.sha256', '```',
                  'The script is the exact enumeration/hash implementation (Python hashlib.sha256 on binary streams). Default mode never refreshes manifests. Reconciliation compares the full file set and directories, link metadata, every digest and exact manifest text; re-enumeration must also match. It checks approval state/revision independently before checking bound baseline bytes. No baseline verifier that rewrites evidence is invoked.', '',
                  '### Executed initial gate', '',
                  f'Start: `{report["startedAt"]}`; finish: `{report["finishedAt"]}`.',
                  f'Counts: 9/9 seed groups; {report["files"]} unique file entries; {report["directories"]} directory entries; {report["symlinks"]} symlinks. No missing or extra manifest paths. All required and supplemental paths readable.',
                  f'Membership, recomputed digests, exact manifest reconciliation, second enumeration and approval revision comparison: {"PASS" if report["passed"] else "FAIL"}.',
                  f'Approval recorded and calculated revision: `{report["actualReviewManifestSha256"]}` (matches: {report["approvalRevisionMatches"]}).']
        for c in report['commands']:
            lines += [f'- `{c["command"]}`, cwd `{c["cwd"]}`, {c["startedAt"]}–{c["finishedAt"]}, exit {c["exitCode"]}; full output `{c["output"]}`.']
        lines += ['', 'Task-1 results/timestamps/exit codes are retained in `input-gate-results.json` and the three logs. Default rechecks write only stdout; use `--results task-2-input-gate-results.json` for separately retained recheck evidence/logs. Recheck before downstream work and again before review binding. Any missing path, changed membership, unreadable input, digest or approval mismatch blocks progression; record it in gaps.md and the run plan, without refreshing iteration-001 evidence.', '']
        (OUT/'input-inventory.md').write_text('\n'.join(lines))
    print(json.dumps(report))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except Exception as error:
        print('INPUT GATE BLOCKED: '+str(error), file=sys.stderr)
        sys.exit(1)
