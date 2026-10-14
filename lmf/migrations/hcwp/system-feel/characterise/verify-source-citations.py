#!/usr/bin/env python3
"""Strict, read-only-input citation gate. Run from repository root."""
import argparse
import os
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
DOCS = ('behaviour.md', 'dependencies.md', 'gaps.md')
BUNDLES = {'example-code/patient-banner (pseudononymised).txt',
           'example-code/HCWP Core (pseudonymised) - single file.txt'}
BOUND = '3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence-prefix', help='Fresh evidence prefix for a later gate, e.g. task-6')
    args = parser.parse_args()
    if args.evidence_prefix and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', args.evidence_prefix):
        parser.error('invalid evidence prefix')
    prefix = args.evidence_prefix
    gate_name = (prefix or 'task-2-input')+'-gate-results.json'
    results_name = (prefix+'-' if prefix else '')+'source-citation-results.json'
    log_name = (prefix+'-' if prefix else '')+'source-citation-verification.log'
    gate_prefix = gate_name.removesuffix('-gate-results.json')+'-'
    destinations = [results_name, log_name, gate_name] + [gate_prefix+name for name in
        ('input-hash-check.log', 'baseline-revision-check.log', 'baseline-hash-check.log')]
    if any(os.path.lexists(OUT/name) for name in destinations):
        print('CITATION GATE BLOCKED: evidence destination already exists; use a fresh --evidence-prefix', file=sys.stderr)
        return 1
    command = 'python3 lmf/migrations/hcwp/system-feel/characterise/verify-source-citations.py'
    if prefix:
        command += ' --evidence-prefix '+prefix
    report = {'command': command,
              'cwd': str(Path.cwd()), 'startedAt': datetime.now(timezone.utc).isoformat(),
              'documentCount': len(DOCS), 'documents': {}, 'totalTokenCount': 0,
              'uniqueCitationCount': 0, 'resolvedCount': 0, 'failures': [], 'integrityCommands': []}
    def fail(id, message):
        report['failures'].append({'id': id, 'failure': message})
    try:
        if Path.cwd().resolve() != ROOT:
            raise ValueError('must run from repository root')
        if sha(OUT/'input-files.sha256') != BOUND:
            raise ValueError('bound input manifest revision mismatch')
        gate = subprocess.run([sys.executable, str(OUT/'inventory-inputs.py'), '--results', gate_name], cwd=ROOT, capture_output=True, text=True)
        report['integrityCommands'].append({'command': 'python3 lmf/migrations/hcwp/system-feel/characterise/inventory-inputs.py --results '+gate_name,
                                           'exitCode': gate.returncode, 'output': gate.stdout + gate.stderr})
        if gate.returncode:
            raise ValueError('input membership/digest/approval gate failed; citations not resolved')
        manifest = {}
        for line in (OUT/'input-files.sha256').read_text().splitlines():
            digest, path = line.split('  ', 1)
            manifest[path] = digest
        records = json.loads((OUT/'source-citations.json').read_text())
        if not isinstance(records, list) or not records:
            raise ValueError('absent/empty registry coverage')
        indexed = {}
        for record in records:
            if not isinstance(record, dict):
                fail(None, 'record must be an object'); continue
            id = record.get('id')
            if not isinstance(id, str) or not re.fullmatch(r'C[0-9]{3,}', id):
                fail(str(id), 'malformed ID'); continue
            if id in indexed:
                fail(id, 'duplicate ID'); continue
            indexed[id] = record
        report['uniqueCitationCount'] = len(indexed)
        uses = {}
        for doc in DOCS:
            text = (OUT/doc).read_text()
            tokens = re.findall(r'\[src:([^\]]*)\]', text)
            report['documents'][doc] = {'tokenCount': len(tokens), 'uniqueTokenCount': len(set(tokens))}
            report['totalTokenCount'] += len(tokens)
            if not text.strip() or not tokens:
                fail(None, 'absent/empty coverage: ' + doc)
            if text.count('[src:') != len(tokens):
                fail(None, 'unterminated source token: ' + doc)
            # Bundle coordinates/URLs and ad-hoc source markers may not substitute for structured tokens.
            if re.search(r'(?:example-code/[^\n`]*\.txt(?:[:#]|\s+lines?\s+)|\[(?:source|src)(?!:)[^\]]*\]|\b(?:patient-banner|HCWP Core)[^\n]*\bL\d+|\.(?:cs|cshtml|txt)(?::\d+|#L\d+)|\bsrc:\s*C\d+\b(?!\]))', text, re.I):
                fail(None, 'unstructured source reference: ' + doc)
            for id in tokens:
                if not re.fullmatch(r'C[0-9]{3,}', id):
                    fail(id, 'malformed token in ' + doc)
                uses.setdefault(id, set()).add(doc)
                if id not in indexed:
                    fail(id, 'missing record: ' + doc)
                elif indexed[id].get('document') != doc:
                    fail(id, 'wrong document binding: ' + doc)
        for id, record in indexed.items():
            before = len(report['failures'])
            if id not in uses:
                fail(id, 'unused record')
            if record.get('document') not in DOCS:
                fail(id, 'invalid document')
            path = record.get('path')
            if path not in BUNDLES:
                fail(id, 'not an original bundle'); continue
            file = ROOT/path
            if not file.is_file():
                fail(id, 'file missing'); continue
            declared = record.get('sha256')
            if declared != manifest.get(path) or sha(file) != declared:
                fail(id, 'declared/manifest/current digest mismatch'); continue
            # splitlines preserves physical line coordinates for LF and CRLF bundles.
            lines = file.read_text().splitlines()
            start, end = record.get('start_line'), record.get('end_line')
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines):
                fail(id, 'invalid line span'); continue
            span = '\n'.join(lines[start-1:end])
            for key in ('symbol', 'fragment'):
                value = record.get(key)
                if not isinstance(value, str) or not value.strip() or value not in span:
                    fail(id, key + ' is empty or absent from exact span')
            if len(report['failures']) == before:
                report['resolvedCount'] += 1
        if not indexed or not report['resolvedCount']:
            fail(None, 'positive citation/resolution count required')
    except Exception as error:
        fail(None, str(error))
    report['finishedAt'] = datetime.now(timezone.utc).isoformat()
    report['exitCode'] = 1 if report['failures'] else 0
    for name in (results_name, log_name):
        with (OUT/name).open('x') as evidence:
            evidence.write(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))
    return report['exitCode']

if __name__ == '__main__':
    sys.exit(main())
