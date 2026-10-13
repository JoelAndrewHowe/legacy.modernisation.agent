#!/usr/bin/env python3
"""Reproducible source extraction. Never uses scenario expectations."""
import re, hashlib, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
SOURCE = ROOT / 'example-code/HCWP Core (pseudonymised) - single file.txt'
raw = SOURCE.read_bytes()
assert hashlib.sha256(raw).hexdigest() == 'f381d3207ac7ef32c0408fc16f8bb5252b7ec0e5ce134453592c54dde9f900a2'
s = raw.decode('utf-8-sig')
files = {}
for m in re.finditer(r'>>> FILE (\d+)/94: (.*?)   \[.*?\]\n=+\n(.*?)<<< END FILE', s.replace('\r\n','\n'), re.S):
    files[int(m[1])] = (m[2], m[3])

def method(n, name):
    text = files[n][1]
    m = re.search(r'^        (?:public|private|internal).*?\b'+name+r'\(', text, re.M)
    assert m, name
    start = text.index('{', m.start()); depth = 1; end = start + 1
    while depth:
        depth += (text[end]=='{') - (text[end]=='}'); end += 1
    return text[m.start():end] + '\n'

out = HERE/'legacy'; out.mkdir(exist_ok=True)
original = HERE/'original'; original.mkdir(exist_ok=True)
selected = [5,6,8,9,12,14,15,18,23,24,25,27,28,32,33,34,35,42,43,44] + list(range(70,87)) + [89]
manifest=[]
for n in selected:
    path, text = files[n]
    (original/f'{n:02d}-{Path(path).name}.txt').write_text(text)
    manifest.append({'bundleFile':n,'originalPath':path,'extractedSha256':hashlib.sha256(text.encode()).hexdigest()})
for n in [5,6,8,9,12,14,15,18,23,24,25,27,28,32,33,34,35]+list(range(70,87))+[89]:
    text=files[n][1].replace('DateTime.Now','ReferenceClock.Now').replace('DateTime.Today','ReferenceClock.Today')
    text=text.replace('[NotifyPropertyChangedInvocator]','')
    text=re.sub(r'^\s*#(?:end)?region.*$', '', text, flags=re.M)
    if n==6:
        # Missing/mismatched members in the trimmed input: references bind directly to TO.
        for name in ['RskResponsiveParenting','RskEngagement','RskSocioFactors','DskHearingAndLanguage','DskSpeechAndLanguage']:
            text=re.sub(r'(?m)^(\s*)'+name+r' = null;',r'\1KdpExaminationResultTo.'+name+' = null;',text)
    (out/Path(files[n][0]).name).write_text('// Extracted bundle file '+str(n)+'; see extract.py and README.md.\n'+text)
text=files[42][1].replace('using System.ServiceModel.Activation;','using Orvex.TransferObjects;').replace('[AspNetCompatibilityRequirements(RequirementsMode = AspNetCompatibilityRequirementsMode.Allowed)]','')
(out/'ChildMeasurementsService.cs').write_text(text)
text='using System.Linq; using Orvex.Model; using Orvex.Services.Internal;\nnamespace Orvex.Business.Utils { public class ExaminationsCrudManager {\n'+method(43,'UpdateRepeatFlags')+'\n// Excluded infrastructure boundaries: intentionally no-op.\ninternal static void UpdateAppointmentStatuses(IUnitOfWork u, string c, long p, long i) {}\ninternal static void ClearProducedRecalls(IUnitOfWork u, string c, long p) {}\n}}\n'
(out/'ExaminationsCrudManager.cs').write_text(text)
text='using System; using System.Collections.Generic; using System.Linq; using AutoMapper; using HLX.BusinessTier.Common.Util; using Orvex.Business.Utils; using Orvex.Business.Validation; using Orvex.Model; using Orvex.Services; using Orvex.Services.Internal; using Orvex.TransferObjects; using Orvex.Contracts.Enums;\nnamespace Orvex.Business { public class KdpExaminationService : IKdpExaminationService {\nprivate readonly Func<IUnitOfWork> unitOfWorkFactory; private readonly KdpExaminationValidator kdpExaminationValidator; private const byte PreschoolConsentCategory=2, MedicalConsentType=11; private const string kdpConsentYesValue="Y";\npublic KdpExaminationService(Func<IUnitOfWork> factory, KdpExaminationValidator validator) { unitOfWorkFactory=factory; kdpExaminationValidator=validator; }\n'
for name in ['GetKdpExamination','GetChildDetails','GetKdpResultTo','GetKdpExaminationResult','SaveKdpExaminationResult','InsertKdpExaminationResult','GetChildExaminationPrimaryKey','GetNextChildMeasurementPrimaryKey','GetAgeRangeFromExamSchedule']:
    text+=method(44,name)
