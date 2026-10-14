#!/usr/bin/env python3
"""Task-3 contract authoring, NOT a reference implementation or scenario runner.
Expectations are authored below, not obtained by executing migrated code.
Creates new contract files exclusively; never replaces retained artifacts.
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUTPUTS = [HERE / 'fixtures.json', HERE / 'scenarios.json']
if any(p.exists() for p in OUTPUTS):
    raise SystemExit('Contract destinations already exist; refusing replacement')

physical = ['Heart', 'Hips', 'Eyes', 'Testes', 'PhysicalGeneral']
selected = {
    'ClientId': 101, 'Title': 'Mx', 'Surname': 'Synthetic', 'Forename': 'Example One',
    'NhsNumber': 'SYN-NHS-101', 'DateOfBirth': '2025-01-01T00:00:00',
    'DateOfDeath': None, 'Sex': 1, 'CurrentStatus': 'SYN_ACTIVE',
    'CurrentStatusDate': None,
    'Address1': '1 Synthetic Lane', 'Address2': 'Invented District',
    'Address3': '', 'Address4': None, 'Address5': '-', 'Postcode': 'SYN POST 1',
    'ChildAlertCodes': [],
    'ChildCentres': [
        {'ChildLocationType': 'SCHOOL', 'ChildLocationCode': 'SYNSCH1',
         'ChildLocations': {'Code': 'SYNSCH1', 'Name': 'Synthetic School One', 'Organisation': None}},
        {'ChildLocationType': 'HEALTH_AUTHORITY', 'ChildLocationCode': 'SYNAREA1',
         'ChildLocations': {'Code': 'SYNAREA1', 'Name': 'Synthetic Area One', 'Organisation': 'SYNORG1'}}
    ]
}
other = copy.deepcopy(selected)
other.update(ClientId=202, Surname='Other Synthetic', Forename='Example Two',
             NhsNumber='SYN-NHS-202', Address1='2 Synthetic Lane', Sex=2)
other['ChildAlertCodes'] = [{'AlertCodes': {'AlertText': 'SYNTHETIC OTHER-PATIENT ALERT — isolation sentinel'}}]
missing = copy.deepcopy(selected)
missing.update(Title=None, Surname='', Forename='', NhsNumber=None, Sex=0,
               CurrentStatus='', Address1=None, Address2='', Address3='-',
               Address4=None, Address5='', Postcode='-', ChildCentres=[])
alert = copy.deepcopy(selected)
alert['ChildAlertCodes'] = [{'AlertCodes': {'AlertText': 'SYNTHETIC CHILD ALERT — demonstration only'}},
                          {'AlertCodes': {'AlertText': 'SYNTHETIC SECOND ALERT — no clinical meaning'}}]

# Explicit invented rows, not inserted through the legacy save workflow.
# Index patterns are only test-data diversity, not clinical/repeat algorithms.
rows = []
for i in range(23):
    day = 28 - i
    if i in (1, 2):
        day = 28  # three equal dates; no legacy tie order is expected
    row = {
        'PkChildExaminationId': 1001 + i, 'ClientId': 101,
        'ExaminationCode': 'KD03', 'ExamType': 'Kdp',
        'ExamDescription': 'Synthetic KD03 6–8-week contact',
        'ExaminationDate': f'2025-02-{day:02}T00:00:00',
        'ResultEnteredDate': f'2025-03-{1 + i % 5:02}T12:00:00',
        'OriginalExamCode': 'KD03', 'IsRepeat': i != 0,
        'ReasonNotExamined': 1 if i % 5 == 4 else None,
        'LocationType': 5 if i % 2 == 0 else 2,
        'LocationCode': 'SYNLOC1' if i % 2 == 0 else 'SYNLOC2',
        'LocationName': 'Synthetic Surgery One' if i % 2 == 0 else 'Synthetic Clinic Two',
        'ExaminerHcpCode': 'SYNHCP1' if i % 3 == 0 else 'SYNHCP2',
        'ExaminerName': 'Synthetic Examiner One' if i % 3 == 0 else 'Synthetic Examiner Two',
        'DomesticViolenceConcern': 2 if i % 4 == 0 else 1,
        'Height': None, 'Weight': None, 'HeadCircumference': None,
        'ChildMeasurementId': None,
        **{f: (None if i % 5 == 4 else 1 + (i + j) % 3) for j, f in enumerate(physical)}
    }
    rows.append(row)
# A social-only concern counterexample (no physical value 2).
rows[3].update({f: 1 for f in physical})
rows[3]['DomesticViolenceConcern'] = 2
# Equal contact/recorded dates also support a future ID tie-break test.
rows[1]['ResultEnteredDate'] = rows[2]['ResultEnteredDate']
sentinel = copy.deepcopy(rows[0])
sentinel.update(PkChildExaminationId=2001, ClientId=202, ExaminationDate='2025-03-14T00:00:00',
                LocationName='SYNTHETIC OTHER-PATIENT LOCATION', ExaminerName='SYNTHETIC OTHER-PATIENT EXAMINER')
unsupported = copy.deepcopy(rows[0])
unsupported.update(PkChildExaminationId=3001, ExaminationCode='KD04', OriginalExamCode='KD04',
                   ExamDescription='Synthetic unsupported KDP contact', ExaminationDate='2025-03-13T00:00:00')
nonkdp = copy.deepcopy(rows[0])
nonkdp.update(PkChildExaminationId=3002, ExaminationCode='SYN_OTHER', ExamType='SyntheticNonKdp')

fixtures = {
    'schemaVersion': 1, 'status': 'Authored inputs only; no reference scenario executed',
    'evidenceClaim': 'Future parity with extracted legacy logic, not execution of original Windows/Oracle UI',
    'inputManifestSha256': '3ff28bcc423ef54f0915de0ce8f6a79f2b70cf92299c2a18805e6396156f874a',
    'baselineReviewManifestSha256': '5f50912226b822117af68002edbb802b13cabec9d5b7545d7e01309685969699',
    'baselineScenarios': 'lmf/migrations/hcwp/characterise/scenarios.json#KD03-001–KD03-040 (unchanged; not copied or replaced)',
    'provenance': {
        'author': 'Task-3 doer; deterministic invented literals and index patterns in define-fixtures.py',
        'names': 'Invented Synthetic/Example/Mx components; no supplied patient example copied',
        'addresses': 'Invented Synthetic Lane/District and SYN POST tokens; not deliverable addresses',
        'nhsNumbers': 'SYN-NHS-* are deliberately nonvalid synthetic identifier strings, distinct from ClientId; no checksum or production identity claim',
        'schools': 'Invented SYNSCH* code/name pairs; no real school asserted',
        'organisations': 'Invented SYNORG1 authority code/name; authority lookup flag Y is source-backed, health-board concept NOT confirmed',
        'alerts': 'Invented uppercase SYNTHETIC text; no clinical warning advice or recovered resource prose',
        'histories': '23 invented selected-patient stored KD03 rows plus foreign-patient and contact-type sentinels; unrealistic volume solely for filter/page tests, NOT typical clinical history',
        'clock': 'Fixed wall-clock timestamps with no timezone conversion; Gregorian/en-GB controlled harness adaptation',
        'repeat': 'Stored bool values supplied as read-back inputs, not recomputed by this task; baseline repeat scenarios remain authoritative',
        'lookups': 'Invented location/professional descriptions; physical 1/2/3 values are source-backed, null is absent',
        'healthBoardDecision': {'conceptConfirmed': False, 'wordingApproved': False, 'owner': 'product owner', 'labelUntilDecision': 'Organisation', 'gap': 'SF-G04'}
    },
    'clock': '2025-03-15T12:00:00', 'culture': 'en-GB',
    'patients': {'selected': selected, 'other': other, 'missing': missing, 'alert': alert},
    'authorityLocations': [{'Code': 'SYNORG1', 'Name': 'Synthetic Organisation One', 'LocationTypes': {'Authority': 'Y'}},
                           {'Code': 'SYNORG1', 'Name': 'Synthetic nonauthority sentinel', 'LocationTypes': {'Authority': 'N'}}],
    'symbolicAdaptations': {
        'centreTypes': 'SCHOOL and HEALTH_AUTHORITY tokens represent named source enum constants; not recovered numeric identities',
        'statusCodes': 'Named CurrentStatus_* tokens represent missing constants. SYN_ACTIVE is an invented nontrigger. Literal 7 tested separately for the view age suppression; not asserted equal to a missing constant',
        'resources': 'Observe resource identity + exact arguments; do not substitute invented CodeDescriptionFormat, status, enum or alert prose',
        'gender': 'Observe GENDER enum choice/resolver request only; EnumResolver rendering unavailable',
        'repository': 'Explicit in-memory graph inputs for requested ClientId and authority predicates; no EF6/Oracle execution',
        'clock': 'Substitute fixed timestamp at DateTime.Now site only; DateOfDeath still takes precedence'
    },
    'physicalFields': physical,
    'physicalChoices': {'1': '1 - Satisfactory', '2': '2 - Concern', '3': '3 - Not assessed', 'null': 'absent, not equivalent to 3'},
    'histories': {'empty': [], 'one': [rows[0], sentinel],
                  'many': rows + [sentinel, unsupported, nonkdp]},
    'limitations': ['Extracted reference only', 'Synthetic local-demo data', 'Legacy resources/UI/EF6/Oracle unavailable',
                    'Draft Welsh deferred to Refactor; no translations authored', 'EF-in-memory target only; PostgreSQL/production unverified',
                    'Load/performance beyond deterministic query/paging deferred']
}
scenarios = []
def add(id_, groups, title, op, inputs, expected, citations, claim='extracted-legacy'):
    scenarios.append({'id': f'SF-{id_:03}', 'required': True, 'groups': groups,
                      'title': title, 'claim': claim, 'operation': op, 'inputs': inputs,
                      'expected': expected, 'sourceCitationIds': citations})

def summary_inputs(patient='selected', **overrides):
    return {'patient': patient, 'repositoryPatients': ['selected', 'other'] if patient == 'other' else ['other', patient],
            'authorityLocations': 'authorityLocations', 'clock': '2025-03-15T12:00:00',
            'patientOverrides': overrides}

add(1, ['G01', 'G05', 'G06'], 'All included fields from requested selected child; symbolic unavailable labels', 'summary', summary_inputs(), {
    'ClientId': 101, 'Fullname': 'Mx Synthetic, Example One', 'NhsNumber': 'SYN-NHS-101',
    'DateOfBirth': '2025-01-01T00:00:00', 'birthDateText': '01-Jan-2025', 'AgeString': '10 weeks',
    'ageDisplay': '10 weeks', 'ageLabelResource': 'AgeLabel',
    'genderRequest': {'enum': 'GENDER', 'value': 1, 'member': 'MALE'},
    'FullAddress': '1 Synthetic Lane, Invented District, SYN POST 1',
    'statusRequest': {'resolver': 'CurrentStatusText', 'arguments': ['SYN_ACTIVE']},
    'School': {'resource': 'CodeDescriptionFormat', 'arguments': ['SYNSCH1', 'Synthetic School One']},
    'Organisation': 'SYNORG1, Synthetic Organisation One', 'ChildAlerts': [], 'ShowAlert': False
}, ['C001','C003','C004','C005','C007','C008','C012','C015','C017','C018','C079'])
add(2, ['G02'], 'Missing optional values preserve field-specific emptiness and absent-centre dash', 'summary', summary_inputs('missing'), {
    'Fullname': '', 'NhsNumber': None, 'FullAddress': '', 'statusText': '',
    'School': '-', 'Organisation': '-', 'ChildAlerts': [], 'ShowAlert': False,
    'genderRequest': {'enum': 'GENDER', 'value': 0, 'member': 'NOTKNOWN'}
}, ['C005','C008','C014','C015','C017','C018','C079'])
add(3, ['G01','G02'], 'Name does not trim trailing separator', 'name', {'Title': '', 'Surname': 'Synthetic', 'Forename': None}, {'value': 'Synthetic, '}, ['C005'])
add(4, ['G02'], 'Address discards dash but includes each nonempty line in source sequence', 'address',
    {'Address1':'Synthetic A','Address2':'-','Address3':'Synthetic C','Address4':'Synthetic D','Address5':'Synthetic E','Postcode':''},
    {'value':'Synthetic A, Synthetic C, Synthetic D, Synthetic E'}, ['C008'])
add(5, ['G02'], 'Whitespace-only address line is not treated as missing', 'address',
    {'Address1':' ','Address2':None,'Address3':'','Address4':'-','Address5':None,'Postcode':'SYN'}, {'value':' , SYN'}, ['C008'])
for n, value, blank, expected in [(6,None,False,'-'),(7,'',True,''),(8,'Synthetic',False,'Synthetic')]:
    add(n, ['G02'], 'StaticSpan text missing/default/leave-blank branch', 'span-text',
        {'value':value,'leaveBlankIfNull':blank,'format':None}, {'text':expected}, ['C010'])
# Hand-authored age branch expectations; no implementation computes these values.
age_cases = [
    ('2025-03-15T12:00:00',None,'0 day'), ('2025-03-14T12:00:00',None,'1 day'),
    ('2025-03-09T12:00:00',None,'6 days'), ('2025-03-08T12:00:00',None,'1 week'),
    ('2025-03-02T12:00:00',None,'1 week'), ('2025-03-01T12:00:00',None,'2 weeks'),
    ('2024-12-01T00:00:00',None,'14 weeks'), ('2024-11-30T00:00:00',None,'4 months'),
    ('2024-03-31T00:00:00',None,'1 Years 0 Months'),
    ('2025-01-01T00:00:00','2025-01-08T00:00:00','1 week')
]
for n,(birth,death,expected) in enumerate(age_cases,9):
    add(n, ['G03'], f'Controlled age branch {n-8}', 'age',
        {'DateOfBirth':birth,'DateOfDeath':death,'clock':'2025-03-15T12:00:00'}, {'AgeString':expected}, ['C012'])
add(19, ['G03'], 'Web view literal 7 suppresses computed age independently of missing status constants', 'summary',
    summary_inputs(CurrentStatus='7'), {'AgeString':'10 weeks','ageDisplay':'-','ageLabelResource':'AgeLabel'}, ['C012','C013'])
add(20, ['G03','G04'], 'Death threshold replaces clock and selects age-at-death label', 'summary',
    summary_inputs(CurrentStatus='CurrentStatus_Died',DateOfDeath='2025-01-08T00:00:00'),
    {'AgeString':'1 week','ageDisplay':'1 week','ageLabelResource':'AgeAtDeath','ShowAlert':True,
     'statusAlert':{'headingResource':'ChildDiedAlertHeading','messageResource':'ChildDiedAlertMessage','date':'2025-01-08T00:00:00','dateFormatResource':'DateFormatStandard'}}, ['C012','C013','C018','C019','C020'])
add(21, ['G04'], 'Child text alone triggers alert and preserves all mapped texts', 'summary', summary_inputs('alert'),
    {'ShowAlert':True,'ChildAlerts':['SYNTHETIC CHILD ALERT — demonstration only','SYNTHETIC SECOND ALERT — no clinical meaning']}, ['C003','C018','C019'])
for n, status, stem, datekey in [(22,'CurrentStatus_MovementOut','ChildMovedOut','CurrentStatusDate'),
                                (23,'CurrentStatus_TransferredOut','ChildTransferredOut','CurrentStatusDate'),
                                (24,'CurrentStatus_Stillbirth','ChildStillborn','DateOfBirth')]:
    add(n, ['G04'], 'Status alone triggers alert: '+status, 'summary',
        summary_inputs(CurrentStatus=status,CurrentStatusDate='2025-03-01T00:00:00'),
        {'ShowAlert':True,'ChildAlerts':[], 'statusAlert':{'headingResource':stem+'AlertHeading','messageResource':stem+'AlertMessage',
         'date':'2025-01-01T00:00:00' if datekey=='DateOfBirth' else '2025-03-01T00:00:00','dateFormatResource':'DateFormatStandard'}}, ['C018','C019','C020'])
add(25, ['G04'], 'Explicit false query suppresses dialog setup, not ShowAlert condition', 'alert-setup',
    {'patient':'alert','showAlertsQuery':'false'}, {'ShowAlert':True,'setupAlertDialogs':False}, ['C019','C020'])
add(26, ['G04'], 'Non-false query permits alert dialog setup (markup condition only)', 'alert-setup',
    {'patient':'alert','showAlertsQuery':None}, {'ShowAlert':True,'setupAlertDialogs':True}, ['C019','C020'])
add(27, ['G05'], 'First SCHOOL match retained, not invented alphabetical sorting', 'summary',
    summary_inputs(ChildCentres=[{'ChildLocationType':'SCHOOL','ChildLocationCode':'SYNSCH2','ChildLocations':{'Name':'Synthetic School Two'}},
                                selected['ChildCentres'][0]]),
    {'School':{'resource':'CodeDescriptionFormat','arguments':['SYNSCH2','Synthetic School Two']},'Organisation':'-'}, ['C003','C015','C017'])
add(28, ['G05'], 'School with absent linked location still passes null name to resource format', 'summary',
    summary_inputs(ChildCentres=[{'ChildLocationType':'SCHOOL','ChildLocationCode':'SYNSCH1','ChildLocations':None}]),
    {'School':{'resource':'CodeDescriptionFormat','arguments':['SYNSCH1',None]},'Organisation':'-'}, ['C015','C017'])
for n, centres, authorities in [(29,[],[]), (30,[{'ChildLocationType':'HEALTH_AUTHORITY','ChildLocations':None}],[]),
                                (31,[selected['ChildCentres'][1]],[]),
                                (32,[selected['ChildCentres'][1]],[{'Code':'SYNORG1','Name':'Synthetic nonauthority','LocationTypes':{'Authority':'N'}}])]:
    inp=summary_inputs(ChildCentres=centres); inp['authorityLocationsOverride']=authorities
    add(n,['G05'],'Organisation missing branch / authority predicate '+str(n),'summary',inp,{'Organisation':'-'},['C017'])
add(33,['G06'],'Requested foreign patient summary is isolated from selected child','summary',summary_inputs('other'),
    {'ClientId':202,'NhsNumber':'SYN-NHS-202','Fullname':'Mx Other Synthetic, Example Two','FullAddress':'2 Synthetic Lane, Invented District, SYN POST 1',
     'ChildAlerts':['SYNTHETIC OTHER-PATIENT ALERT — isolation sentinel'],'ShowAlert':True},['C001','C003','C005','C008','C018'])

add(34,['G06','G07'],'Zero selected-patient KD03 results','results',{'history':'empty','ClientId':101,'scope':'KD03'},
    {'count':0,'orderedDateGroups':[]},['C021','C022'])
add(35,['G06','G07'],'One selected result despite other-patient sentinel','results',{'history':'one','ClientId':101,'scope':'KD03'},
    {'count':1,'orderedDateGroups':[{'date':'2025-02-28T00:00:00','idsUnordered':[1001]}]},['C021','C022'])
groups=[{'date':'2025-02-28T00:00:00','idsUnordered':[1001,1002,1003]}]
for i in range(3,23):
    groups.append({'date':f'2025-02-{28-i:02}T00:00:00','idsUnordered':[1001+i]})
add(36,['G06','G07','G08','G09'],'23 selected KD03 results, descending dates with unordered ties','results',
    {'history':'many','ClientId':101,'scope':'KD03'}, {'count':23,'orderedDateGroups':groups,'excludedIds':[2001,3001,3002]},['C021','C022'])
add(37,['G06','G07'],'Legacy service includes other KDP contact; KD03-only is explicit slice adapter','results',
    {'history':'many','ClientId':101,'scope':'all-KDP'}, {'count':24,'idsUnordered':list(range(1001,1024))+[3001],'excludedIds':[2001,3002]},['C021','C022'])
add(38,['G09'],'Complete source ordering method has only contact-date descending key','ordering-contract',
    {'citationId':'C022','registry':'source-citations.json'},
    {'method':'GetKdpResults','keys':[{'field':'ExaminationDate','direction':'descending'}],'equalDateTieBreakDefined':False},['C022'])
add(39,['G08','G09'],'Permuting equal-date input must preserve date groups, no asserted ID tie order','results',
    {'history':'many','ClientId':101,'scope':'KD03','reverseInput':True},
    {'count':23,'orderedDateGroups':groups},['C021','C022'])
add(40,['G06'],'Other-patient result retrieval returns only its sentinel','results',
    {'history':'many','ClientId':202,'scope':'KD03'},
    {'count':1,'idsUnordered':[2001],'excludedIds':list(range(1001,1024))+[3001,3002]},['C021','C022'])

for n,reason,repeat,state,label in [(41,None,False,'Recorded','Initial'),(42,1,True,'Not examined','Repeat')]:
    add(n,['G10'],'Reason and persisted repeat map to independent presentation facets','facets',
        {'ExaminationCode':'KD03','ReasonNotExamined':reason,'IsRepeat':repeat,**{f:None for f in physical},'DomesticViolenceConcern':2},
        {'examinationState':state,'repeatLabel':label,'hasConcern':False,'persistedAggregateStatus':False},
        ['C024','C025','C027','C032'], 'intentional-display-predicate-over-source-values')
for n,value,label in [(43,1,'1 - Satisfactory'),(44,2,'2 - Concern'),(45,3,'3 - Not assessed'),(46,None,None)]:
    add(n,['G10'],'Each physical field preserves choice or absent value '+str(value),'physical-values',
        {'ExaminationCode':'KD03',**{f:value for f in physical}},
        {'physical':{f:{'raw':value,'choice':label} for f in physical},'hasConcern':value==2},
        ['C027','C028','C029','C030','C031'], 'source-values-and-intentional-display-predicate')
for n, field in enumerate(physical,47):
    add(n,['G10'],'Concern predicate includes '+field+' independently','facets',
        {'ExaminationCode':'KD03','ReasonNotExamined':None,'IsRepeat':False,
         **{f:(2 if f==field else None) for f in physical},'DomesticViolenceConcern':1},
        {'hasConcern':True,'persistedAggregateStatus':False},['C027','C032'],'intentional-display-predicate-over-source-values')
add(52,['G10'],'Social/family concern names do not contribute to Has concern','facets',
    {'ExaminationCode':'KD03','ReasonNotExamined':None,'IsRepeat':False, **{f:1 for f in physical},
     'DomesticViolenceConcern':2,'OnChildProtectionRegister':'Y','LookedAfterChild':'Y'},
    {'hasConcern':False,'persistedAggregateStatus':False},['C027','C032'],'intentional-display-predicate-over-source-values')
add(53,['G10'],'Female stored Testes value is not rejected by an invented gender rule','physical-values',
    {'ExaminationCode':'KD03','Sex':2, **{f:None for f in physical},'Testes':2},
    {'physical':{'Testes':{'raw':2,'choice':'2 - Concern'}},'hasConcern':True},['C027','C028','C030','C031'],
    'source-values-and-intentional-display-predicate')

contract = {
    'schemaVersion':1, 'fixtureFile':'fixtures.json','contract':'fixture-scenario-contract.md',
    'status':'Defined, not executed; all required; no approval or reference pass claimed',
    'citationRegistry':'source-citations.json',
    'citationResolution':'IDs link existing behaviour.md records, not new inline document bindings',
    'groups': {f'G{i:02}': title for i,title in enumerate([
        'Patient mapping/formatting all included fields','Missing optional patient values','Controlled age and deceased/status paths',
        'Alert and no-alert visibility/status triggers','School and Organisation lookup formatting', 'Selected-patient isolation',
        'Zero/one/multiple KD03 retrieval','Descending contact-date order','Explicit unspecified equal-date order',
        'Reason/repeat/physical field values and intentional concern predicate'],1)},
    'scenarios':scenarios
}
for path, data in zip(OUTPUTS,[fixtures,contract]):
    with path.open('x') as stream:
        json.dump(data,stream,indent=2,ensure_ascii=False)
        stream.write('\n')
print(json.dumps({'created':[p.name for p in OUTPUTS],'scenarioDefinitions':len(scenarios),'referenceScenariosExecuted':0}))
