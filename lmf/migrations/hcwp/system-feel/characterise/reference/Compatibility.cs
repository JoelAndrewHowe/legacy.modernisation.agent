// Dependency doubles only; legacy resolver/query expressions live in Legacy.cs.
using System.Linq.Expressions;
using System.Text.Json;
using System.Text.Json.Serialization;

public static class ReferenceClock { public static DateTime Now; }
public static class LookupsUtility {
    // Symbolic constants: original numeric identities are unavailable.
    public const string CurrentStatus_MovementOut = "CurrentStatus_MovementOut";
    public const string CurrentStatus_TransferredOut = "CurrentStatus_TransferredOut";
    public const string CurrentStatus_Died = "CurrentStatus_Died";
    public const string CurrentStatus_Stillbirth = "CurrentStatus_Stillbirth";
    public static class CENTRE_TYPES { public const string HEALTH_AUTHORITY = "HEALTH_AUTHORITY", SCHOOL = "SCHOOL"; }
}
public static class Resource {
    public static object Format(string resource, params object[] arguments) => new { resource, arguments };
}
public class ChildGeneral {
    public long ClientId {get;set;}
    public string Title {get;set;}
    public string Surname {get;set;}
    public string Forename {get;set;}
    public string NhsNumber {get;set;}
    public DateTime DateOfBirth {get;set;}
    public DateTime? DateOfDeath {get;set;}
    public DateTime? CurrentStatusDate {get;set;}
    public int Sex {get;set;}
    public string CurrentStatus {get;set;}
    public string Address1 {get;set;}
    public string Address2 {get;set;}
    public string Address3 {get;set;}
    public string Address4 {get;set;}
    public string Address5 {get;set;}
    public string Postcode {get;set;}
    public List<ChildCentres> ChildCentres {get;set;} = new();
    public List<ChildAlert> ChildAlertCodes {get;set;} = new();
}
public class ChildAlert { public AlertCodes AlertCodes {get;set;} }
public class AlertCodes { public string AlertText {get;set;} }
public class ChildCentres {
    public string ChildLocationType {get;set;}
    public string ChildLocationCode {get;set;}
    public ChildLocations ChildLocations {get;set;}
}
public class ChildLocations {
    public string Code {get;set;}
    public string Name {get;set;}
    public string Organisation {get;set;}
    public LocationTypes LocationTypes {get;set;}
}
public class LocationTypes { public string Authority {get;set;} }
public interface IUnitOfWork { IEnumerable<T> Repository<T>(); }
public class UnitOfWork : IUnitOfWork {
    public List<ChildLocations> Locations;
    public IEnumerable<T> Repository<T>() => Locations.Cast<T>();
}
public static class TrackingDouble {
    public static IEnumerable<T> AsNoTracking<T>(this IEnumerable<T> source) => source;
}
public static class ExamType { public const string Kdp = "Kdp"; }
public class Row {
    public long ClientId {get;set;}
    public long PkChildExaminationId {get;set;}
    public string ExaminationCode {get;set;}
    public string ExamType {get;set;}
    public DateTime ExaminationDate {get;set;}
    [JsonExtensionData] public Dictionary<string,JsonElement> Other {get;set;}
}
public class ChildExamination {
    public long ClientId;
    public Description ExaminationDescriptions;
    public Given ChildExaminationGiven;
    public Row Saved;
}
public class Description { public string FkExamDescriptionType; }
public class Given { public DateTime ExaminationDate; }
public class ResultTO { public List<Row> HcpExaminationResultToList; }
