using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Orvex.Business;
using Orvex.Business.Utils;
using Orvex.Business.Validation;
using Orvex.Model;
using Orvex.TransferObjects;
using Orvex.ViewModels;
using Orvex.Messages;

public static class ScenarioAdapter {
    public static void Set(object target,string name,JsonNode value) {
        var p=target.GetType().GetProperty(name) ?? throw new InvalidOperationException("Unknown input property "+name);
        p.SetValue(target,value==null ? null : JsonSerializer.Deserialize(value.ToJsonString(),p.PropertyType));
    }
    public static JsonObject Values(object target) {
        var o=new JsonObject();
        foreach(var p in target.GetType().GetProperties().Where(p=>p.CanRead && p.GetMethod.IsPublic && Store.Scalar(p.PropertyType))) o[p.Name]=JsonSerializer.SerializeToNode(p.GetValue(target));
        return o;
    }
    static Store Seed(JsonObject f,JsonObject scenario) {
        var store=new Store {ExamNext=(long)f["sequences"]["examinationNext"],MeasurementNext=(long)f["sequences"]["measurementNext"]};
        foreach(var (_,n) in f["patients"].AsObject()) {
            store.Rows<ChildGeneral>().Add(new() {ClientId=(long)n["ClientId"],DateOfBirth=DateTime.Parse((string)n["DateOfBirth"]),DateOfDeath=n["DateOfDeath"]==null?null:DateTime.Parse((string)n["DateOfDeath"]),Sex=(string)n["Gender"]});
            store.Rows<Consent>().Add(new() {ClientId=(long)n["ClientId"],ConsentCategory=2,ConsentType=11,ConsentResult=(bool)n["HasPreschoolConsent"]?"Y":"N"});
        }
        var op=f["operationalLookups"];
        foreach(var n in op["examinations"].AsArray()) store.Rows<ExaminationDescriptions>().Add(new() {PkExamDescriptionId=(string)n["Code"],LongDescription=(string)n["Description"],FkExamDescriptionType=(Orvex.Contracts.Enums.ExamType)(byte)n["ExamType"]});
        foreach(var n in op["locations"].AsArray()) store.Rows<ChildLocations>().Add(new() {Code=(string)n["Code"],LocationType=(byte)n["LocationType"],Name=(string)n["Name"]});
        foreach(var n in op["examiners"].AsArray()) store.Rows<HealthCareProfessionals>().Add(new() {Code=(string)n["Code"],StaffType=(string)n["Type"],Name1=(string)n["Name1"],Name2=(string)n["Name2"]});
        foreach(var n in op["examinerCategories"].AsArray()) store.Rows<Examiner>().Add(new() {PkExaminerId=(string)n["Code"],Description=(string)n["Description"]});
        foreach(var (k,v) in f["choices"]["reasons"].AsObject()) store.Rows<ExamNotExaminedReason>().Add(new() {PkExamNotExamRsonId=byte.Parse(k),KdpDescription=(string)v});
        var env=f["environments"][(string)scenario["environment"] ?? "standard"];
        foreach(var n in env["schedule"].AsArray()) store.Rows<PreschoolScheduleExams>().Add(new() {FkExamCode=(string)n["ExaminationCode"],MinimumAgeWks=(decimal?)n["MinimumAgeWks"],MaximumAgeWks=(decimal?)n["MaximumAgeWks"],ActiveFrom=DateTime.Parse((string)n["ActiveFrom"]),ActiveTo=DateTime.Parse((string)n["ActiveTo"])});
        store.Rows<SystemGeneralOptions>().Add(new() {LBmiIndex=(byte?)env["bmiOptions"]["LBmiIndex"],HBmiIndex=(byte?)env["bmiOptions"]["HBmiIndex"]});
        foreach(var n in env["centileBands"].AsArray()) store.Rows<DeviationsCentile>().Add(new() {Age=(short)n["Age"],Gender=(string)n["Gender"],MeasurementType=(string)n["MeasurementType"],UpperBound=(decimal?)n["Upper"],LowerBound=(decimal?)n["Lower"]});
        foreach(var n in f["histories"][(string)scenario["history"] ?? "empty"].AsArray()) {
            var t=new KdpExaminationResultTO(); foreach(var (k,v) in n.AsObject()) { if(k!="IsRepeat") Set(t,k,v); } t.IsRepeat=(string)n["IsRepeat"]=="Y";
            var ce=new ChildExamination(); var g=new ChildExaminationGiven(); var kd=new ChildExaminationKdp();
            AutoMapper.Mapper.Map(t,ce); AutoMapper.Mapper.Map(t,g); AutoMapper.Mapper.Map(t,kd);
            store.Rows<ChildExamination>().Add(ce); store.Rows<ChildExaminationGiven>().Add(g); store.Rows<ChildExaminationKdp>().Add(kd);
        }
        store.Link(); return store;
    }
    public static JsonObject Execute(JsonObject f,JsonObject s) {
        ReferenceClock.Now=DateTime.Parse((string)f["clock"]["now"]);
        var store=Seed(f,s); var before=store.Snapshot();
        var counts=new[]{store.Rows<ChildExamination>().Count,store.Rows<ChildExaminationGiven>().Count,store.Rows<ChildExaminationKdp>().Count,store.Rows<ChildMeasurement>().Count};
        var patient=f["patients"][(string)s["patient"]]; long id=(long)patient["ClientId"];
        var messenger=new Messenger(s["confirmations"]?.AsArray().Select(n=>(bool)n) ?? Enumerable.Empty<bool>());
        var validator=new KdpExaminationValidator();
        var service=new ObservedService(new KdpExaminationService(()=>new UnitOfWork(store),validator));
        var measurements=new ChildMeasurementsService(()=>new UnitOfWork(store));
        var lookups=new LookupDouble(f);
        var parent=new KdpExaminationDelegate(service,validator,messenger,()=>new KdpExaminationResultDelegate(validator,messenger,lookups,measurements,service));
        parent.GetKdpResults(id);
        var op=(string)s["operation"]; var accepted=true; var saved=false; JsonObject second=null;
        KdpExaminationResultDelegate d=null;
        if(op=="repeat") {
            JsonObject first=null;
            for(int r=0;r<(int)s["runs"];r++) { using var u=new UnitOfWork(store); ExaminationsCrudManager.UpdateRepeatFlags(u,id,"KD03"); u.Commit(); if(r==0) first=store.Snapshot(); else second=new JsonObject {["sameAfterSecondRun"]=JsonNode.DeepEquals(first,store.Snapshot())}; }
        } else {
            d=parent.AddNewKdpResult();
            var input=(JsonObject)f["drafts"][(string)s["draft"]].DeepClone();
            if(s["overrides"] is JsonObject overrides) foreach(var (k,v) in overrides) input[k]=v?.DeepClone();
            if(op=="draft") {} // Defaults only, no fixture mutation.
            else if(op=="unsupported" || (op!="field" && input["ExaminationCode"]!=null && (string)input["ExaminationCode"]!="KD03")) accepted=false;
            else if(op=="record") {
                d.ExaminationDate=DateTime.Parse((string)input["ExaminationDate"]);
                accepted=d.ValidateAndSetExamCode((string)input["ExaminationCode"]);
                if(accepted) {
                    foreach(var (k,v) in input.Where(kv=>kv.Key.EndsWith("MeasurementDeclined"))) Set(d.KdpExaminationResultTo,k,v);
                    foreach(var k in new[]{"LocationType","ExaminerCategory"}) if(input.ContainsKey(k)) Set(d,k,input[k]);
                    foreach(var (k,v) in input) {
                        if(k is "ExaminationCode" or "ExaminationDate" or "LocationType" or "ExaminerCategory" || k.EndsWith("MeasurementDeclined")) continue;
                        if(k=="LocationCode") { if(!d.ValidateLocationCode((string)v)) {accepted=false;break;} }
                        if(k=="ExaminerHcpCode") { if(!d.ValidateExaminerCode((string)v)) {accepted=false;break;} }
                        Set(d,k=="CoreComponent"?"CoreComponentOffered":k=="ExaminerHcpCode"?"ExaminerKdpCode":k,v);
                    }
                    if(accepted) accepted=d.ValidateExaminationDate(d.ExaminationDate);
                    if(accepted && d.Height.HasValue) accepted=d.ValidateHeight(d.Height);
                    if(accepted && d.Weight.HasValue) accepted=d.ValidateWeight(d.Weight);
                    if(accepted && d.HeadCircumference.HasValue) accepted=d.ValidateHeadCircumference(d.HeadCircumference.Value);
                    if(accepted) saved=accepted=parent.Save(0);
                }
            } else {
                foreach(var (k,v) in input) Set(d.KdpExaminationResultTo,k,v);
                // Refresh lazy date/schedule ranges after raw TO population.
                d.Populate(d.KdpExaminationResultTo,(string)patient["Gender"],DateTime.Parse((string)patient["DateOfBirth"]),patient["DateOfDeath"]==null?null:DateTime.Parse((string)patient["DateOfDeath"]),service.GetKdpExamination(id).HcpExaminationResultToList);
                if(op=="field") {
                    var method=d.GetType().GetMethod((string)s["method"]) ?? throw new InvalidOperationException("Unknown field method");
                    var arg=JsonSerializer.Deserialize(s["value"].ToJsonString(),method.GetParameters()[0].ParameterType);
                    accepted=(bool)method.Invoke(d,new[]{arg});
                } else {
                    if(op=="decline") foreach(var a in s["assignments"].AsArray()) Set(d,(string)a["property"],a["value"]);
                    if(op!="save" && op!="decline") throw new InvalidOperationException("Unknown operation "+op);
                    saved=accepted=parent.Save(0);
                }
            }
        }
        if(messenger.Responses.Count!=0) throw new InvalidOperationException("Unused confirmation responses");
        var obs=new JsonObject {["accepted"]=accepted,["saved"]=saved,["messages"]=messenger.SemanticMessages(),["newRows"]=new JsonObject {["examination"]=store.Rows<ChildExamination>().Count-counts[0],["given"]=store.Rows<ChildExaminationGiven>().Count-counts[1],["kdp"]=store.Rows<ChildExaminationKdp>().Count-counts[2],["measurement"]=store.Rows<ChildMeasurement>().Count-counts[3]},["storeUnchanged"]=JsonNode.DeepEquals(before,store.Snapshot()),["offeredCodes"]=new JsonArray("KD03")};
        if(op=="unsupported") obs["messages"].AsArray().Add(new JsonObject {["kind"]="ScopeError",["key"]="UnsupportedContact"});
        if(d!=null) {
            obs["fieldValues"]=Values(d.KdpExaminationResultTo); obs["draftValues"]=Values(d.KdpExaminationResultTo);
            obs["requiredFlags"]=new JsonObject {["IsHeightRequired"]=d.IsHeightRequired,["IsWeightRequired"]=d.IsWeightRequired,["IsHeadCircumferenceRequired"]=d.IsHeadCircumferenceRequired};
            if(d.Height!=0) { obs["bmi"]=JsonSerializer.SerializeToNode(d.Bmi); obs["bmiOutsideRange"]=d.IsBmiOutsideRange; }
            else obs["bmiUnobserved"]="Rejected raw height=0; no BMI getter invoked on save failure";
            var ranges=new JsonObject(); foreach(var range in measurements.GetExpectedRanges((string)patient["Gender"],DateTime.Parse((string)patient["DateOfBirth"]),d.ExaminationDate)) ranges[range.MeasurementType]=new JsonObject {["LowerBound"]=range.LowerBound,["UpperBound"]=range.UpperBound}; obs["expectedRanges"]=ranges;
        }
        if(saved) obs["savedValues"]=Values(service.GetKdpExaminationResult(d.PkChildExaminationId)); // new UoW, new entities, new TO
        if(service.Fault is {} fault) {
            obs["errors"]=new JsonArray(fault.Message.Split('\n',StringSplitOptions.RemoveEmptyEntries).Select(line=>(JsonNode)JsonValue.Create(line[(line.IndexOf(": ")+2)..].TrimEnd('\r'))).ToArray());
            obs["validatorPrompt"]=fault.Detail.Title;
            var message=messenger.Sent.OfType<NonFatalErrorEncountered>().Last(); obs["savePrompt"]=message.Prompt;
            obs["parentNotification"]=new JsonObject {["type"]=message.GetType().Name,["kind"]="Error",["title"]=message.Title,["prompt"]=message.Prompt};
        }
        var flags=new JsonObject(); foreach(var ce in store.Rows<ChildExamination>().Where(c=>c.FkExaminationId=="KD03")) flags[ce.PkChildExaminationId.ToString()]=ce.IsRepeat;
        obs["repeatFlags"]=flags;
        var unchanged=new JsonArray(); foreach(var (_,p) in f["patients"].AsObject()) { long pid=(long)p["ClientId"]; if(JsonNode.DeepEquals(PatientSnapshot(before,pid),store.Snapshot(pid))) unchanged.Add(pid); } obs["unchangedPatients"]=unchanged;
        obs["kd03Order"]=new JsonArray(service.GetKdpExamination(id).HcpExaminationResultToList.Where(t=>t.ExaminationCode=="KD03").OrderByDescending(t=>t.ExaminationDate).Select(t=>(JsonNode)JsonValue.Create(t.PkChildExaminationId)).ToArray());
        if(second!=null) obs["sameAfterSecondRun"]=second["sameAfterSecondRun"].DeepClone();
        return obs;
    }
    static JsonObject PatientSnapshot(JsonObject all,long patient) {
        var result=new JsonObject(); var ids=all[nameof(ChildExamination)].AsArray().Where(n=>(long)n["ClientId"]==patient).Select(n=>(long)n["PkChildExaminationId"]).ToHashSet();
        foreach(var (table,rows) in all) { var a=new JsonArray(); foreach(var n in rows.AsArray()) { bool belongs=table is nameof(ChildExamination) or nameof(ChildMeasurement) ? (long)n["ClientId"]==patient : ids.Contains((long)n[table==nameof(ChildExaminationGiven)?"PkFkChildExamGivenId":"PkFkExamKdpGivenId"]); if(belongs) a.Add(n.DeepClone()); } result[table]=a; } return result;
    }
}
