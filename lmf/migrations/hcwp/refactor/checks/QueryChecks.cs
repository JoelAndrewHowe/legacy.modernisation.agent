using Hcwp.Application;
using Hcwp.Persistence;
using Orvex.Model;
using System.Text.Json;
using System.Text.Json.Nodes;
using C = Hcwp.SystemFeel.Converted;

// Synthetic query semantics below supplement (not replace) the approved SF
// input-only observations in SystemFeelObservations.cs, executed by verify-task-2.
public static partial class QueryChecks
{
    sealed class SummaryRepository : IPatientSummaryRepository
    {
        public C.ChildGeneral Patient = new() { ClientId = 101, Surname = "Synthetic", Forename = "Baby", NhsNumber = "SYNTHETIC-101", DateOfBirth = new(2025, 1, 1), Sex = 2, Address1 = "1 Synthetic Road", Address2 = "-", Postcode = "TEST" };
        public C.ChildGeneral Find(long id) => id == Patient.ClientId ? Patient : null;
        public IEnumerable<C.ChildLocations> AuthorityLocations() => [];
    }
    sealed class MisScopedSummaryRepository(C.ChildGeneral patient) : IPatientSummaryRepository
    {
        public C.ChildGeneral Find(long id) => patient;
        public IEnumerable<C.ChildLocations> AuthorityLocations() => [];
    }
    public static int Run(string fixturePath)
    {
        var results = new List<object>();
        void Check(string name, Action test)
        {
            try { test(); results.Add(new { name, status = "passed" }); }
            catch (Exception e) { results.Add(new { name, status = "failed", error = e.ToString() }); }
        }
        void Require(bool condition) { if (!condition) throw new InvalidOperationException("Query assertion failed"); }
        var f = JsonNode.Parse(File.ReadAllText(fixturePath)).AsObject();
        ReferenceClock.Now = new(2025, 2, 20);
        var store = DemoData.Seed(f);
        // Query-only volume fixture, not clinically typical history. Persisted via
        // the same EF InMemory graph/mapping as recording; no expectations injected.
        for (var i = 1; i <= 26; i++)
        {
            var id = 1000 + i;
            store.Rows<ChildExamination>().Add(new() { PkChildExaminationId = id, ClientId = i == 26 ? 202 : 101, FkExaminationId = i == 25 ? "KD04" : "KD03", IsRepeat = i % 2 == 0 ? "Y" : "N" });
            store.Rows<ChildExaminationGiven>().Add(new() { PkFkChildExamGivenId = id, ExaminationDate = new DateTime(2025, 2, 1).AddDays(i / 3), ResultEnteredDate = i % 3 == 0 ? null : new DateTime(2025, 3, 1).AddDays(i == 4 ? 1 : i % 2), FkNotExaminedReasonId = i % 4 == 0 ? (byte)1 : null, FkChildLocationHeldCode = i % 2 == 0 ? "A" : "B", FkHcpExaminerCode = i % 3 == 0 ? "X" : "Y" });
            store.Rows<ChildExaminationKdp>().Add(new() { PkFkExamKdpGivenId = id, Heart = (byte)(i % 3 + 1), RskFamilyHealth = 2 });
        }
        // Add KD04 metadata independently of whether baseline supplies it.
        if (!store.Rows<ExaminationDescriptions>().Any(x => x.PkExamDescriptionId == "KD04"))
            store.Rows<ExaminationDescriptions>().Add(new() { PkExamDescriptionId = "KD04", FkExamDescriptionType = Orvex.Contracts.Enums.ExamType.Kdp });
        store.Link();
        using (store.Open()) { }
        var recording = new Kd03Recording(store);
        var q = new Kd03ResultsQuery(recording);
        var before = store.Snapshot().ToJsonString();
        ResultsPage all;
        try { all = q.Search(101, new() { PageSize = 50 }); }
        catch (Exception e)
        {
            Console.WriteLine(JsonSerializer.Serialize(new { total = 1, passed = 0, failed = 1, skipped = 0,
                results = new[] { new { name = "absent recorded date query mapping and ordering", status = "failed", error = e.ToString() } } }));
            return 1;
        }
        Check("selected patient KD03 isolation", () => Require(all.Total == 24 && all.Rows.All(r => r.ClientId == 101 && r.ExaminationCode == "KD03")));
        Check("unknown patient has empty history", () => { var p = q.Search(99999, new()); Require(p.Total == 0 && p.Page == 1 && p.Rows.Count == 0); });
        Check("other patient query remains isolated", () => { var p = q.Search(202, new()); Require(p.Total == 1 && p.Rows.Single().PkChildExaminationId == 1026); });
        Check("filter count before paging and page clamp", () => { var p = q.Search(101, new() { States = [ExaminationState.NotExamined], Page = 3 }); Require(p.Total == 6 && p.Page == 1 && p.Rows.Count == 6 && p.First == 1 && p.Last == 6); });
        Check("default page and range", () => { var p = q.Search(101, new()); Require(p.Rows.Count == 10 && p.Total == 24 && p.First == 1 && p.Last == 10 && p.Pages == 3); });
        Check("last page", () => { var p = q.Search(101, new() { Page = 3 }); Require(p.Rows.Count == 4 && p.First == 21 && p.Last == 24); });
        Check("positive page clamped", () => Require(q.Search(101, new() { Page = int.MaxValue }).Page == 3));
        Check("negative page clamped", () => Require(q.Search(101, new() { Page = int.MinValue }).Page == 1));
        Check("invalid size defaults", () => Require(q.Search(101, new() { PageSize = 0 }).PageSize == 10));
        foreach (var size in new[] { 10, 25, 50 })
            Check("allowed page size " + size, () => Require(q.Search(101, new() { PageSize = size }).Rows.Count == Math.Min(24, size)));
        Check("stable ordering and null recorded dates", () => Require(all.Rows.Select(r => r.PkChildExaminationId).SequenceEqual(new long[] {1024,1023,1022,1021,1019,1020,1018,1017,1016,1015,1013,1014,1012,1011,1010,1009,1007,1008,1006,1005,1004,1003,1001,1002})));
        Check("absent recorded date remains null and renders explicitly", () => {
            var absent = q.Detail(101, 1003);
            Require(Kd03ResultsQuery.RecordedDate(absent) == null);
            Require((Kd03ResultsQuery.RecordedDate(absent)?.ToString("yyyy-MM-dd") ?? "Not recorded") == "Not recorded");
            Require(Kd03ResultsQuery.RecordedDate(q.Detail(101, 1001))?.ToString("yyyy-MM-dd") == "2025-03-02");
        });
        Check("shared legacy getter still throws for stored null", () => {
            var legacy = new Orvex.TransferObjects.KdpExaminationResultTO { ResultEnteredDate = null };
            try { _ = legacy.ResultEnteredDate; }
            catch (NullReferenceException) { return; }
            throw new Exception("Legacy stored-null getter behaviour changed");
        });
        Check("query date adapter preserves populated legacy value", () => {
            var legacy = new Orvex.TransferObjects.KdpExaminationResultTO { ResultEnteredDate = new DateTime(2025, 3, 2) };
            Require(Kd03ResultsQuery.RecordedDate(legacy) == legacy.ResultEnteredDate);
        });
        Check("equal date recorded date ID tie break", () => { var rows = all.Rows.Where(r => r.PkChildExaminationId is 1004 or 1005).ToArray(); Require(rows.Length == 2 && rows[0].ExaminationDate == rows[1].ExaminationDate && rows[0].ResultEnteredDate == rows[1].ResultEnteredDate && rows[0].PkChildExaminationId == 1005); });
        Check("pages disjoint and complete", () => Require(Enumerable.Range(1, 3).SelectMany(p => q.Search(101, new() { Page = p }).Rows).Select(r => r.PkChildExaminationId).SequenceEqual(all.Rows.Select(r => r.PkChildExaminationId))));
        Check("AND categories OR values", () => { var p = q.Search(101, new() { States = [ExaminationState.Recorded], Repeats = [true], Locations = ["A", "B"], Examiners = ["X"] }); Require(p.Total == 2 && p.Rows.Select(r => r.PkChildExaminationId).Order().SequenceEqual(new long[] {1006,1018})); });
        Check("OR within states and repeats", () => Require(q.Search(101, new() { States = [ExaminationState.Recorded, ExaminationState.NotExamined], Repeats = [true, false] }).Total == 24));
        Check("not examined facet", () => Require(q.Search(101, new() { States = [ExaminationState.NotExamined] }).Total == 6));
        Check("inclusive date boundaries", () => Require(q.Search(101, new() { From = new(2025,2,2), To = new(2025,2,3) }).Total == 6));
        Check("reversed dates empty", () => Require(q.Search(101, new() { From = new(2025,2,3), To = new(2025,2,2) }).Total == 0));
        Check("empty range safe", () => { var p = q.Search(101, new() { Locations = ["unavailable"], Page = 999 }); Require(p.Total == 0 && p.Page == 1 && p.First == 0 && p.Last == 0 && p.Rows.Count == 0); });
        foreach (var finding in Enum.GetValues<PhysicalFinding>())
            Check("physical finding " + finding, () => Require(q.Search(101, new() { Findings = [finding] }).Total == 8));
        Check("OR physical findings", () => Require(q.Search(101, new() { Findings = [PhysicalFinding.Satisfactory, PhysicalFinding.Concern] }).Total == 16));
        Check("physical concern excludes social fields", () => Require(!Kd03ResultsQuery.HasConcern(new() { RskFamilyHealth = 2, DomesticViolenceConcern = 2, Development = 2 })));
        foreach (var field in new[] { "Heart", "Hips", "Eyes", "Testes", "PhysicalGeneral" })
            Check("concern includes " + field, () => { var r = new Orvex.TransferObjects.KdpExaminationResultTO(); r.GetType().GetProperty(field).SetValue(r, (byte?)2); Require(Kd03ResultsQuery.HasConcern(r)); });
        Check("safe detail missing other patient unsupported contact", () => Require(q.Detail(101, 99999) == null && q.Detail(101, 1026) == null && q.Detail(101, 1025) == null && q.Detail(99999, 1001) == null));
        Check("detail fresh read with complete values", () => { var r = q.Detail(101,1001); Require(r.Heart == 2 && r.RskFamilyHealth == 2); r.Heart = 3; Require(q.Detail(101,1001).Heart == 2); });
        Check("queries do not mutate storage", () => { store.Reload(); Require(store.Snapshot().ToJsonString() == before); });
        var repo = new SummaryRepository(); var summary = new PatientSummaryQuery(repo);
        Check("summary approved formatting", () => { var s = summary.Read(101); Require(s.FullName == "Synthetic, Baby" && s.Address == "1 Synthetic Road, TEST" && s.Age == "7 weeks" && s.Organisation == "-" && !s.ShowAlert); });
        Check("summary isolation", () => Require(summary.Read(202) == null));
        Check("summary rejects mis-scoped repository response", () => Require(new PatientSummaryQuery(new MisScopedSummaryRepository(repo.Patient)).Read(202) == null));
        Check("summary child alert", () => { repo.Patient.ChildAlertCodes.Add(new() { AlertCodes = new() { AlertText = "Synthetic alert" } }); var s = summary.Read(101); Require(s.ShowAlert && s.Alerts.Single() == "Synthetic alert"); repo.Patient.ChildAlertCodes.Clear(); });
        Check("summary status alert and age at death", () => { repo.Patient.CurrentStatus = C.LookupsUtility.CurrentStatus_Died; repo.Patient.DateOfDeath = new(2025,1,2); var s = summary.Read(101); Require(s.ShowAlert && s.Age == "1 day"); });
        var failed = results.Count(r => JsonSerializer.SerializeToNode(r)["status"].GetValue<string>() == "failed");
        Console.WriteLine(JsonSerializer.Serialize(new { total = results.Count, passed = results.Count - failed, failed, skipped = 0, results }, new JsonSerializerOptions { WriteIndented = true }));
        return failed == 0 && results.Count > 0 ? 0 : 1;
    }
}
