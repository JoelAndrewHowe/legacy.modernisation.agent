using Hcwp.Application;
using Orvex.TransferObjects;
using Orvex.Messages;
using Orvex.Services.Internal;
using System.Globalization;

namespace Hcwp.Presentation;

// Circuit-owned inputs and explicit confirmation; all clinical rules remain in the approved delegates.
public sealed class RecordingPageModel(Kd03Recording recording, LookupDouble lookups = null) : IMessenger
{
    public const long SelectedPatient = 101;
    public KdpExaminationResultTO Draft { get; private set; } = NewDraft();
    public DateTime Date { get => Draft.ExaminationDate; set => Draft.ExaminationDate = value; }
    public byte? Heart { get => Draft.Heart; set => Draft.Heart = value; }
    public string Error { get; private set; }
    public List<MessageBase> Messages { get; } = [];
    public ConfirmationMessageBase Pending { get; private set; }
    private bool? response;
    public bool Saved { get; private set; }
    public IReadOnlyList<KdpExaminationResultTO> Results { get; private set; } = [];
    public decimal? Bmi => ResultDisplay.Bmi(Draft);
    private static KdpExaminationResultTO NewDraft() => new()
    {
        ClientId = SelectedPatient, ExaminationCode = "KD03", ExaminationDate = new(2025, 2, 19),
        ResultEnteredDate = ReferenceClock.Now, Origin = 2, Reschedule = "N",
        HeightMeasurementDeclined = "N", WeightMeasurementDeclined = "N", HeadMeasurementDeclined = "N"
    };
    public void Reload() => Results = recording.ReadPatient(SelectedPatient).HcpExaminationResultToList
        .Where(r => r.ExaminationCode == "KD03").OrderByDescending(r => r.ExaminationDate).ToList();
    public void NewResult() { Draft = NewDraft(); Error = null; Pending = null; Messages.Clear(); Saved = false; }
    public void Set(string property, string value)
    {
        Pending = null; response = null; Saved = false;
        var p = Draft.GetType().GetProperty(property);
        if (property == "ExaminationDate" && string.IsNullOrEmpty(value)) { Date = DateTime.MinValue; return; }
        var type = Nullable.GetUnderlyingType(p.PropertyType) ?? p.PropertyType;
        p.SetValue(Draft, string.IsNullOrEmpty(value) ? null
            : type == typeof(DateTime) ? DateTime.Parse(value, CultureInfo.InvariantCulture)
            : Convert.ChangeType(value, type, CultureInfo.InvariantCulture));
        // Preserve the approved declined-toggle inconsistency: either direction clears the value.
        if (property.EndsWith("MeasurementDeclined"))
            Draft.GetType().GetProperty(property switch { "HeightMeasurementDeclined" => "Height", "WeightMeasurementDeclined" => "Weight", _ => "HeadCircumference" }).SetValue(Draft, null);
        if (property == "LocationType") { Draft.LocationCode = null; Draft.LocationName = null; }
        if (property == "ExaminerCategory") { Draft.ExaminerHcpCode = null; Draft.ExaminerType = null; Draft.ExaminerName = null; }
    }
    public void Confirm(bool yes)
    {
        if (Pending == null) return;
        Pending = null;
        if (!yes) { Messages.Clear(); Saved = false; return; }
        response = true; Save(); response = null;
    }
    public void Send<T>(T message)
    {
        if (message is not MessageBase m) throw new NotSupportedException("Excluded lookup window");
        Messages.Add(m);
        if (m is ConfirmationMessageBase c)
        {
            if (!response.HasValue) { Pending = c; throw new AwaitingConfirmation(); }
            c.Response = response.Value;
        }
        if (m is NonFatalErrorEncountered) Error = m.Message;
    }
    private sealed class AwaitingConfirmation : Exception { }
    public void Save()
    {
        Error = null; Pending = null; Messages.Clear(); Saved = false;
        if (Draft.PkChildExaminationId != 0) { Error = "Start a new result before saving again."; return; }
        try
        {
            Hcwp.Domain.Kd03Scope.EnsureNewResult(SelectedPatient, Draft);
            var parent = recording.CreateRules(this, lookups);
            parent.GetKdpResults(SelectedPatient);
            var d = parent.AddNewKdpResult();
            d.ExaminationDate = Draft.ExaminationDate;
            if (!d.ValidateAndSetExamCode(Draft.ExaminationCode)) return;
            // Check rejected numeric inputs before invoking setters which calculate BMI.
            if (Draft.Height.HasValue && !d.ValidateHeight(Draft.Height)) return;
            if (Draft.Weight.HasValue && !d.ValidateWeight(Draft.Weight)) return;
            if (Draft.HeadCircumference.HasValue && !d.ValidateHeadCircumference(Draft.HeadCircumference.Value)) return;
            foreach (var p in Draft.GetType().GetProperties().Where(p => p.CanRead && p.CanWrite && Store.Scalar(p.PropertyType)))
            {
                if (p.Name is "ExaminationCode" or "ExaminationDate" or "LocationCode" or "ExaminerHcpCode" or "LocationName" or "ExaminerName" or "ExaminerType") continue;
                var target = d.GetType().GetProperty(p.Name == "CoreComponent" ? "CoreComponentOffered" : p.Name);
                if (target?.CanWrite == true) target.SetValue(d, p.GetValue(Draft));
                else p.SetValue(d.KdpExaminationResultTo, p.GetValue(Draft));
            }
            if (!d.ValidateLocationCode(Draft.LocationCode) || !d.ValidateExaminerCode(Draft.ExaminerHcpCode)) return;
            d.LocationCode = Draft.LocationCode;
            if (string.IsNullOrEmpty(Draft.ExaminerCategory) && !string.IsNullOrEmpty(Draft.ExaminerHcpCode))
                d.KdpExaminationResultTo.ExaminerHcpCode = Draft.ExaminerHcpCode; // approved missing-list permissiveness
            else d.ExaminerKdpCode = Draft.ExaminerHcpCode;
            if (!d.ValidateExaminationDate(d.ExaminationDate)) return;
            if (d.Height.HasValue && !d.ValidateHeight(d.Height)) return;
            if (d.Weight.HasValue && !d.ValidateWeight(d.Weight)) return;
            if (d.HeadCircumference.HasValue && !d.ValidateHeadCircumference(d.HeadCircumference.Value)) return;
            if (!parent.Save(0)) return;
            Saved = true; Draft = d.KdpExaminationResultTo; Reload();
        }
        catch (AwaitingConfirmation) { }
        catch (ArgumentException ex) { Error = ex.Message; }
    }
}
