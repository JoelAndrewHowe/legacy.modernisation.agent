#!/usr/bin/env python3
"""Execute required scenarios, independently observe, then compare. No expected data enters runtime."""
import argparse
import collections
import copy
import datetime
import hashlib
import itertools
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SLICE = HERE.parent
ROOT = HERE.parents[5]
OPS = {'summary','name','address','span-text','age','alert-setup','results','ordering-contract','physical-values','facets'}

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def compare(expected, observed, location='$'):
    """Strict recursive subset. bool is not int; list lengths/order are exact."""
    if isinstance(expected, dict):
        if not isinstance(observed, dict):
            return [location + ': expected object']
        failures = []
        for key, value in expected.items():
            if key not in observed:
                failures.append(location + '.' + key + ': missing')
            else:
                failures += compare(value, observed[key], location + '.' + key)
        return failures
    if isinstance(expected, list):
        if not isinstance(observed, list) or len(expected) != len(observed):
            return [location + ': list type/cardinality mismatch']
        return [error for n, (a,b) in enumerate(zip(expected,observed)) for error in compare(a,b,f'{location}[{n}]')]
    if type(expected) is not type(observed) or expected != observed:
        return [f'{location}: expected {expected!r}, observed {observed!r}']
    return []

def compare_observation(expected, observed):
    # Unordered comparisons consume EVERY observed row; no subset-only membership pass.
    expected = copy.deepcopy(expected)
    failures = []
    if any(k in expected for k in ('idsUnordered','excludedIds','orderedDateGroups')):
        rows = observed.get('rows', [])
        ids = [r['PkChildExaminationId'] for r in rows]
        if observed.get('count') != len(rows):
            failures.append('count differs from complete observed row count')
        if 'idsUnordered' in expected and collections.Counter(expected.pop('idsUnordered')) != collections.Counter(ids):
            failures.append('complete ID multiset mismatch')
        if any(i in ids for i in expected.pop('excludedIds', [])):
            failures.append('excluded ID leaked')
        if 'orderedDateGroups' in expected:
            groups = [{'date': date, 'idsUnordered': sorted(r['PkChildExaminationId'] for r in group)}
                      for date, group in itertools.groupby(rows, key=lambda r:r['ExaminationDate'])]
            target = expected.pop('orderedDateGroups')
            target = [{'date':g['date'], 'idsUnordered':sorted(g['idsUnordered'])} for g in target]
            failures += compare(target, groups, '$.orderedDateGroups')
    return failures + compare(expected, observed)

def validate_contract(fixtures, contract):
    if fixtures['schemaVersion'] != 1 or contract['schemaVersion'] != 1:
        raise ValueError('Unsupported contract schema')
    cases = contract['scenarios']
    if not cases or len(cases) != 53 or {x['id'] for x in cases} != {f'SF-{i:03}' for i in range(1,54)}:
        raise ValueError('Missing/duplicate/extra required scenario definitions')
    groups = {f'G{i:02}' for i in range(1,11)}
    if set(contract['groups']) != groups or {g for x in cases for g in x['groups']} != groups:
        raise ValueError('Missing/unknown scenario group')
    for x in cases:
        if x['required'] is not True or x['operation'] not in OPS or not x['expected'] or not x['groups']:
            raise ValueError('Unknown/empty/non-required scenario ' + x['id'])
    return cases

def resolve(scenario, f):
    i = copy.deepcopy(scenario['inputs'])
    op = scenario['operation']
    if op == 'summary':
        p = copy.deepcopy(f['patients'][i['patient']])
        p.update(copy.deepcopy(i['patientOverrides']))
        repo = [p if key == i['patient'] else copy.deepcopy(f['patients'][key]) for key in i['repositoryPatients']]
        if len({x['ClientId'] for x in repo}) != len(repo):
            raise ValueError('Duplicate patient repository membership')
        i = {'ClientId':p['ClientId'], 'repositoryPatients':repo, 'clock':i['clock'],
             'authorityLocations':copy.deepcopy(i['authorityLocationsOverride'] if 'authorityLocationsOverride' in i else f[i['authorityLocations']])}
    elif op == 'alert-setup':
        i['patient'] = copy.deepcopy(f['patients'][i['patient']])
    elif op == 'results':
        i['rows'] = copy.deepcopy(f['histories'][i.pop('history')])
        if i.pop('reverseInput',False):
            i['rows'].reverse()
    return {'operation':op, 'inputs':i}

