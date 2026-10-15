using Hcwp.Application;
using Hcwp.Persistence;
using Hcwp.Presentation;
using System.Text.Json;
using System.Text.Json.Nodes;

public static class HistoryChecks
{
    public static int Run(string fixturePath)
    {
        var results = new List<object>();
        void Check(string name, Action test)
        {
            try { test(); results.Add(new { name, status = "passed" }); }
            catch (Exception e) { results.Add(new { name, status = "failed", error = e.ToString() }); }
        }
        void Require(bool ok) { if (!ok) throw new Exception("History assertion failed"); }
        var f = JsonNode.Parse(File.ReadAllText(fixturePath)).AsObject();
        var store = DemoData.Seed(f);
        DemoHistory.Seed(store, File.ReadAllText(Path.Combine(Path.GetDirectoryName(fixturePath), "synthetic-history.json")));
        using (store.Open()) { }
        var q = new Kd03ResultsQuery(new(store));
        var choices = q.Choices(101);
        var before = store.Snapshot().ToJsonString();
        ResultsUrlState Parse(string query) => ResultsUrlState.Parse("http://localhost/results?" + query, choices);
        Check("default demonstration has 23 selected results and three pages", () => Require(q.Search(101, new()).Total == 23 && q.Search(101, new()).Pages == 3 && q.Search(101, new() { Page = 3 }).Rows.Count == 3));
        Check("other patient retained and inaccessible from selected details", () => Require(q.Search(202, new()).Total == 1 && q.Detail(101, 8024) == null && q.Detail(101, 9999) == null));
        Check("lookup descriptions only from selected history", () => Require(choices.Locations.Length == 2 && choices.Examiners.Length == 2 && choices.Locations.All(c => c.Description.StartsWith("Synthetic"))));
        Check("URL all facets round trip and multiple OR selections", () =>
        {
            var state = Parse("state=Recorded&state=NotExamined&repeat=initial&repeat=repeat&finding=Concern&finding=HasConcern&location=HISTA&location=HISTB&examiner=HISTX&from=2025-01-02&to=2025-01-08&page=2&size=25");
            var round = ResultsUrlState.Parse("http://localhost" + ResultsUrlState.Url(state.Filter), choices);
            Require(state.Notices.Length == 0 && round.Notices.Length == 0 && ResultsUrlState.Url(state.Filter) == ResultsUrlState.Url(round.Filter) && round.Filter.States.Length == 2 && round.Filter.Findings.Length == 2 && round.Filter.Page == 2 && round.Filter.PageSize == 25);
        });
        Check("invalid enum numeric injection and unavailable lookups ignored", () =>
        {
            var state = Parse("state=9&state=Recorded&finding=999&repeat=wat&location=OTHERPATIENT&examiner=unknown&page=2147483648&size=11&from=bad&to=2025-02-30");
            Require(state.Notices.Length == 9 && state.Filter.States.SequenceEqual(new[] { ExaminationState.Recorded }) && state.Filter.Findings.Length == 0 && state.Filter.Locations.Length == 0 && state.Filter.Examiners.Length == 0 && state.Filter.Page == 1 && state.Filter.PageSize == 10 && state.Filter.From == null && state.Filter.To == null);
        });
        Check("duplicate and reversed range safe", () => { var s = Parse("state=Recorded&state=Recorded&from=2025-02-01&to=2025-01-01"); Require(s.Filter.States.Length == 1 && s.Filter.From == null && s.Filter.To == null && s.Notices.Length == 2); });
        Check("unknown query cannot inject return location", () => Require(ResultsUrlState.Url(Parse("returnUrl=https://evil.invalid&patient=202").Filter).StartsWith("/results?size=10&page=1")));
        Check("omitted page resets after filter and size submission", () => Require(Parse("finding=Concern&size=50").Filter.Page == 1));
        Check("inclusive history boundaries", () => Require(q.Search(101, Parse("from=2025-01-02&to=2025-01-03").Filter).Total == 6));
        Check("combined filters AND and physical facets OR", () =>
        {
            var p = q.Search(101, Parse("state=Recorded&repeat=repeat&finding=Concern&finding=Satisfactory&location=HISTA&examiner=HISTX").Filter);
            Require(p.Total == 2 && p.Rows.All(r => r.ClientId == 101 && !string.IsNullOrEmpty(r.LocationName)));
        });
        Check("empty and excessive page resolve without disclosure", () => { var p = q.Search(101, Parse("from=2099-01-01&page=999").Filter); Require(p.Total == 0 && p.Page == 1 && p.First == 0); Require(q.Search(101, Parse("page=999").Filter).Page == 3); });
        Check("complete detail inventory grouped exactly once", () => Require(ResultDisplay.Groups.SelectMany(g => g.Properties).Order().SequenceEqual(RecordingFields.All.Select(f => f.Property).Order())));
        Check("every detail field render is explicit with no raw lookup codes", () =>
        {
            foreach (var r in q.Search(101, new() { PageSize = 50 }).Rows)
                foreach (var field in RecordingFields.All) Require(!string.IsNullOrWhiteSpace(ResultDisplay.Field(r, field)) && !ResultDisplay.Field(r, field).Contains("HIST"));
        });
        Check("unknown saved lookup value uses honest fallback", () => Require(ResultDisplay.Field(new() { Heart = 99 }, RecordingFields.All.Single(f => f.Property == "Heart")) == "Description unavailable"));
        Check("calculated BMI matches approved bounded display", () => Require(ResultDisplay.Bmi(new() { Height = 60, Weight = 6 }) == 16.67m && ResultDisplay.Bmi(new()) == null));
        Check("read filters details do not change persistence", () => { store.Reload(); Require(before == store.Snapshot().ToJsonString()); });
        var failed = results.Count(r => JsonSerializer.SerializeToNode(r)["status"].GetValue<string>() == "failed");
        Console.WriteLine(JsonSerializer.Serialize(new { total = results.Count, passed = results.Count - failed, failed, skipped = 0, results }, new JsonSerializerOptions { WriteIndented = true }));
        return failed == 0 ? 0 : 1;
    }
}
