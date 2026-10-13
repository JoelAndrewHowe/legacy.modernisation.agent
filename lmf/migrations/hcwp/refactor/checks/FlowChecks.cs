using Hcwp.Application;
using Hcwp.Persistence;
using Hcwp.Presentation;
using System.Text.Json;
using System.Text.Json.Nodes;

public static class FlowChecks
{
    public static int Run(string fixturePath)
    {
        var f = JsonNode.Parse(File.ReadAllText(fixturePath)).AsObject();
        ReferenceClock.Now = DateTime.Parse((string)f["clock"]["now"]);
        var results = new List<object>();
        void Check(string name, Action action)
        {
            try { action(); results.Add(new { name, status = "passed" }); }
            catch (Exception ex) { results.Add(new { name, status = "failed", error = ex.ToString() }); }
        }
        void Require(bool ok, string message) { if (!ok) throw new Exception(message); }
        (Store, RecordingPageModel) Setup() { var s = DemoData.Seed(f); return (s, new(new Kd03Recording(s), new LookupDouble(f))); }
        Check("full fixture browser model save and fresh read", () =>
        {
            var (s, m) = Setup();
            foreach (var (key, value) in f["drafts"]["full"].AsObject()) DemoData.Set(m.Draft, key, value);
            m.Save(); Require(m.Saved && m.Error == null, m.Error ?? "Save rejected");
            var saved = m.Results.Single();
            foreach (var (key, expected) in f["savedProjections"]["full"].AsObject())
                Require(JsonNode.DeepEquals(JsonSerializer.SerializeToNode(saved.GetType().GetProperty(key).GetValue(saved)), expected), "Mismatch " + key);
            m.Draft.Heart = 3; m.Reload(); Require(m.Results.Single().Heart == 1, "Echoed draft");
            Require(new Kd03Recording(s).ReadPatient(202).HcpExaminationResultToList.Count == 0, "Changed other patient");
        });
        Check("invalid save and field rejection do not persist", () =>
        {
            var (s, m) = Setup(); var before = s.Snapshot();
            m.Save(); Require(!m.Saved && m.Error.Contains("NoResultsEnteredMessage"), "Missing no-results error");
            m.Heart = 1; m.Set("Height", "0"); m.Save();
            Require(!m.Saved && m.Error.Contains("InvalidHeightMessage"), "Invalid height accepted");
            m.Set("Height", ""); m.Set("HeadCircumference", "150"); m.Save();
            Require(!m.Saved && m.Error.Contains("HeadCircumferenceInvalidFormatMessage"), "Head field limit lost");
            s.Reload(); Require(JsonNode.DeepEquals(before, s.Snapshot()), "Rejected inputs changed storage");
        });
        Check("explicit duplicate confirmation no/yes and same-day rejection", () =>
        {
            var (s, m) = Setup(); m.Heart = 1; m.Save(); Require(m.Saved, "First save failed");
            m.NewResult(); m.Date = new(2025, 2, 20); m.Heart = 2; m.Save();
            Require(m.Pending != null && !m.Saved && m.Results.Count == 1, "Did not await confirmation");
            m.Confirm(false); Require(!m.Saved && m.Results.Count == 1, "No saved result");
            m.Save(); m.Confirm(true); Require(m.Saved && m.Results.Count == 2 && m.Results[0].IsRepeat, "Yes failed");
            m.NewResult(); m.Date = new(2025, 2, 20); m.Heart = 1; m.Save();
            Require(m.Pending == null && !m.Saved && m.Error.Contains("KdpResultAlreadyEnteredMessage"), "Same-day accepted");
        });
        Check("warning and declined behaviour retained", () =>
        {
            var (_, m) = Setup(); m.Date = new(2025, 3, 14); m.Heart = 1;
            m.Set("Height", "60"); m.Set("HeightMeasurementDeclined", "Y"); Require(m.Draft.Height == null, "Yes did not clear");
            m.Set("Height", "60"); m.Set("HeightMeasurementDeclined", "N"); Require(m.Draft.Height == null, "No did not clear");
            m.Save(); Require(m.Saved && m.Messages.Any(x => x.Message == "KdpContactGivenAfterMaxAge"), "Age warning lost");
        });
        var failed = results.Count(r => JsonSerializer.SerializeToNode(r)["status"].GetValue<string>() == "failed");
        Console.WriteLine(JsonSerializer.Serialize(new { total = results.Count, passed = results.Count - failed, failed, skipped = 0, results }, new JsonSerializerOptions { WriteIndented = true }));
        return failed == 0 ? 0 : 1;
    }
}
