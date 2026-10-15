using System.Text.Json.Nodes;
using Orvex.Model;

namespace Hcwp.Persistence;

// Target-only synthetic history. Never used by approved baseline scenario seeding.
public static class DemoHistory
{
    public static void Seed(Store store, string json)
    {
        var fixture = JsonNode.Parse(json).AsObject();
        foreach (var n in fixture["locations"].AsArray()) store.Rows<ChildLocations>().Add(new() { Code = (string)n["code"], LocationType = 2, Name = (string)n["name"] });
        foreach (var n in fixture["examiners"].AsArray()) store.Rows<HealthCareProfessionals>().Add(new() { Code = (string)n["code"], StaffType = "18", Name1 = (string)n["name"] });
        foreach (var n in fixture["results"].AsArray())
        {
            var id = (long)n["id"];
            store.Rows<ChildExamination>().Add(new() { PkChildExaminationId = id, ClientId = (long)n["patient"], FkExaminationId = "KD03", IsRepeat = (bool)n["repeat"] ? "Y" : "N", Origin = 2 });
            store.Rows<ChildExaminationGiven>().Add(new() { PkFkChildExamGivenId = id,
                ExaminationDate = DateTime.Parse((string)n["date"]), ResultEnteredDate = n["recorded"] == null ? null : DateTime.Parse((string)n["recorded"]),
                FkNotExaminedReasonId = (byte?)n["reason"], FkChildLocationHeldCode = (string)n["location"], FkLocationHeldTypeId = 2,
                FkHcpExaminerCode = (string)n["examiner"], FkExaminerCatId = "18", FkStaffTypeExaminerId = "18", Origin = 2,
                RescheduleExamination = "N", HeightMeasurementRefused = "N", WeightMeasurementRefused = "N", HeadMeasurementRefused = "N" });
            store.Rows<ChildExaminationKdp>().Add(new() { PkFkExamKdpGivenId = id, Heart = (byte?)n["physical"], Hips = (byte?)n["physical"], Eyes = (byte?)n["physical"], Testes = (byte?)n["physical"], PhysicalGeneral = (byte?)n["physical"], Consent = "Y", LookedAfterChild = "N", ReceivingBoostScheme = "U", OnChildProtectionRegister = "N", OnwardReferralsMade = "N", EvidenceOfXgm = 4, DomesticViolenceConcern = 2, CoreComponent = 1 });
        }
        // Deliberately high fixture keys do not collide with new-result allocation.
        store.ExamNext = Math.Max(store.ExamNext, fixture["results"].AsArray().Max(n => (long)n["id"]) + 1);
        store.Link();
    }
}