text+='private static List<ChildExaminationGivenSubTO> GetKdpOutstandingAppointments(long p,IUnitOfWork u) => new();\nprivate void UpdateKdpExaminationResult(IUnitOfWork u,KdpExaminationResultTO t,ChildExamination c) => throw new NotSupportedException("Editing excluded");\npublic void DeleteKdpExaminationResult(long i,long p,string c) => throw new NotSupportedException("Deletion excluded");\n}}\n'
(out/'KdpExaminationService.cs').write_text(text)
# Convert the original AutoMapper configuration into inspectable assignment methods.
config=method(44,'ConfigureMappings')
mapping='using System; using System.Linq; using Orvex.Model; using Orvex.TransferObjects;\nnamespace AutoMapper { public static class Mapper {\n'
for src,dst,body in re.findall(r'Mapper.CreateMap<(\w+), (\w+)>\(\)(.*?);',config,re.S):
    if src=='PreSchoolExams_NextExamDue_ProcResults': continue
    props=lambda typ: re.findall(r'public (?:virtual )?([\w?]+)\s+(\w+)\s*\{', next(t for p,t in files.values() if re.search(r'class '+typ+r'\b',t)))
    sp={name:typ for typ,name in props(src)}; dp={name:typ for typ,name in props(dst)}
    explicit={}
    for dest,expr in re.findall(r'\.ForMember\(dest => dest\.(\w+), act => act\.MapFrom\(src => (.*?)\)\)',body,re.S):
        explicit[dest]=expr.strip()
        if dest=='ExaminerName': explicit[dest]='string.Join(" ", src.HealthCareProfessionals.Name1, src.HealthCareProfessionals.Name2)'
        if dest=='FkNotExaminedReasonId': explicit[dest]='string.IsNullOrEmpty(src.ReasonNotExamined) ? (byte?)null : Convert.ToByte(src.ReasonNotExamined)'
    for dest,res,expr in re.findall(r'\.ForMember\(dest => dest\.(\w+), act => act\.ResolveUsing<(\w+)>\(\)\.FromMember\(src => (.*?)\)\)',body,re.S):
        explicit[dest]= expr+' == "Y"' if res=='StringToBoolResolver' else expr+' ? "Y" : "N"'
    for name in dp:
        if name in sp and name not in explicit: explicit[name]='src.'+name
    mapping+=f'public static void Map({src} src, {dst} dest) {{\n'
    for name,expr in explicit.items():
        if name not in dp: continue
        if src=='ChildExaminationGiven' and name=='ReasonNotExamined': expr='src.FkNotExaminedReasonId?.ToString()'
        if src=='ChildMeasurement' and name=='PkChildExaminationId': expr='src.FkChildExaminationId ?? 0'
        # AutoMapper null-propagates absent navigation properties.
        expr=expr.replace('src.ExaminationDescriptions.LongDescription','src.ExaminationDescriptions?.LongDescription').replace('src.ChildLocations.Name','src.ChildLocations?.Name').replace('src.Examiner.Description','src.Examiner?.Description').replace('src.HealthCareProfessionals.Name1','src.HealthCareProfessionals?.Name1').replace('src.HealthCareProfessionals.Name2','src.HealthCareProfessionals?.Name2').replace('src.ChildExaminationGiven.ExamNotExaminedReason.KdpDescription','src.ChildExaminationGiven?.ExamNotExaminedReason?.KdpDescription')
        if dst=='ChildExaminationGiven' and name=='Origin': expr='src.Origin ?? 0'
        mapping+=f'dest.{name} = {expr};\n'
    mapping+='}\n'
mapping+='public static T Map<T>(object src) where T : new() { var dest=new T(); Map((dynamic)src,(dynamic)dest); return dest; }\n}}\n'
(HERE/'Mapping.cs').write_text(mapping)
# Resource prose is absent: use resource identifiers, retaining formatting call sites.
texts='\n'.join(p.read_text() for p in out.glob('*.cs'))
keys=set(re.findall(r'\b([A-Z]\w*(?:Message|Prompt|Title|Text|Flag|Description))\b',texts))
keys.update(re.findall(r'(?:nameof\(Resources\.|Name = ")([A-Z]\w+)',texts))
keys.update(['ConfirmContinue','ResultsRecordedButNotExamined','KdpContactGivenBeforeMinAge','KdpContactGivenAfterMaxAge'])
(HERE/'Resources.cs').write_text('namespace Orvex.Resources { public static class Resources {\n'+''.join(f'public static string {k} => "{k}";\n' for k in sorted(keys))+'}}\n')
(HERE/'extraction-manifest.json').write_text(json.dumps({'sourceSha256':hashlib.sha256(raw).hexdigest(),'files':manifest},indent=2)+'\n')
