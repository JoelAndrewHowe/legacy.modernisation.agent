using Hcwp.Application;
using Orvex.TransferObjects;
using System.ServiceModel;

namespace Hcwp.Presentation;

// Circuit-scoped state: persistence is application-scoped, form state is not.
public sealed class RecordingPageModel(Kd03Recording recording)
{
    public const long SelectedPatient = 101;
    public DateTime Date { get; set; } = new(2025, 2, 19);
    public byte? Heart { get; set; }
    public string Error { get; private set; }
    public IReadOnlyList<KdpExaminationResultTO> Results { get; private set; } = [];

    public void Reload() => Results = recording.ReadPatient(SelectedPatient).HcpExaminationResultToList
        .Where(r => r.ExaminationCode == "KD03").ToList();

    public void Save()
    {
        Error = null;
        var draft = new KdpExaminationResultTO
        {
            ClientId = SelectedPatient, ExaminationCode = "KD03", ExaminationDate = Date,
            ResultEnteredDate = ReferenceClock.Now, Origin = 2, Reschedule = "N",
            HeightMeasurementDeclined = "N", WeightMeasurementDeclined = "N", HeadMeasurementDeclined = "N",
            Heart = Heart
        };
        try { recording.Add(SelectedPatient, draft); Reload(); }
        catch (FaultException ex) { Error = ex.Message; }
    }
}
