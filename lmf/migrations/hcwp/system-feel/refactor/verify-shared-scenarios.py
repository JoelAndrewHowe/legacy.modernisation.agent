#!/usr/bin/env python3
"""Shared approved SF inputs through current application boundaries; Refactor evidence only."""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
TARGET = HERE.parents[1]
PACKET = HERE.parent / 'characterise'
spec = importlib.util.spec_from_file_location('reference', PACKET / 'reference/run.py')
reference = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reference)


def summary_projection(observed):
    keys = ('Fullname', 'NhsNumber', 'DateOfBirth', 'ageDisplay', 'FullAddress', 'School',
            'Organisation', 'ShowAlert', 'ChildAlerts')
    result = {k: observed[k] for k in keys}
    result['sex'] = observed['genderRequest']['value']
    result['currentStatusCode'] = observed.get('statusRequest', {}).get('arguments', [''])[0]
    return result


def normalize_results(value, kd03=False):
    result = copy.deepcopy(value)
    if kd03:
        result['rows'] = [r for r in result['rows'] if r['ExaminationCode'] == 'KD03']
        result['count'] = len(result['rows'])
    for row in result['rows']:
        # Existing recording DTO uses zero for absent optional measurement key.
        if row.get('ChildMeasurementId') == 0:
            row['ChildMeasurementId'] = None
    # Canonicalize only within equal contact dates; still compare complete rows,
    # multiplicity and descending date groups. Raw runtime order remains retained.
    result['rows'].sort(key=lambda r: r['PkChildExaminationId'])
    result['rows'].sort(key=lambda r: r['ExaminationDate'], reverse=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', required=True)
    args = parser.parse_args()
    dest = Path(args.evidence_dir).resolve()
    if not dest.is_relative_to(HERE / 'evidence'):
        parser.error('Refactor evidence directory required')
    dest.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    commands = []

    def run(argv, name, inputs=None):
        p = subprocess.run(argv, cwd=TARGET, input=inputs, capture_output=True, text=True)
        commands.append(dict(argv=argv, cwd=str(TARGET), exitCode=p.returncode))
        (dest / name).write_text(p.stdout + p.stderr)
        if p.returncode:
            raise ValueError('Command failed: ' + name)
        return p.stdout

    fixtures = json.loads((PACKET / 'fixtures.json').read_text())
    cases = reference.validate_contract(fixtures, json.loads((PACKET / 'scenarios.json').read_text()))
    selected = [s for s in cases if s['operation'] in ('summary', 'results', 'name', 'address', 'age')]
    requests = [reference.resolve(s, fixtures) for s in selected]
    payload = ''.join(json.dumps(r) + '\n' for r in requests)
    (dest / 'requests.jsonl').write_text(payload)
    run(['dotnet', '--info'], 'dotnet-info.log')
    run(['dotnet', 'build', str(PACKET / 'reference/Reference.csproj'), '-c', 'Release'], 'reference-build.log')
    run(['dotnet', 'build', 'refactor/checks/Checks.csproj', '--no-incremental'], 'refactor-build.log')
    reference_output = run(['dotnet', str(PACKET / 'reference/bin/Release/net10.0/Reference.dll')], 'reference.jsonl', payload)
    refactor_output = run(['dotnet', 'run', '--project', 'refactor/checks', '--no-build', '--', '--system-feel-observe'], 'refactor.jsonl', payload)
    ref = [json.loads(line) for line in reference_output.splitlines()]
    current = [json.loads(line) for line in refactor_output.splitlines()]
    if len(ref) != len(selected) or len(current) != len(selected):
        raise ValueError('Missing/extra observations')
    converted_path = HERE / 'evidence/refactor-task-2-prestart/observations.json'
    converted = {s['id']: s for s in json.loads(converted_path.read_text())}
    observations = []
    for s, request, legacy, actual in zip(selected, requests, ref, current):
        port = converted[s['id']]['converted']
        failures = reference.compare_observation(s['expected'], legacy)
        failures += reference.compare_observation(s['expected'], port)
        if s['operation'] == 'summary':
            projected = [summary_projection(x) for x in (legacy, port)]
            normalized = actual
            # Apply the exact approved expectation on every field in this boundary.
            expected = {k: s['expected'][k] for k in projected[0] if k in s['expected']}
        elif s['operation'] != 'results':
            projected = [legacy, port]
            normalized = actual
            expected = s['expected']
            failures += reference.compare_observation(expected, actual)
        else:
            projected = [normalize_results(x, True) for x in (legacy, port)]
            normalized = normalize_results(actual)
            expected = copy.deepcopy(s['expected'])
            if request['inputs']['scope'] == 'all-KDP':
                # SF-037 characterises the broader source; application is KD03-only.
                kd03_ids = [r['PkChildExaminationId'] for r in request['inputs']['rows'] if r['ExaminationCode'] == 'KD03']
                expected = {'count': len([i for i in s['expected']['idsUnordered'] if i in kd03_ids]),
                            'idsUnordered': [i for i in s['expected']['idsUnordered'] if i in kd03_ids],
                            'excludedIds': s['expected']['excludedIds'] + [i for i in s['expected']['idsUnordered'] if i not in kd03_ids]} 
            failures += reference.compare_observation(expected, actual)
        failures += reference.compare(projected[0], normalized)
        failures += reference.compare(normalized, projected[0])
        failures += reference.compare(projected[1], normalized)
        if s['operation'] == 'summary':
            failures += reference.compare(expected, actual)
        observations.append(dict(id=s['id'], operation=s['operation'], inputs=request['inputs'],
            approvedExpected=s['expected'], boundaryExpected=expected, reference=legacy, converted=port,
            refactor=actual, projectedReference=projected[0], projectedConverted=projected[1],
            normalizedRefactor=normalized, passed=not failures, failures=failures))
    files = [PACKET / 'fixtures.json', PACKET / 'scenarios.json', converted_path,
             Path(__file__), TARGET / 'refactor/checks/SystemFeelObservations.cs']
    files += [p for p in (TARGET / 'refactor/src').rglob('*') if p.is_file() and p.suffix in ('.cs', '.csproj') and not {'bin', 'obj'} & set(p.parts)]
    report = dict(startedAt=started, finishedAt=datetime.now(timezone.utc).isoformat(), total=len(selected), passed=sum(x['passed'] for x in observations),
                  failed=sum(not x['passed'] for x in observations), skipped=0, commands=commands,
                  claim='Current application parity with extracted reference; not Windows/Oracle execution. Convert observations are the verified immutable prestart execution.',
                  coverage=[dict(id=s['id'], reason='Outside integrated summary/results boundaries; retained 53-scenario reference/Convert evidence only') for s in cases if s not in selected],
                  files={str(p.relative_to(TARGET)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    (dest / 'observations.json').write_text(json.dumps(observations, indent=2) + '\n')
    (dest / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))
    return 0 if report['total'] > 0 and report['failed'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
