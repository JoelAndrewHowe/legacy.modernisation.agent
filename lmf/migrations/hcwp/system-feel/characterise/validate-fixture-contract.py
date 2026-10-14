#!/usr/bin/env python3
"""Structural input validation only; does NOT execute reference scenarios."""
import collections
import datetime
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
DEST = HERE / 'task-3-contract-results.json'
if DEST.exists():
    raise SystemExit('Retained structural evidence already exists; refusing overwrite')
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
checks = []
def check(name, condition):
    checks.append({'check': name, 'passed': bool(condition)})

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

f = json.loads((HERE / 'fixtures.json').read_text())
s = json.loads((HERE / 'scenarios.json').read_text())
citations = {r['id']: r for r in json.loads((HERE / 'source-citations.json').read_text())}
scenarios = s['scenarios']
fields = ['Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral']
ops = {'summary','name','address','span-text','age','alert-setup','results','ordering-contract','physical-values','facets'}
check('nonempty v1 contracts', f['schemaVersion'] == s['schemaVersion'] == 1 and len(scenarios) > 0)
check('stable unique IDs', len({x['id'] for x in scenarios}) == len(scenarios) and
      all(re.fullmatch(r'SF-\d{3}', x['id']) for x in scenarios))
check('53 authored required definitions (NOT executed scenarios)', len(scenarios) == 53 and all(x['required'] is True for x in scenarios))
check('all ten seed groups present', set(s['groups']) == {f'G{i:02}' for i in range(1,11)} and
      {g for x in scenarios for g in x['groups']} == set(s['groups']))
check('exact physical field inventory', f['physicalFields'] == fields)
check('provenance all categories', all(f['provenance'].get(k) for k in
      ['names','addresses','nhsNumbers','schools','organisations','alerts','histories','clock','repeat','lookups']))
check('no health-board agent approval', f['provenance']['healthBoardDecision']['conceptConfirmed'] is False and
      f['provenance']['healthBoardDecision']['wordingApproved'] is False)
check('bound input and baseline manifest identities',
      digest(HERE / 'input-files.sha256') == f['inputManifestSha256'] and
      digest(ROOT / 'lmf/migrations/hcwp/characterise/review-files.sha256') == f['baselineReviewManifestSha256'])
check('all source citation references resolve to behaviour records', all(
      x['sourceCitationIds'] and all(c in citations and citations[c]['document']=='behaviour.md' for c in x['sourceCitationIds'])
      for x in scenarios))
check('expectations nonempty and operations supported', all(x['expected'] and x['operation'] in ops for x in scenarios))
check('summary fixture refs and unique repository IDs', all(
      x['inputs']['patient'] in f['patients'] and
      x['inputs']['patient'] in x['inputs']['repositoryPatients'] and
      len({f['patients'][p]['ClientId'] for p in x['inputs']['repositoryPatients']}) == len(x['inputs']['repositoryPatients'])
      for x in scenarios if x['operation']=='summary'))
check('alert fixture refs', all(x['inputs']['patient'] in f['patients'] for x in scenarios if x['operation']=='alert-setup'))
check('history refs', all(x['inputs']['history'] in f['histories'] for x in scenarios if x['operation']=='results'))
rows = f['histories']['many']
selected = [r for r in rows if r['ClientId']==101 and r['ExaminationCode']=='KD03']
check('23 selected-patient KD03 stored inputs', len(selected)==23)
check('unique result IDs', len({r['PkChildExaminationId'] for r in rows})==len(rows))
check('other patient sentinel', any(r['ClientId']==202 for r in rows))
check('unsupported KDP and non-KDP sentinels', any(r['ExaminationCode']=='KD04' and r['ExamType']=='Kdp' for r in rows)
      and any(r['ExamType']!='Kdp' for r in rows))
check('two locations and examiners', len({r['LocationCode'] for r in selected})>=2 and len({r['ExaminerHcpCode'] for r in selected})>=2)
check('both reason and repeat states', {r['IsRepeat'] for r in selected}=={True,False} and
      any(r['ReasonNotExamined'] is None for r in selected) and any(r['ReasonNotExamined'] is not None for r in selected))
check('every physical field has null/1/2/3 inputs', all({r[field] for r in selected}=={None,1,2,3} for field in fields))
check('physical values distinguish absence and not-assessed', f['physicalChoices']['null'] != f['physicalChoices']['3'])
check('social-only false-concern stored counterexample', any(r['DomesticViolenceConcern']==2 and
      all(r[field]!=2 for field in fields) for r in selected))
