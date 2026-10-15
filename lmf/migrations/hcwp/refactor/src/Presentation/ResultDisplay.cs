using Hcwp.Application;
using Orvex.TransferObjects;

namespace Hcwp.Presentation;

public static class ResultDisplay
{
    public static readonly (string Title, string[] Properties)[] Groups = [
        ("Contact details", ["ExaminationDate", "ReasonNotExamined", "Consent", "Reschedule", "WithdrawConsent"]),
        ("Measurements", ["Height", "Weight", "HeadCircumference", "HeightMeasurementDeclined", "WeightMeasurementDeclined", "HeadMeasurementDeclined"]),
        ("Physical assessments", ["Heart", "Hips", "Eyes", "Testes", "PhysicalGeneral"]),
        ("Child and family information", ["ReceivingBoostSchemeService", "LookedAfterChild", "OnChildProtectionRegister", "OnwardReferralsMade", "EvidenceOfXgm", "DomesticViolenceConcern", "CoreComponent"]),
        ("Location and professional", ["LocationType", "LocationCode", "ExaminerCategory", "ExaminerHcpCode"]),
        ("Recording metadata", ["Origin"])
    ];
    public static decimal? Bmi(KdpExaminationResultTO result) => result.Height is > 0 && result.Weight.HasValue
        ? Math.Min(99.99m, Math.Round(result.Weight.Value / ((result.Height.Value / 100) * (result.Height.Value / 100)), 2)) : null;
    public static string Date(DateTime? date) => date?.ToString("d MMMM yyyy", System.Globalization.CultureInfo.GetCultureInfo("en-GB")) ?? "Not recorded";
    public static string Field(KdpExaminationResultTO result, RecordingField field)
    {
        if (field.Property == "WithdrawConsent") return "Not stored with result; ordinary save does not update patient consent";
        if (field.Property == "LocationCode") return PatientBannerValues.Present(result.LocationName);
        if (field.Property == "ExaminerHcpCode") return PatientBannerValues.Present(result.ExaminerName);
        if (field.Property == "ExaminationDate") return Date(result.ExaminationDate);
        var value = RecordingFields.Value(result, field.Property);
        if (string.IsNullOrEmpty(value)) return "Not recorded";
        if (field.Options == null) return value;
        return field.Options.Select(o => o.Split('|')).FirstOrDefault(o => o[0] == value)?[1] ?? "Description unavailable";
    }
    public static string Label(RecordingField field) => field.Property switch
    {
        "LocationCode" => "Location", "ExaminerHcpCode" => "Examiner",
        "WithdrawConsent" => "Withdraw consent requested", "Testes" => "Testes assessment",
        "HeightMeasurementDeclined" => "Height measurement declined", "WeightMeasurementDeclined" => "Weight measurement declined",
        "HeadMeasurementDeclined" => "Head measurement declined", "HeadCircumference" => "Head circumference (cm)",
        _ => field.Label
    };
}
