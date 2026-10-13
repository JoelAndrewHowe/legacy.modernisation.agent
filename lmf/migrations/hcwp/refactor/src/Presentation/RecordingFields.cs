namespace Hcwp.Presentation;

public record RecordingField(string Property, string Label, string Type = "select", string[] Options = null)
{
    public string Id => Property switch { "ExaminationDate" => "contact-date", "Heart" => "heart", _ => Property };
}
public static class RecordingFields
{
    private static readonly string[] Physical = ["1|Satisfactory", "2|Concern", "3|Not assessed"];
    private static readonly string[] YesNo = ["Y|Yes", "N|No"];
    private static readonly string[] Unknown = ["Y|Yes", "N|No", "U|Not Known"];
    public static readonly RecordingField[] All = [
        new("ExaminationDate", "Contact date", "date"),
        new("Origin", "Origin", Options: ["1|Scheduled", "2|Unscheduled", "3|Movement In", "4|Amendment", "5|Not Known"]),
        new("ReasonNotExamined", "Reason not examined", Options: ["1|Was not brought", "2|Unwell or uncooperative child", "3|Examination refused", "4|Parent / Carer not present", "5|Not required"]),
        new("Consent", "Consent", Options: YesNo),
        new("Reschedule", "Reschedule", Options: YesNo),
        new("WithdrawConsent", "Withdraw consent (ordinary save does not update patient consent)", Options: ["False|No", "True|Yes"]),
        new("LocationType", "Location type", Options: ["5|GP Surgery", "2|Clinic", "1|School", "17|At Home", "6|Hospital", "18|Telephone Contact", "22|Virtual"]),
        new("LocationCode", "Location code (synthetic surgery: SYNLOC)", "text"),
        new("ExaminerCategory", "Examiner category", Options: ["18|Synthetic examiner category"]),
        new("ExaminerHcpCode", "Examiner code (synthetic: SYN001; unused: SYN002)", "text"),
        new("Height", "Height (cm)", "number"),
        new("HeightMeasurementDeclined", "Height measurement declined (changing either way clears height)", Options: YesNo),
        new("Weight", "Weight (kg)", "number"),
        new("WeightMeasurementDeclined", "Weight measurement declined (changing either way clears weight)", Options: YesNo),
        new("HeadCircumference", "Head circumference (cm; field limit below 100, save limit below 1000)", "number"),
        new("HeadMeasurementDeclined", "Head measurement declined (changing either way clears head circumference)", Options: YesNo),
        new("Heart", "Heart assessment", Options: Physical),
        new("Hips", "Hips assessment", Options: Physical),
        new("Eyes", "Eyes assessment", Options: Physical),
        new("Testes", "Testes assessment (boys label; no gender rejection rule)", Options: Physical),
        new("PhysicalGeneral", "General physical assessment", Options: Physical),
        new("ReceivingBoostSchemeService", "Receiving boost scheme service", Options: Unknown),
        new("LookedAfterChild", "Looked after child", Options: Unknown),
        new("OnChildProtectionRegister", "On child protection register", Options: Unknown),
        new("OnwardReferralsMade", "Onward referrals made", Options: YesNo),
        new("EvidenceOfXgm", "Evidence of XGM", Options: ["1|XGM observed", "2|XGM disclosed", "3|XGM not present", "4|Not examined"]),
        new("DomesticViolenceConcern", "Domestic violence assessment", Options: ["1|Assessment completed", "2|Assessment not completed"]),
        new("CoreComponent", "Core component offered", Options: ["1|Universal", "2|Enhanced", "3|Enhanced Plus", "4|Intensive", "5|Intensive Plus"])
    ];
    public static string Value(object draft, string property)
    {
        var value = draft.GetType().GetProperty(property).GetValue(draft);
        return value is DateTime date ? date.ToString(property == "ExaminationDate" ? "yyyy-MM-dd" : "O") : Convert.ToString(value, System.Globalization.CultureInfo.InvariantCulture);
    }
    public static string ErrorTarget(string error) => error.Contains("Date") || error.Contains("AlreadyEntered") ? "contact-date"
        : error.Contains("Height") ? "Height" : error.Contains("Weight") ? "Weight"
        : error.Contains("HeadCircumference") ? "HeadCircumference" : error.Contains("Location") ? "LocationCode"
        : error.Contains("Examiner") || error.Contains("Hcp") ? "ExaminerHcpCode"
        : error.Contains("Reschedule") ? "Reschedule" : error.Contains("NotExamined") ? "ReasonNotExamined" : "heart";
}