check('explicit inclusive future date boundaries', min(r['ExaminationDate'] for r in selected)=='2025-02-06T00:00:00' and
      max(r['ExaminationDate'] for r in selected)=='2025-02-28T00:00:00')
check('equal contact and recorded dates exist', len({(r['ExaminationDate'],r['ResultEnteredDate']) for r in selected})<len(selected))
check('histories not already ordered', [r['ExaminationDate'] for r in rows] != sorted([r['ExaminationDate'] for r in rows],reverse=True))
# Validate authored membership expectations against fixture bytes, not legacy retrieval behaviour.
for x in scenarios:
    if x['operation'] != 'results':
        continue
    inp, expected = x['inputs'], x['expected']
    membership = [r for r in f['histories'][inp['history']] if r['ClientId']==inp['ClientId'] and
                  r['ExamType']=='Kdp' and (inp['scope']=='all-KDP' or r['ExaminationCode']=='KD03')]
    ids = collections.Counter(r['PkChildExaminationId'] for r in membership)
    check(x['id']+' authored count consistent with fixture membership', len(membership)==expected['count'])
    check(x['id']+' authored exclusions consistent with fixture membership', all(i not in ids for i in expected.get('excludedIds',[])))
    if 'idsUnordered' in expected:
        check(x['id']+' complete authored membership', collections.Counter(expected['idsUnordered'])==ids)
    if 'orderedDateGroups' in expected:
        groups=expected['orderedDateGroups']
        dates=[g['date'] for g in groups]
        check(x['id']+' date groups descend and exhaust membership', dates==sorted(dates,reverse=True) and
              len(dates)==len(set(dates)) and collections.Counter(i for g in groups for i in g['idsUnordered'])==ids and
              all(collections.Counter(g['idsUnordered'])==collections.Counter(
                  r['PkChildExaminationId'] for r in membership if r['ExaminationDate']==g['date']) for g in groups))
check('no result expectations accidentally prescribe tie ID order', all('orderedIds' not in x['expected'] for x in scenarios if x['operation']=='results'))
check('source inspection is required, not runtime tie observation alone', any(x['operation']=='ordering-contract' and
      x['inputs']['citationId']=='C022' and x['expected']['equalDateTieBreakDefined'] is False for x in scenarios))
check('all five independent intentional concern cases', all(any(x['operation']=='facets' and x['inputs'].get(field)==2 and
      all(x['inputs'].get(other)!=2 for other in fields if other!=field) and x['expected'].get('hasConcern') is True for x in scenarios)
      for field in fields))
check('no stored aggregate field in input histories', all(not any(k.lower() in {'hasconcern','overallstatus','aggregatestatus'} for k in r) for r in rows))
check('deceased threshold and literal7 separately specified', any(x['operation']=='age' and x['inputs']['DateOfDeath'] is not None for x in scenarios)
      and any(x['operation']=='summary' and x['inputs']['patientOverrides'].get('CurrentStatus')=='7' for x in scenarios))
check('unavailable labels tested symbolically', any(isinstance(x['expected'].get('School'),dict) for x in scenarios)
      and any('genderRequest' in x['expected'] for x in scenarios))
counts = {g: sum(g in x['groups'] for x in scenarios) for g in s['groups']}
failed = [x['check'] for x in checks if not x['passed']]
result = {'command':'PYTHONDONTWRITEBYTECODE=1 python3 lmf/migrations/hcwp/system-feel/characterise/validate-fixture-contract.py',
          'cwd':str(Path.cwd()),'startedAt':started,'finishedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'evidenceType':'structural contract validation, NOT reference observations',
          'files':{name:digest(HERE/name) for name in ['fixtures.json','scenarios.json','fixture-scenario-contract.md','define-fixtures.py','validate-fixture-contract.py']},
          'scenarioDefinitions':len(scenarios),'referenceScenariosExecuted':0,'groups':counts,
          'structuralChecks':checks,'passedChecks':len(checks)-len(failed),'failedChecks':len(failed),
          'failures':failed,'exitCode':1 if failed else 0}
with DEST.open('x') as stream:
    json.dump(result,stream,indent=2); stream.write('\n')
print(json.dumps({k:result[k] for k in ['scenarioDefinitions','referenceScenariosExecuted','passedChecks','failedChecks','failures','exitCode']}))
raise SystemExit(result['exitCode'])
