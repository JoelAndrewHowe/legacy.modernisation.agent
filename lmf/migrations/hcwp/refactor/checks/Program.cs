using System.Security.Cryptography;
using System.Text.Json;
using System.Text.Json.Nodes;

if (args.Length == 2 && args[0] == "--language") return LanguageChecks.Run(args[1]);
if (args.Length == 2 && args[0] == "--history") return HistoryChecks.Run(args[1]);
if (args.Length == 2 && args[0] == "--shell") return await ShellChecks.Run(args[1]);
if (args.Length == 3 && args[0] == "--shell-browser-fixture") return await ShellChecks.Run(args[1], args[2]);
if (args.Length == 1 && args[0] == "--system-feel-observe") return QueryChecks.ObserveApprovedSystemFeel();
if (args.Length == 2 && args[0] == "--queries") return QueryChecks.Run(args[1]);
if (args.Length == 2 && args[0] == "--flow") return FlowChecks.Run(args[1]);
if (args.Length == 2 && args[0] == "--persistence") return ArchitectureChecks.Run(args[1]);
if (args.Length < 2) { Console.Error.WriteLine("Usage: Checks <approved-scenario-directory> <evidence-directory> [--observe-only] [scenario-id]"); return 2; }
var dir = Path.GetFullPath(args[0]);
var fixtures = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "fixtures.json"))).AsObject();
var suite = JsonNode.Parse(File.ReadAllText(Path.Combine(dir, "scenarios.json"))).AsObject();
var observeOnly = args.Skip(2).Contains("--observe-only"); var filter = args.Skip(2).FirstOrDefault(a => !a.StartsWith("--"));
var results = new JsonArray(); var passes = 0; var failures = 0;
var ids = new HashSet<string>();
foreach (var node in suite["scenarios"].AsArray())
{
    var s = node.AsObject(); var id = (string)s["id"];
    if (filter != null && id != filter) continue;
    var differences = new List<string>(); JsonObject observations = null;
    try
    {
        if (!ids.Add(id) || s["required"]?.GetValue<bool>() != true) throw new InvalidDataException("Duplicate or nonrequired scenario");
        // The adapter receives inputs only, never the expected outcome.
        var input = (JsonObject)s.DeepClone(); input.Remove("expected");
        observations = ScenarioAdapter.Execute(fixtures, input);
        if (!observeOnly)
        {
            var expected = Resolve(fixtures, s["expected"].AsObject());
            Compare(expected, observations, "", differences);
        }
    }
    catch (Exception ex) { differences.Add(ex.ToString()); }
    var status = differences.Count > 0 ? "failed" : observeOnly ? "observed" : "passed";
    if (status == "failed") failures++; else if (status == "passed") passes++;
    var result = new JsonObject { ["id"] = id, ["status"] = status, ["observations"] = observations, ["differences"] = new JsonArray(differences.Select(d => (JsonNode)JsonValue.Create(d)).ToArray()) };
    results.Add(result); Console.WriteLine(result.ToJsonString());
}
if (results.Count == 0) failures++;
var report = new JsonObject { ["schemaVersion"] = 1, ["claim"] = "parity with extracted legacy logic; not the original Windows/Oracle system", ["sourceSha256"] = fixtures["source"]["sha256"].DeepClone(), ["fixtureSha256"] = Hash("fixtures.json"), ["scenarioSha256"] = Hash("scenarios.json"), ["mode"] = observeOnly ? "observe-only" : "verify", ["selectedScenario"] = filter, ["total"] = results.Count, ["passed"] = passes, ["failed"] = failures, ["skipped"] = 0, ["results"] = results };
var evidence = Path.GetFullPath(args[1]); Directory.CreateDirectory(evidence);
var filename = (observeOnly ? "observations" : "results") + (filter == null ? "" : "." + filter) + ".json";
File.WriteAllText(Path.Combine(evidence, filename), report.ToJsonString(new JsonSerializerOptions { WriteIndented = true }) + "\n");
Console.WriteLine(new JsonObject { ["total"] = results.Count, ["passed"] = passes, ["failed"] = failures, ["skipped"] = 0 }.ToJsonString());
return failures == 0 ? 0 : 1;

string Hash(string name) => Convert.ToHexStringLower(SHA256.HashData(File.ReadAllBytes(Path.Combine(dir, name))));
static JsonObject Resolve(JsonObject f, JsonObject definition)
{
    var expected = definition["base"] is { } b ? (JsonObject)f["observationDefaults"][(string)b].DeepClone() : new JsonObject();
    foreach (var (k, v) in definition) if (k is not "base" and not "savedFixture" and not "savedOverrides") expected[k] = v?.DeepClone();
    if (definition["savedFixture"] is { } name)
    {
        var saved = (JsonObject)f["savedProjections"][(string)name].DeepClone();
        if (definition["savedOverrides"] is JsonObject overrides) foreach (var (k, v) in overrides) saved[k] = v?.DeepClone();
        expected["savedValues"] = saved;
    }
    return expected;
}
static void Compare(JsonNode expected, JsonNode actual, string path, List<string> differences)
{
    if (expected is JsonObject o)
    {
        if (actual is not JsonObject a) { differences.Add(path + ": expected object, got " + actual); return; }
        foreach (var (k, v) in o)
        {
            if (!a.ContainsKey(k)) differences.Add(path + "." + k + ": missing observation");
            else Compare(v, a[k], path + "." + k, differences);
        }
    }
    else if (path == ".unchangedPatients" && expected is JsonArray patients && actual is JsonArray unchanged)
    {
        foreach (var p in patients) if (!unchanged.Any(v => JsonNode.DeepEquals(p, v))) differences.Add(path + ": changed patient " + p);
    }
    else if (!JsonNode.DeepEquals(expected, actual)) differences.Add(path + ": expected " + (expected?.ToJsonString() ?? "null") + ", got " + (actual?.ToJsonString() ?? "null"));
}
