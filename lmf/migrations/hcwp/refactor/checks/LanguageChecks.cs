using System.Text.Json;
using Hcwp.Presentation;

internal static class LanguageChecks
{
    public static int Run(string inventoryPath)
    {
        var checks = new List<object>();
        void Check(string name, Action action)
        {
            try { action(); checks.Add(new { name, status = "passed" }); }
            catch (Exception e) { checks.Add(new { name, status = "failed", error = e.Message }); }
        }
        void Require(bool value) { if (!value) throw new Exception("Assertion failed"); }
        var json = File.ReadAllText(inventoryPath);
        var inventory = JsonSerializer.Deserialize<Dictionary<string, string>>(json);
        Check("Reviewable nonempty draft translations", () => Require(inventory.Count > 150 && inventory.All(p => !string.IsNullOrWhiteSpace(p.Value))));
        var language = new InterfaceLanguage(json);
        Check("English default and unsupported language fallback", () => {
            Require(language.Text("Patient summary") == "Patient summary");
            language.Select("fr"); Require(language.Code == "en");
        });
        Check("Welsh product copy and event without recreation", () => {
            int changed = 0; language.Changed += () => changed++;
            language.Select("cy"); language.Select("cy");
            Require(changed == 1 && language.Text("Patient summary") == "Crynodeb y claf");
        });
        Check("Missing and blank Welsh fall back to English", () => {
            Require(language.Text("Unlisted English") == "Unlisted English");
            var missing = new InterfaceLanguage("{\"English fallback\":\"\"}"); missing.Select("cy");
            Require(missing.Text("English fallback") == "English fallback");
        });
        Check("Unresolved legacy identities stay unchanged", () => Require(language.Text("NoResultsEnteredMessage") == "NoResultsEnteredMessage"));
        Check("All form labels and lookup descriptions inventoried", () => {
            foreach (var field in RecordingFields.All)
            {
                Require(inventory.ContainsKey(field.Label));
                Require(inventory.ContainsKey(ResultDisplay.Label(field)));
                foreach (var option in field.Options ?? []) Require(inventory.ContainsKey(option.Split('|')[1]));
            }
            foreach (var group in ResultDisplay.Groups) Require(inventory.ContainsKey(group.Title));
        });
        Check("Localized ranges preserve numeric values", () => Require(language.Format("Showing {0}–{1} of {2} results.", 11, 20, 23) == "Yn dangos 11–20 o 23 canlyniad."));
        var failed = checks.Count(c => JsonSerializer.Serialize(c).Contains("\"failed\""));
        Console.WriteLine(JsonSerializer.Serialize(new { total = checks.Count, passed = checks.Count - failed, failed, skipped = 0, checks }));
        return failed == 0 ? 0 : 1;
    }
}
