using Hcwp.Application;
using Orvex.TransferObjects;

namespace Hcwp.Presentation;

public static class ResultDisplay
{
    public static string Date(DateTime? date) => date?.ToString("d MMMM yyyy", System.Globalization.CultureInfo.GetCultureInfo("en-GB")) ?? "Not recorded";
    public static string Field(KdpExaminationResultTO result, RecordingField field)
    {
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