def ordering_observation():
    # Inspect the COMPLETE extracted original method, not fixture expected keys.
    text = (HERE/'original/C022.txt').read_text()
    if len(re.findall(r'\bGetKdpResults\s*\(', text)) != 1 or text.count('{') != text.count('}'):
        raise ValueError('Incomplete ordering method')
    matches = re.findall(r'\.(OrderByDescending|OrderBy|ThenByDescending|ThenBy)\(it => it\.(\w+)\)', text)
    if not matches:
        raise ValueError('No inspectable ordering keys')
    keys = [{'field':field,'direction':'descending' if name.endswith('Descending') else 'ascending'} for name,field in matches]
    return {'method':'GetKdpResults', 'keys':keys, 'equalDateTieBreakDefined':len(keys)>1,
            'sourceArtifact':'reference/original/C022.txt', 'sourceArtifactSha256':sha(HERE/'original/C022.txt')}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence-prefix', required=True,
                        help='fresh write-once evidence prefix (required; never reuse a retained prefix)')
    args = parser.parse_args()
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', args.evidence_prefix):
        raise SystemExit('Invalid evidence prefix')
    prefix = args.evidence_prefix
    dests = [SLICE/(prefix+s) for s in ['-reference-results.json','-reference-observations.json','-reference-verification.log']]
    # Preflight ALL destinations, including integrity subprocess outputs, before any write.
    gate_suffixes = ['-gate-results.json','-input-hash-check.log','-baseline-revision-check.log','-baseline-hash-check.log','-source-citation-results.json','-source-citation-verification.log']
    if any(p.exists() for p in dests + [SLICE/(prefix+'-reference'+s) for s in gate_suffixes]):
        raise SystemExit('Retained evidence exists; use a fresh --evidence-prefix')
    if Path.cwd() != ROOT:
        raise SystemExit('Run verify from repository root')
    started = now()
    log, commands, observations, errors = [], [], [], []
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1', 'DOTNET_CLI_TELEMETRY_OPTOUT':'1'}
    def command(argv):
        record = {'command':argv, 'cwd':str(ROOT), 'startedAt':now()}
        p = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True)
        record.update(finishedAt=now(), exitCode=p.returncode)
        commands.append(record)
        log.append(json.dumps(record)+'\n'+p.stdout+p.stderr)
        if p.returncode:
            raise RuntimeError('Command failed: ' + ' '.join(argv))
        return p.stdout
    try:
        command(['python3', str(SLICE.relative_to(ROOT)/'verify-source-citations.py'), '--evidence-prefix', prefix+'-reference'])
        command(['python3',str(HERE.relative_to(ROOT)/'extract.py')])
        bound = json.loads((SLICE/'task-3-contract-results.json').read_text())
        if bound['failedChecks'] != 0 or bound['exitCode'] != 0:
            raise ValueError('Task-3 structural contract did not pass')
        for path, digest in bound['files'].items():
            if sha(SLICE/path) != digest:
                raise ValueError('Task-3 bound contract changed: '+path)
        fixtures = json.loads((SLICE/'fixtures.json').read_text())
        contract = json.loads((SLICE/'scenarios.json').read_text())
        cases = validate_contract(fixtures, contract)
        command(['dotnet','--info'])
        command(['dotnet','build',str(HERE.relative_to(ROOT)/'Reference.csproj'),'--nologo','--configuration','Release'])
        requests = [(s,resolve(s,fixtures)) for s in cases if s['operation'] != 'ordering-contract']
        runtime_command = ['dotnet',str(HERE/'bin/Release/net10.0/Reference.dll')]
        runtime_started = now()
        p = subprocess.run(runtime_command, input=''.join(json.dumps(r)+'\n' for _,r in requests), cwd=ROOT, env=env, capture_output=True, text=True)
        commands.append({'command':runtime_command, 'cwd':str(ROOT), 'startedAt':runtime_started,'finishedAt':now(),'exitCode':p.returncode})
        log.append(p.stdout+p.stderr)
        if p.returncode:
            raise RuntimeError('Reference runtime failed')
        lines = p.stdout.splitlines()
        if len(lines) != len(requests):
            raise ValueError('Missing/extra runtime observations')
        actual = {s['id']:json.loads(line) for (s,_),line in zip(requests, lines)}
        for scenario in cases:
            try:
                observed = ordering_observation() if scenario['operation']=='ordering-contract' else actual[scenario['id']]
                failures = [observed['error']] if 'error' in observed else compare_observation(scenario['expected'], observed)
                if scenario['operation'] in ('facets','physical-values') and observed.get('inputAfter') != scenario['inputs']:
                    failures.append('Read-only physical/facet input changed')
                observations.append({'id':scenario['id'], 'groups':scenario['groups'], 'operation':scenario['operation'], 'claim':scenario['claim'],
                                     'observed':observed, 'expected':scenario['expected'], 'passed':not failures, 'failures':failures})
            except Exception as e:
                observations.append({'id':scenario['id'],'groups':scenario['groups'],'passed':False,'failures':[repr(e)]})
    except Exception as e:
        errors.append(repr(e))
    counts = {'required':53,'executed':len(observations),'passed':sum(x['passed'] for x in observations),
              'failed':sum(not x['passed'] for x in observations), 'skipped':0}
    passed = not errors and counts['executed']==53 and counts['passed']>0 and counts['failed']==counts['skipped']==0
    inputs = [p for p in HERE.rglob('*') if p.is_file() and not any(x in p.parts for x in ('bin','obj','__pycache__')) and p.suffix not in ('.pyc','.pyo')]
    inputs += [SLICE/p for p in ['fixtures.json','scenarios.json','fixture-scenario-contract.md','source-citations.json','input-files.sha256','verify','verify-source-citations.py','task-3-contract-results.json']]
    report = {'command':sys.argv, 'cwd':str(ROOT),'startedAt':started,'finishedAt':now(), 'pythonVersion':platform.python_version(),
              'evidenceClaim':'Extracted C# rules with synthetic dependency doubles; not original Windows/Oracle execution',
              'files':{str(p.relative_to(ROOT)):sha(p) for p in sorted(inputs)}, 'commands':commands,'counts':counts,
              'groups':{g:{'executed':sum(g in x['groups'] for x in observations),'passed':sum(g in x['groups'] and x['passed'] for x in observations)} for g in sorted({g for x in observations for g in x['groups']})},
              'errors':errors,'passed':passed,'exitCode':0 if passed else 1}
    payloads = [json.dumps(report,indent=2)+'\n',json.dumps(observations,indent=2)+'\n','\n'.join(log)]
    for path, text in zip(dests,payloads):
        with path.open('x') as f:
            f.write(text)
    print(json.dumps({'counts':counts,'errors':errors,'passed':passed,'results':str(dests[0].relative_to(ROOT))}))
    return report['exitCode']

if __name__ == '__main__':
    raise SystemExit(main())
