using System.Text.Json;
using System.Text.Json.Nodes;
using Orvex.Model;

namespace Hcwp.Persistence;

public static class DemoData
{
    public static void Set(object target, string property, JsonNode value)
    {
        var p = target.GetType().GetProperty(property) ?? throw new ArgumentException(property);
        p.SetValue(target, value == null ? null : JsonSerializer.Deserialize(value.ToJsonString(), p.PropertyType));
    }

    public static Store Seed(JsonObject f, string environment = "standard")
    {
        var store = new Store { ExamNext = (long)f["sequences"]["examinationNext"], MeasurementNext = (long)f["sequences"]["measurementNext"] };
        foreach (var (_, n) in f["patients"].AsObject())
        {
            store.Rows<ChildGeneral>().Add(new() { ClientId = (long)n["ClientId"], DateOfBirth = DateTime.Parse((string)n["DateOfBirth"]), DateOfDeath = n["DateOfDeath"] == null ? null : DateTime.Parse((string)n["DateOfDeath"]), Sex = (string)n["Gender"] });
            store.Rows<Consent>().Add(new() { ClientId = (long)n["ClientId"], ConsentCategory = 2, ConsentType = 11, ConsentResult = (bool)n["HasPreschoolConsent"] ? "Y" : "N" });
        }
        var op = f["operationalLookups"];
        foreach (var n in op["examinations"].AsArray()) store.Rows<ExaminationDescriptions>().Add(new() { PkExamDescriptionId = (string)n["Code"], LongDescription = (string)n["Description"], FkExamDescriptionType = (Orvex.Contracts.Enums.ExamType)(byte)n["ExamType"] });
        foreach (var n in op["locations"].AsArray()) store.Rows<ChildLocations>().Add(new() { Code = (string)n["Code"], LocationType = (byte)n["LocationType"], Name = (string)n["Name"] });
        foreach (var n in op["examiners"].AsArray()) store.Rows<HealthCareProfessionals>().Add(new() { Code = (string)n["Code"], StaffType = (string)n["Type"], Name1 = (string)n["Name1"], Name2 = (string)n["Name2"] });
        foreach (var n in op["examinerCategories"].AsArray()) store.Rows<Examiner>().Add(new() { PkExaminerId = (string)n["Code"], Description = (string)n["Description"] });
        foreach (var (k, v) in f["choices"]["reasons"].AsObject()) store.Rows<ExamNotExaminedReason>().Add(new() { PkExamNotExamRsonId = byte.Parse(k), KdpDescription = (string)v });
        var env = f["environments"][environment];
        foreach (var n in env["schedule"].AsArray()) store.Rows<PreschoolScheduleExams>().Add(new() { FkExamCode = (string)n["ExaminationCode"], MinimumAgeWks = (decimal?)n["MinimumAgeWks"], MaximumAgeWks = (decimal?)n["MaximumAgeWks"], ActiveFrom = DateTime.Parse((string)n["ActiveFrom"]), ActiveTo = DateTime.Parse((string)n["ActiveTo"]) });
        store.Rows<SystemGeneralOptions>().Add(new() { LBmiIndex = (byte?)env["bmiOptions"]["LBmiIndex"], HBmiIndex = (byte?)env["bmiOptions"]["HBmiIndex"] });
        foreach (var n in env["centileBands"].AsArray()) store.Rows<DeviationsCentile>().Add(new() { Age = (short)n["Age"], Gender = (string)n["Gender"], MeasurementType = (string)n["MeasurementType"], UpperBound = (decimal?)n["Upper"], LowerBound = (decimal?)n["Lower"] });
        store.Link();
        return store;
    }
}
