using Hcwp.Application;
using Hcwp.Persistence;
using Hcwp.Presentation;
using Orvex.Model;
using Orvex.TransferObjects;
using System.ServiceModel;
using System.Text.Json;
using System.Text.Json.Nodes;

public static class ArchitectureChecks
{
    public static int Run(string fixturePath)
    {
        var results = new List<object>();
        void Check(string name, Action action)
        {
            try { action(); results.Add(new { name, status = "passed" }); }
            catch (Exception ex) { results.Add(new { name, status = "failed", error = ex.ToString() }); }
        }
        void Require(bool condition, string error) { if (!condition) throw new InvalidOperationException(error); }
        var f = JsonNode.Parse(File.ReadAllText(fixturePath)).AsObject();
        ReferenceClock.Now = DateTime.Parse((string)f["clock"]["now"]);
        var store = DemoData.Seed(f);
        var recording = new Kd03Recording(store);
        KdpExaminationResultTO submitted = null, readBack = null;
        Check("fresh-context full-field read-back", () =>
        {
            submitted = new KdpExaminationResultTO { ClientId = 101, ResultEnteredDate = ReferenceClock.Now };
            foreach (var (key, value) in f["drafts"]["full"].AsObject()) DemoData.Set(submitted, key, value);
            readBack = recording.Add(101, submitted);
            Require(!ReferenceEquals(submitted, readBack), "Read-back echoed submitted object");
            var firstRead = recording.ReadPatient(101).HcpExaminationResultToList.Single();
            using var a = store.Open(); using var b = store.Open();
            var ea = a.Set<ChildExamination>().Single(); var eb = b.Set<ChildExamination>().Single();
            Require(!ReferenceEquals(ea, eb), "Contexts share tracked entities");
            submitted.Heart = 3; submitted.Height = 999;
            var secondRead = recording.ReadPatient(101).HcpExaminationResultToList.Single();
            Require(secondRead.Heart == 1 && secondRead.Height == 60 && firstRead.Heart == 1, "Draft mutation leaked into EF data");
            foreach (var (key, expected) in f["savedProjections"]["full"].AsObject())
            {
                var actual = JsonSerializer.SerializeToNode(secondRead.GetType().GetProperty(key).GetValue(secondRead));
                Require(JsonNode.DeepEquals(actual, expected), "Read-back mismatch: " + key);
            }
        });
        Check("invalid save leaves EF storage unchanged", () =>
        {
            var before = store.Snapshot();
            try { recording.Add(101, new() { ClientId = 101, ExaminationCode = "KD03", ExaminationDate = new(2025, 2, 20) }); throw new Exception("Invalid empty result accepted"); }
            catch (FaultException) { }
            store.Reload();
            Require(JsonNode.DeepEquals(before, store.Snapshot()), "Rejected submission changed persistence");
        });
        Check("KD03-only and selected-patient boundary", () =>
        {
            var before = store.Snapshot();
            foreach (var draft in new KdpExaminationResultTO[]
            {
                new() { ClientId = 101, ExaminationCode = "KD04" },
                new() { ClientId = 202, ExaminationCode = "KD03" },
                new() { ClientId = 101, ExaminationCode = "KD03", PkChildExaminationId = 9001 }
            })
            {
                try { recording.Add(101, draft); throw new Exception("Excluded submission accepted"); }
                catch (ArgumentException) { }
            }
            Require(JsonNode.DeepEquals(before, store.Snapshot()), "Scope rejection changed persistence");
            Require(recording.ReadPatient(202).HcpExaminationResultToList.Count == 0, "Another patient was changed");
        });
        Check("new presentation model reloads existing application data", () =>
        {
            var model = new RecordingPageModel(recording); model.Reload();
            Require(model.Results.Count == 1 && model.Results[0].ClientId == 101 && model.Results[0].Heart == 1, "Page reload lost saved data");
        });
        var failed = results.Count(r => JsonSerializer.SerializeToNode(r)["status"].GetValue<string>() == "failed");
        Console.WriteLine(JsonSerializer.Serialize(new { total = results.Count, passed = results.Count - failed, failed, skipped = 0, results }, new JsonSerializerOptions { WriteIndented = true }));
        return failed == 0 ? 0 : 1;
    }
}
