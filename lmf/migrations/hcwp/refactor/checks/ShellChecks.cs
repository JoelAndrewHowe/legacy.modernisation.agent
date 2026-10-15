using System.Text.Json;
using Hcwp.Application;
using Hcwp.Components;
using Hcwp.Persistence;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

public static class ShellChecks
{
    sealed class AlertRepository(DemoPatientSummaryRepository repository) : IPatientSummaryRepository
    {
        public Hcwp.SystemFeel.Converted.ChildGeneral Find(long id) => repository.ReadFixture("alert", id);
        public IEnumerable<Hcwp.SystemFeel.Converted.ChildLocations> AuthorityLocations() => repository.AuthorityLocations();
    }
    public static async Task<int> Run(string fixturePath, string browserFixturePath = null)
    {
        var checks = new List<object>();
        async Task Check(string name, Func<Task> test)
        {
            try { await test(); checks.Add(new { name, status = "passed" }); }
            catch (Exception error) { checks.Add(new { name, status = "failed", error = error.ToString() }); }
        }
        void Require(bool value) { if (!value) throw new InvalidOperationException("Shell assertion failed"); }
        ReferenceClock.Now = new DateTime(2025, 3, 15);
        var repository = new DemoPatientSummaryRepository(File.ReadAllText(fixturePath));
        var services = new ServiceCollection().AddLogging().BuildServiceProvider();
        await using var renderer = new HtmlRenderer(services, services.GetRequiredService<ILoggerFactory>());
        Task<string> Render(PatientSummary patient) => renderer.Dispatcher.InvokeAsync(async () =>
            (await renderer.RenderComponentAsync<PatientBanner>(ParameterView.FromDictionary(new Dictionary<string, object> { ["Patient"] = patient }))).ToHtmlString());
        var query = new PatientSummaryQuery(repository);
        await Check("synthetic selected-patient graph and isolation", async () =>
        {
            Require(query.Read(202) == null && query.Read(999) == null);
            var html = await Render(query.Read(101));
            foreach (var label in new[] { "Full name", "NHS number", "Date of birth", "Age", "Sex", "Address", "Current status", "School", "Health board", "SYN-NHS-101", "Synthetic School One", "Cardiff and Vale University Health Board" }) Require(html.Contains(label));
            Require(!html.Contains("ClientId") && !html.Contains("Patient ID") && !html.Contains("Organisation") && !html.Contains("Synthetic Organisation One") && !html.Contains("Synthetic nonauthority sentinel"));
        });
        await Check("no-alert fixture has no empty alert announcement", async () =>
        {
            var html = await Render(query.Read(101));
            Require(!html.Contains("role=\"alert\"") && !html.Contains("patient-alert-title"));
        });
        await Check("alert fixture renders prominent named alert and every text", async () =>
        {
            var html = await Render(new PatientSummaryQuery(new AlertRepository(repository)).Read(101));
            Require(html.Contains("role=\"alert\"") && html.Contains("aria-labelledby=\"patient-alert-title\""));
            Require(html.Contains("SYNTHETIC CHILD ALERT") && html.Contains("SYNTHETIC SECOND ALERT") && !html.Contains("OTHER-PATIENT"));
            Require(html.Contains("Health board") && html.Contains("Cardiff and Vale University Health Board") && !html.Contains("Organisation"));
        });
        await Check("missing context fails visibly without other patient data", async () =>
        {
            var html = await Render(null);
            Require(html.Contains("Selected patient context unavailable") && !html.Contains("SYN-NHS"));
        });
        if (browserFixturePath != null)
        {
            // Test-only document: real component + approved alert graph, never a product route/switch.
            var banner = await Render(new PatientSummaryQuery(new AlertRepository(repository)).Read(101));
            File.WriteAllText(browserFixturePath, "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"><link rel=\"stylesheet\" href=\"/vendor/nhsw/nhsw.min.css\"><title>Alert fixture presentation harness</title></head><body><main class=\"nhsw-main-wrapper\"><div class=\"nhsw-width-container\">" + banner + "</div></main></body></html>");
        }
        var failed = checks.Count(x => JsonSerializer.SerializeToElement(x).GetProperty("status").GetString() == "failed");
        Console.WriteLine(JsonSerializer.Serialize(new { total = checks.Count, passed = checks.Count - failed, failed, skipped = 0, results = checks }));
        return failed == 0 ? 0 : 1;
    }
}
