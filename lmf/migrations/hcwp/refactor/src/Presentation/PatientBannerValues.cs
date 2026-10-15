using System.Text.Json;
using Hcwp.Application;

namespace Hcwp.Presentation;

// Product-authored descriptions are not recovered legacy resource prose.
public static class PatientBannerValues
{
    public static string Present(string value) => string.IsNullOrWhiteSpace(value) || value == "-" ? "Not recorded" : value;
    public static IEnumerable<(string Label, string Value)> Read(PatientSummary patient)
    {
        yield return ("Full name", Present(patient.FullName));
        yield return ("NHS number", Present(patient.NhsNumber));
        yield return ("Date of birth", patient.DateOfBirth.ToString("d MMMM yyyy", System.Globalization.CultureInfo.GetCultureInfo("en-GB")));
        yield return ("Age", Present(patient.Age));
        yield return ("Sex", patient.Sex switch { 1 => "Male", 2 => "Female", 9 => "Not specified", _ => "Not known" });
        yield return ("Address", Present(patient.Address));
        yield return ("Current status", patient.CurrentStatusCode == "SYN_ACTIVE" ? "Synthetic active status (demonstration fixture)" :
            string.IsNullOrEmpty(patient.CurrentStatusCode) ? "Not recorded" : "Status description unavailable (CurrentStatusText)");
        var school = JsonSerializer.SerializeToElement(patient.School);
        var schoolText = school.ValueKind == JsonValueKind.Object && school.TryGetProperty("arguments", out var arguments)
            ? Present(arguments[1].GetString()) + " — legacy format unavailable (CodeDescriptionFormat)" : "Not recorded";
        yield return ("School", schoolText);
        // Approved target wording: demo organisation fixtures represent Welsh health boards only.
        // The converted lookup/formatting remains unchanged.
        yield return ("Health board", Present(patient.Organisation));
    }
}
