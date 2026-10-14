#!/usr/bin/env python3
"""Negative/comparator and runtime independence checks. Not reference scenario counts."""
import argparse
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--evidence-prefix', default='task-4')
args = parser.parse_args()
if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', args.evidence_prefix):
    raise SystemExit('Invalid evidence prefix')
DEST = HERE.parent/(args.evidence_prefix+'-harness-test-results.json')
collision_prefix = args.evidence_prefix+'-self-test-collision'
SENTINEL = HERE.parent/(collision_prefix+'-reference-results.json')
# Reject retained results or any isolated collision artifacts before checks/builds.
if DEST.exists() or list(HERE.parent.glob(collision_prefix+'-*')):
    raise SystemExit('Retained test evidence exists; use a fresh --evidence-prefix')
spec = importlib.util.spec_from_file_location('reference_runner', HERE/'run.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
f = json.loads((HERE.parent/'fixtures.json').read_text())
c = json.loads((HERE.parent/'scenarios.json').read_text())
started = r.now()
checks = []
commands = []
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE':'1', 'DOTNET_CLI_TELEMETRY_OPTOUT':'1'}
def command(argv, **kwargs):
    record = {'command':argv, 'cwd':str(r.ROOT), 'startedAt':r.now()}
    proc = subprocess.run(argv, cwd=r.ROOT, env=env, capture_output=True, text=True, **kwargs)
    record.update(finishedAt=r.now(), exitCode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    commands.append(record)
    return proc
def check(name, passed):
    checks.append({'check':name,'passed':bool(passed)})
def rejects(contract):
    try:
        r.validate_contract(f,contract)
        return False
    except (ValueError,KeyError):
        return True
check('booleans are not numbers', bool(r.compare(True,1)))
check('null differs from empty', bool(r.compare(None,'')))
check('missing expected key fails', bool(r.compare({'value':None},{})))
check('extra observation keys allowed', not r.compare({'value':1},{'value':1,'extra':2}))
check('list cardinality exact', bool(r.compare([1],[1,2])))
rows = [{'PkChildExaminationId':2,'ExaminationDate':'2025-01-01'}, {'PkChildExaminationId':1,'ExaminationDate':'2025-01-01'}]
expected = {'count':2,'orderedDateGroups':[{'date':'2025-01-01','idsUnordered':[1,2]}]}
check('ties accept reversed IDs', not r.compare_observation(expected,{'count':2,'rows':rows}))
check('duplicate IDs rejected', bool(r.compare_observation(expected,{'count':2,'rows':[rows[0],rows[0]]})))
check('excluded patient row rejected', bool(r.compare_observation({'excludedIds':[2]}, {'count':2,'rows':rows})))
check('unordered multiset rejects extra rows', bool(r.compare_observation({'idsUnordered':[1]}, {'count':2,'rows':rows})))
check('incorrect observed count rejected', bool(r.compare_observation(expected, {'count':1,'rows':rows})))
for name, mutate in [
    ('empty scenario set',lambda x:x.update(scenarios=[])),
    ('missing scenario',lambda x:x['scenarios'].pop()),
    ('duplicate ID',lambda x:x['scenarios'][0].update(id='SF-002')),
    ('unknown operation',lambda x:x['scenarios'][0].update(operation='invented')),
    ('empty expectation',lambda x:x['scenarios'][0].update(expected={})),
    ('non-required scenario',lambda x:x['scenarios'][0].update(required=False)),
    ('missing group',lambda x:x['groups'].pop('G01'))]:
    changed = copy.deepcopy(c)
    mutate(changed)
    check(name+' fails closed',rejects(changed))

# Exercise compiled rules with inputs different from the original expectations.
# This demonstrates outputs are computed, not a hard-coded fixture/ID replay.
mutations = [
    ('name responds to data', c['scenarios'][2], {'Surname':'Changed Synthetic'}, 'value', 'Changed Synthetic, '),
    ('address responds to data', c['scenarios'][3], {'Address1':'Changed Address'}, 'value', 'Changed Address, Synthetic C, Synthetic D, Synthetic E'),
    ('age responds to clock', c['scenarios'][8], {'clock':'2025-03-16T12:00:00'}, 'AgeString','1 day'),
    ('concern responds to physical data',c['scenarios'][46],{'Heart':1},'hasConcern',False),
    ('literal false is case sensitive',c['scenarios'][24],{'showAlertsQuery':'False'},'setupAlertDialogs',True)
]
requests=[]
for name, scenario, updates, key, expected_value in mutations:
    request=r.resolve(scenario,f)
    request['inputs'].update(updates)
    requests.append(request)
# Force compilation of current sources: never trust an ambient gitignored DLL.
build = command(['dotnet','build',str(HERE/'Reference.csproj'),'--nologo','--configuration','Release','--no-incremental'])
check('current reference sources build', build.returncode == 0)
p = command(['dotnet',str(HERE/'bin/Release/net10.0/Reference.dll')], input=''.join(json.dumps(x)+'\n' for x in requests)) if build.returncode == 0 else None
if p is None or p.returncode or len(p.stdout.splitlines())!=len(mutations):
    check('mutation runtime completes',False)
else:
    for mutation,line in zip(mutations,p.stdout.splitlines()):
        name,scenario,updates,key,value=mutation
        actual=json.loads(line)
        check(name, actual.get(key)==value and bool(r.compare(scenario['expected'],actual)))
# No source/evidence writes are allowed on a destination collision.
with SENTINEL.open('x') as out:
    json.dump({'evidenceType':'Isolated self-test collision sentinel', 'prefix':collision_prefix}, out)
    out.write('\n')
def snapshot():
    return {str(path):r.sha(path) for path in HERE.parent.iterdir() if path.is_file()}
before = snapshot()
# Missing/invalid prefixes must be usage failures, never attempts at a default run.
for entry in ([str(HERE.parent/'verify')], [sys.executable,str(HERE/'run.py')]):
    p = command(entry)
    check('explicit prefix required: '+Path(entry[-1]).name,
          p.returncode == 2 and 'usage:' in p.stderr and '--evidence-prefix' in p.stderr and before == snapshot())
p = command([str(HERE.parent/'verify'),'--evidence-prefix','../invalid'])
check('invalid prefix rejected before writes',p.returncode != 0 and 'Invalid evidence prefix' in p.stderr and before == snapshot())
p = command([str(HERE.parent/'verify'),'--evidence-prefix',collision_prefix])
check('existing evidence rejected before writing',p.returncode!=0 and 'Retained evidence exists' in (p.stdout+p.stderr) and before==snapshot())
check('collision creates no other prefixed evidence', list(HERE.parent.glob(collision_prefix+'-*')) == [SENTINEL])
# The same self-test prefix must also fail before checks or rebuilding.
p = command([sys.executable,str(HERE/'test-harness.py'),'--evidence-prefix',args.evidence_prefix])
check('self-test collision rejected before checks',p.returncode!=0 and 'Retained test evidence exists' in (p.stdout+p.stderr) and before==snapshot())
sources = [HERE/name for name in ['Reference.csproj','Legacy.cs','Compatibility.cs','Program.cs','test-harness.py','run.py']]
results={'command':sys.argv,'cwd':str(Path.cwd()),'startedAt':started,'finishedAt':r.now(),'commands':commands,'files':{str(path.relative_to(r.ROOT)):r.sha(path) for path in sources},'binarySha256':r.sha(HERE/'bin/Release/net10.0/Reference.dll') if build.returncode == 0 else None,'collisionSentinel':str(SENTINEL.relative_to(r.ROOT)),'evidenceType':'Harness self-tests, NOT required scenario counts','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'exitCode':int(any(not x['passed'] for x in checks))}
with DEST.open('x') as out:
    json.dump(results,out,indent=2)
    out.write('\n')
print(json.dumps(results))
raise SystemExit(results['exitCode'])
