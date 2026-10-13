using System.Collections;
using Hcwp.Persistence;
using Microsoft.EntityFrameworkCore;
using System.Linq.Expressions;
using System.Text.Json.Nodes;
using Orvex.Model;
using Orvex.Services;
using Orvex.Services.Internal;
using Orvex.TransferObjects;
using Orvex.Messages;

public class Repository<T> : IQueryable<T> where T:class {
    readonly List<T> rows; IQueryable<T> Query => rows.AsQueryable();
    public Repository(List<T> rows) { this.rows=rows; }
    public IQueryable<T> Local() => Query;
    public IQueryable<T> Include(Expression<Func<T,object>> path) => Query;
    public Type ElementType => Query.ElementType; public Expression Expression => Query.Expression; public IQueryProvider Provider => Query.Provider;
    public IEnumerator<T> GetEnumerator() => rows.GetEnumerator(); IEnumerator IEnumerable.GetEnumerator() => GetEnumerator();
}
public class Store {
    public Dictionary<Type,IList> Tables=new();
    public long ExamNext,MeasurementNext;
    readonly RecordingDatabase database = new();
    bool initialized;
    readonly object gate = new();
    public long Allocate(Type type) { lock(gate) return type==typeof(ChildExamination) ? ExamNext++ : type==typeof(ChildMeasurement) ? MeasurementNext++ : throw new NotSupportedException(); }
    public RecordingContext Open() {
        lock(gate) {
            if(!initialized) {
                using var seed=database.Open();
                foreach(var rows in Tables.Values) foreach(var row in rows) seed.Add(CloneRow(row));
                seed.SaveChanges(); initialized=true;
            }
        }
        return database.Open();
    }
    public static Store Load(RecordingContext context) {
        var result=new Store();
        foreach(var type in RecordingContext.EntityTypes) {
            var method=typeof(Store).GetMethod(nameof(LoadRows),System.Reflection.BindingFlags.Static|System.Reflection.BindingFlags.NonPublic).MakeGenericMethod(type);
            result.Tables[type]=(IList)method.Invoke(null,new object[]{context});
        }
        result.Link(); return result;
    }
    static List<T> LoadRows<T>(RecordingContext context) where T:class => context.Set<T>().ToList();
    public void Reload() { using var context=Open(); Tables=Load(context).Tables; Link(); }
    public List<T> Rows<T>() where T:class { if(!Tables.ContainsKey(typeof(T))) Tables[typeof(T)]=new List<T>(); return (List<T>)Tables[typeof(T)]; }
    public static bool Scalar(Type t) => t.IsValueType || t==typeof(string);
    public static object CloneRow(object src) {
        var dest=Activator.CreateInstance(src.GetType());
        foreach(var p in src.GetType().GetProperties().Where(p=>p.CanWrite && Scalar(p.PropertyType))) p.SetValue(dest,p.GetValue(src));
        return dest;
    }
    public Store Clone() {
        var copy=new Store {ExamNext=ExamNext,MeasurementNext=MeasurementNext};
        foreach(var (type,rows) in Tables) { var list=(IList)Activator.CreateInstance(typeof(List<>).MakeGenericType(type)); foreach(var row in rows) list.Add(CloneRow(row)); copy.Tables[type]=list; }
        copy.Link(); return copy;
    }
    public void Link() {
        foreach(var ce in Rows<ChildExamination>()) {
            ce.ChildExaminationGiven=Rows<ChildExaminationGiven>().SingleOrDefault(g=>g.PkFkChildExamGivenId==ce.PkChildExaminationId);
            ce.ExaminationDescriptions=Rows<ExaminationDescriptions>().SingleOrDefault(d=>d.PkExamDescriptionId==ce.FkExaminationId);
            ce.ChildMeasurement=Rows<ChildMeasurement>().Where(m=>m.FkChildExaminationId==ce.PkChildExaminationId).ToList();
            if(ce.ChildExaminationGiven is {} g) {
                g.ChildExamination=ce;
                g.ChildExaminationKdp=Rows<ChildExaminationKdp>().SingleOrDefault(k=>k.PkFkExamKdpGivenId==g.PkFkChildExamGivenId);
                if(g.ChildExaminationKdp is {} k) k.ChildExaminationGiven=g;
                g.ChildLocations=Rows<ChildLocations>().SingleOrDefault(l=>l.Code==g.FkChildLocationHeldCode && l.LocationType==g.FkLocationHeldTypeId);
                g.HealthCareProfessionals=Rows<HealthCareProfessionals>().SingleOrDefault(h=>h.Code==g.FkHcpExaminerCode && h.StaffType==g.FkStaffTypeExaminerId);
                g.Examiner=Rows<Examiner>().SingleOrDefault(e=>e.PkExaminerId==g.FkExaminerCatId);
                g.ExamNotExaminedReason=Rows<ExamNotExaminedReason>().SingleOrDefault(r=>r.PkExamNotExamRsonId==g.FkNotExaminedReasonId);
            }
        }
        foreach(var child in Rows<ChildGeneral>()) child.Consents=Rows<Consent>().Where(c=>c.ClientId==child.ClientId).ToList();
    }
    public JsonObject Snapshot(long? patient=null) {
        var result=new JsonObject();
        foreach(var type in new[]{typeof(ChildExamination),typeof(ChildExaminationGiven),typeof(ChildExaminationKdp),typeof(ChildMeasurement)}) {
            var a=new JsonArray();
            foreach(var row in Tables.GetValueOrDefault(type) ?? new ArrayList()) {
                long owner;
                if(row is ChildExamination ce) owner=ce.ClientId;
                else if(row is ChildMeasurement cm) owner=cm.ClientId;
                else { var id=(long)row.GetType().GetProperties().First(p=>p.Name.StartsWith("Pk")).GetValue(row); owner=Rows<ChildExamination>().Single(c=>c.PkChildExaminationId==id).ClientId; }
                if(patient!=null && owner!=patient) continue;
                var o=new JsonObject();
                foreach(var p in type.GetProperties().Where(p=>p.CanWrite && Scalar(p.PropertyType)).OrderBy(p=>p.Name)) o[p.Name]=System.Text.Json.JsonSerializer.SerializeToNode(p.GetValue(row));
                a.Add(o);
            }
            result[type.Name]=a;
        }
        return result;
    }
}
public class UnitOfWork : IUnitOfWork {
    readonly Store committed; readonly RecordingContext context; public Store Working;
    public UnitOfWork(Store store) { committed=store; context=store.Open(); Working=Store.Load(context); }
    public Repository<T> Repository<T>() where T:class => new(Working.Rows<T>());
    public T InsertTransferObject<S,T>(S source) where T:class,new() { var row=new T(); AutoMapper.Mapper.Map((dynamic)source,(dynamic)row); Working.Rows<T>().Add(row); context.Add(row); Working.Link(); return row; }
    public long GetNextId<T>() => committed.Allocate(typeof(T));
    public void Commit() { Working.Link(); context.SaveChanges(); committed.Reload(); }
    public void Dispose() => context.Dispose();
}
public class LookupDouble : ILookupService {
    readonly JsonObject f;
    public LookupDouble(JsonObject fixtures) { f=fixtures; }
    public List<LookupsSubTO> getLookups(TypeOfLookup type,string id,string category) {
        var op=f["operationalLookups"];
        if(type==TypeOfLookup.AllExams) return op["examinations"].AsArray().Select(n=>new LookupsSubTO {Code=(string)n["Code"],Description=(string)n["Description"]}).ToList();
        if(type==TypeOfLookup.ExaminerByPrimaryKeyKdp) return op["examinerCategories"].AsArray().Select(n=>new LookupsSubTO {Code=(string)n["Code"],Description=(string)n["Description"]}).ToList();
        if(type==TypeOfLookup.ExamLocationTypeKdp || type==TypeOfLookup.ExamNotExaminedReasonKdp) return f["choices"][type==TypeOfLookup.ExamLocationTypeKdp?"locationTypes":"reasons"].AsObject().Select(kv=>new LookupsSubTO {Code=kv.Key,Description=(string)kv.Value}).ToList();
        if(type==TypeOfLookup.Locations) return op["locations"].AsArray().Where(n=>n["LocationType"].ToString()==category).Select(n=>new LookupsSubTO {Code=(string)n["Code"],Description=(string)n["Description"]}).ToList();
        if(type==TypeOfLookup.Examiners) return op["examiners"].AsArray().Where(n=>(string)n["Category"]==category).Select(n=>new LookupsSubTO {Code=(string)n["Code"],Description=(string)n["Description"],UsedCode=(string)n["UsedCode"],Type=(string)n["Type"]}).ToList();
        throw new NotSupportedException(type.ToString());
    }
    public List<LookupsSubTO> getLookupsByUsed(TypeOfLookup type,string id,string category,string used,bool allowCached=true) => getLookups(type,id,category).Where(x=>used!="Y" || x.UsedCode=="Y").ToList();
}
public class Messenger : IMessenger {
    public readonly List<MessageBase> Sent=new(); public readonly Queue<bool> Responses;
    public Messenger(IEnumerable<bool> responses) { Responses=new(responses); }
    public void Send<T>(T message) {
        if(message is not MessageBase m) throw new NotSupportedException("Lookup windows excluded");
        Sent.Add(m);
        if(m is ConfirmationMessageBase c) { if(Responses.Count==0) throw new InvalidOperationException("Missing confirmation response"); c.Response=Responses.Dequeue(); }
    }
    public JsonArray SemanticMessages() {
        var result=new JsonArray(); var seenBmi=false;
        foreach(var m in Sent) {
            if(m.Prompt=="ExamResultsErrorSavingPrompt") continue;
            if(m.Message=="BmiOutsidePrescribedRangeMessage") { if(seenBmi) continue; seenBmi=true; }
            result.Add(new JsonObject { ["kind"]=m is ConfirmationMessageBase?"Confirmation":m is WarningNotificationMessage?"Warning":"Error",["key"]=m.Message });
        }
        return result;
    }
}
// Observes the real inner fault without changing its propagation to parent Save.
public class ObservedService : IKdpExaminationService {
    readonly Orvex.Business.KdpExaminationService service;
    public System.ServiceModel.FaultException<Orvex.Messages.Faults.ValidationFault> Fault;
    public ObservedService(Orvex.Business.KdpExaminationService service) { this.service=service; }
    public KdpExaminationTO GetKdpExamination(long p)=>service.GetKdpExamination(p);
    public KdpExaminationResultTO GetKdpExaminationResult(long i)=>service.GetKdpExaminationResult(i);
    public Tuple<double,double> GetAgeRangeFromExamSchedule(string c)=>service.GetAgeRangeFromExamSchedule(c);
    public void DeleteKdpExaminationResult(long i,long p,string c)=>throw new NotSupportedException();
    public void SaveKdpExaminationResult(KdpExaminationTO p,KdpExaminationResultTO r) {
        try { service.SaveKdpExaminationResult(p,r); } catch(System.ServiceModel.FaultException<Orvex.Messages.Faults.ValidationFault> ex) { Fault=ex; throw; }
    }
}
