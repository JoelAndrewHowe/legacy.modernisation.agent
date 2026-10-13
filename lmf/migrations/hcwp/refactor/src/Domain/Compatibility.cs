using System.Collections;
using System.Runtime.CompilerServices;
using Orvex.TransferObjects;

public static class ReferenceClock { public static DateTime Now; public static DateTime Today => Now.Date; }
namespace System.ServiceModel {
    public class FaultException : Exception { public FaultException(string message) : base(message) {} }
    public class FaultException<T> : FaultException { public T Detail { get; } public FaultException(T detail,string message) : base(message) { Detail=detail; } }
}
namespace Orvex.Messages.Faults {
    public class ValidationFault {
        public string Title { get; set; }
        public static System.ServiceModel.FaultException<ValidationFault> Default(string message,string title) => new(new() {Title=title},message);
    }
    public class ValidationWarningFault {
        public string Title { get; set; }
        public static System.ServiceModel.FaultException<ValidationWarningFault> Default(string message,string title) => new(new() {Title=title},message);
    }
    public class OptimisticLockFault {}
}
namespace Orvex.Messages {
    public class MessageBase { public string Message,Title,Prompt; public MessageBase(string message,string title,string prompt) { Message=message;Title=title;Prompt=prompt; } }
    public class ConfirmationMessageBase : MessageBase { public bool Response; public ConfirmationMessageBase(string message,string title,string prompt,Action<bool> action) : base(message,title,prompt) {} }
}
namespace Orvex.TransferObjects {
    // Dictionary semantics retained from AbstractTO; inline validation/locks excluded for add-only scope.
    public abstract class AbstractTO {
        readonly Dictionary<Enum,object> data=new();
        public ArrayList PropertyChanged { get; set; }=new();
        public bool EnabledPropChangeEvents { get; set; }
        public string Id { get; set; } public string Lock { get; set; }
        public object getProperty(Enum key) => data.GetValueOrDefault(key);
        public T GetPropertyOrDefault<T>(Enum key) => data.TryGetValue(key,out var v) ? (T)v : default;
        protected void setProperty(Enum key,object value,[CallerMemberName]string name=null) { data[key]=value; if(EnabledPropChangeEvents) PropertyChanged.Add(key.ToString()); }
        public abstract Array getEnumValues();
        public bool hasChanged() => PropertyChanged.Count>0;
        public void GenerateLock() { Lock="reference-lock"; EnabledPropChangeEvents=true; }
        public void CheckLock(AbstractTO other) => throw new NotSupportedException("Editing excluded");
    }
    public class ChildExaminationGivenSubTO { public long PkChildExaminationGivenId,ClientId; public string ExaminationCode,ExaminationDesc; public DateTime? ExaminationDate; public HLX.BusinessTier.Common.Util.LookupsUtility.EXAMINATION_ORIGIN? Origin; }
}
namespace Orvex.Services {
    public interface IKdpExaminationService {
        KdpExaminationTO GetKdpExamination(long clientId);
        KdpExaminationResultTO GetKdpExaminationResult(long id);
        void SaveKdpExaminationResult(KdpExaminationTO parent,KdpExaminationResultTO result);
        void DeleteKdpExaminationResult(long id,long patient,string code);
        Tuple<double,double> GetAgeRangeFromExamSchedule(string code);
    }
    public interface IChildMeasurementsService {
        decimal? CalculateBmi(decimal height,decimal weight);
        List<ChildMeasurementsRange> GetPrescribedRanges();
        List<ChildMeasurementsRange> GetExpectedRanges(string gender,DateTime birth,DateTime exam);
    }
    public interface ILookupService {
        List<LookupsSubTO> getLookups(TypeOfLookup type,string id,string category);
        List<LookupsSubTO> getLookupsByUsed(TypeOfLookup type,string id,string category,string used,bool allowCached=true);
    }
}
namespace Orvex.Services.Internal {
    public interface IMessenger { void Send<T>(T message); }
    public interface IUnitOfWork : IDisposable {
        Repository<T> Repository<T>() where T:class;
        T InsertTransferObject<S,T>(S source) where T:class,new();
        long GetNextId<T>();
        void Commit();
    }
}
namespace Orvex.ViewModels.Properties { public class Placeholder {} }
namespace Orvex.DomainModel { public class Placeholder {} }
namespace Orvex.Model.WSX_Specific_Model { public class WsxEnterResultProgress {} }
namespace Orvex.Model.Extensions { public interface IActiveDateRange { DateTime? ActiveFrom {get;set;} DateTime? ActiveTo {get;set;} } }
namespace HLX.BusinessTier.Common.Util {
    public static class ReferenceExtensions {
        public static T To<T>(this object src) where T:new() => AutoMapper.Mapper.Map<T>(src);
        public static string GetDisplayName(this Enum value) => value.ToString();
        public static IQueryable<T> Include<T>(this IQueryable<T> q,System.Linq.Expressions.Expression<Func<T,object>> e) => q;
        // Missing ActiveDateRange predicate: fixture-only compatibility, not endpoint evidence.
        public static IQueryable<T> WhereIsActive<T>(this IQueryable<T> q) where T:Orvex.Model.Extensions.IActiveDateRange => q.Where(x=>(x.ActiveFrom==null || x.ActiveFrom<=ReferenceClock.Now) && (x.ActiveTo==null || x.ActiveTo>=ReferenceClock.Now));
    }
}
