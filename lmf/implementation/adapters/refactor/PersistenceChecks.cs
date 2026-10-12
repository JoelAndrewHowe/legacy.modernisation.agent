using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Infrastructure;

public static class PersistenceChecks
{
    public static void Run(string destination)
    {
        var options = new DbContextOptionsBuilder<RecordingContext>().UseInMemoryDatabase("checks-" + Guid.NewGuid()).Options;
        var service = new RecordingService(new PooledDbContextFactory<RecordingContext>(options));
        service.Seed();
        var results = new List<object>();
        void Check(string id, Action action)
        {
            try { action(); results.Add(new { id, passed = true, diagnostic = "" }); }
            catch (Exception error) { results.Add(new { id, passed = false, diagnostic = error.ToString() }); }
        }
        void Require(bool condition, string message) { if (!condition) throw new Exception(message); }
        var sibling = JsonSerializer.Serialize(service.Read(2002));
        Check("fresh-context-all-kd03-fields", () =>
        {
            var dto = service.New();
            dto.Height = 55; dto.Weight = 4; dto.HeadCircumference = 35;
            dto.Heart = 1; dto.Hips = 2; dto.Eyes = 3; dto.Testes = 4; dto.PhysicalGeneral = 5;
            dto.CoreComponent = 1; dto.EvidenceOfXgm = 2; dto.DomesticViolenceConcern = 3;
            dto.LocationType = 5; dto.LocationCode = "SYNTH"; dto.ExaminerCategory = "18"; dto.ExaminerHcpCode = "SYNTH";
            dto.OnwardReferralsMade = "Y"; dto.ReceivingBoostSchemeService = "N"; dto.LookedAfterChild = "N";
            dto.OnChildProtectionRegister = "N"; dto.Sector = "synthetic";
            var expected = JsonSerializer.SerializeToNode(dto).AsObject();
            var outcome = service.Save(dto, true);
            Require(outcome.Saved, JsonSerializer.Serialize(outcome));
            Require(dto.PkChildExaminationId == 0, "Must not echo or mutate supplied DTO");
            var read = service.Read().Single();
            Require(!ReferenceEquals(read, dto) && !ReferenceEquals(read, outcome.ReadBack), "Detached fresh reads required");
            var actual = JsonSerializer.SerializeToNode(read).AsObject();
            foreach (var field in expected)
            {
                if (field.Key is "PkChildExaminationId" or "ExamDescription") continue;
                Require(JsonNode.DeepEquals(field.Value, actual[field.Key]), "Stored mismatch: " + field.Key);
            }
            read.Heart = 99;
            Require(service.Read().Single().Heart == 1, "Detached read mutation leaked");
        });
        Check("invalid-no-write", () =>
        {
            var before = JsonSerializer.Serialize(service.Read());
            foreach (var mutate in new Action<KdpExaminationResultTO>[] {
                d => d.ExaminationCode = "KD08", d => d.ClientId = 2002,
                d => d.Height = 0, d => d.HeadCircumference = 100,
                d => d.ExaminationDate = new(2026, 1, 1), d => d.ReasonNotExamined = "2" })
            {
                var dto = service.New(); dto.ExaminationDate = new(2025, 2, 23); dto.Heart = 1; mutate(dto);
                var rejected = service.Save(dto, true);
                Require(!rejected.Saved && rejected.Errors.Length > 0, "Invalid submission accepted");
                Require(JsonSerializer.Serialize(service.Read()) == before, "Rejected submission changed persistence");
            }
            var empty = service.New(); empty.ExaminationDate = new(2025, 2, 19);
            Require(!service.Save(empty, true).Saved, "NoResults must reject");
        });
        Check("warnings-confirmation-repeat-patient-isolation", () =>
        {
            var before = service.Read().Count;
            var earlier = service.New(); earlier.ExaminationDate = new(2025, 2, 10); earlier.Heart = 2; earlier.Consent = "N";
            var pending = service.Save(earlier);
            Require(!pending.Saved && pending.Errors.Length == 0 && pending.Warnings.Contains("KdpDuplicateExamCodeMessage") && pending.Warnings.Contains("KdpContactGivenBeforeMinAge"), JsonSerializer.Serialize(pending));
            Require(service.Read().Count == before, "Unconfirmed warnings wrote data");
            Require(service.Save(earlier, true).Saved, "Confirmed warning blocked");
            var rows = service.Read().OrderBy(r => r.ExaminationDate).ToList();
            Require(!rows[0].IsRepeat && rows[1].IsRepeat, "Repeat flags not persisted");
            Require(JsonSerializer.Serialize(service.Read(2002)) == sibling, "Other patient changed");
            Require(!service.Save(earlier, true).Saved, "Same date duplicate saved");
        });
        Check("decline-clears-and-bmi-warning", () =>
        {
            var dto = service.New(); dto.ExaminationDate = new(2025, 2, 21); dto.Heart = 1;
            dto.Height = 55; dto.HeightMeasurementDeclined = "Y";
            Require(service.Save(dto, true).ReadBack.Height == null, "Decline failed to clear");
            var low = service.New(); low.ExaminationDate = new(2025, 2, 22); low.Height = 55; low.Weight = 3;
            var pending = service.Save(low);
            Require(pending.Warnings.Contains("BmiOutsidePrescribedRangeMessage") && !pending.Saved, "BMI warning omitted");
        });
        var json = JsonSerializer.SerializeToNode(results).AsArray();
        File.WriteAllText(destination, JsonSerializer.Serialize(new { checks = json, passed = json.Count(r => r["passed"].GetValue<bool>()), failed = json.Count(r => !r["passed"].GetValue<bool>()), skipped = 0 }, new JsonSerializerOptions { WriteIndented = true }));
        if (json.Any(r => !r["passed"].GetValue<bool>())) throw new Exception("Persistence checks failed; see " + destination);
    }
}
