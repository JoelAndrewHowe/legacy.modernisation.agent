using Converted = Hcwp.SystemFeel.Converted;

namespace Hcwp.Application;

// Replaceable graph boundary: no fabricated joins to the recording-only patient entity.
public interface IPatientSummaryRepository
{
    Converted.ChildGeneral Find(long selectedPatient);
    IEnumerable<Converted.ChildLocations> AuthorityLocations();
}

public sealed record PatientSummary(
    string FullName, string NhsNumber, DateTime DateOfBirth, string Age,
    int Sex, string Address, string CurrentStatusCode, object School,
    string Organisation, bool ShowAlert, IReadOnlyList<string> Alerts);

public sealed class PatientSummaryQuery(IPatientSummaryRepository repository)
{
    public PatientSummary Read(long selectedPatient)
    {
        var patient = repository.Find(selectedPatient);
        if (patient == null || patient.ClientId != selectedPatient) return null;
        var alerts = new Converted.AlertModel
        {
            CurrentStatusCode = patient.CurrentStatus,
            ChildAlerts = patient.ChildAlertCodes.Select(a => a.AlertCodes.AlertText).ToList()
        };
        return new(Converted.Legacy.Name(patient), patient.NhsNumber, patient.DateOfBirth,
            patient.CurrentStatus == "7" ? "-" : Converted.Legacy.GetAge(patient.DateOfBirth, patient.DateOfDeath ?? ReferenceClock.Now),
            patient.Sex, Converted.Legacy.Address(patient), patient.CurrentStatus,
            Converted.Legacy.School(patient.ChildCentres.FirstOrDefault(c => c.ChildLocationType == Converted.LookupsUtility.CENTRE_TYPES.SCHOOL)),
            Converted.Legacy.GetOrganisationValue(patient.ChildCentres, new Converted.UnitOfWork { Locations = repository.AuthorityLocations().ToList() }),
            alerts.ShowAlert, alerts.ChildAlerts.AsReadOnly());
    }
}
