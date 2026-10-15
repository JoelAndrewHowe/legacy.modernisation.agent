using Hcwp.Components;
using Hcwp.Application;
using Hcwp.Persistence;
using Hcwp.Presentation;
using System.Text.Json.Nodes;

var builder = WebApplication.CreateBuilder(args);
// This bounded local demo also serves build-time assets when dotnet run defaults to Production.
builder.WebHost.UseStaticWebAssets();
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
var fixtures = JsonNode.Parse(File.ReadAllText(Path.Combine(builder.Environment.ContentRootPath, "demo-fixtures.json"))).AsObject();
ReferenceClock.Now = DateTime.Parse((string)fixtures["clock"]["now"]);
var store = DemoData.Seed(fixtures);
if (builder.Configuration.GetValue("DemoHistory", true))
    DemoHistory.Seed(store, File.ReadAllText(Path.Combine(builder.Environment.ContentRootPath, "synthetic-history.json")));
using (store.Open()) { }
builder.Services.AddSingleton(store);
builder.Services.AddSingleton<Kd03Recording>();
builder.Services.AddSingleton<Kd03ResultsQuery>();
builder.Services.AddSingleton<IPatientSummaryRepository>(new DemoPatientSummaryRepository(
    File.ReadAllText(Path.Combine(builder.Environment.ContentRootPath, "patient-summary-fixtures.json"))));
builder.Services.AddSingleton<PatientSummaryQuery>();
builder.Services.AddSingleton(new LookupDouble(fixtures));
builder.Services.AddScoped<RecordingPageModel>();
var app = builder.Build();
app.UseAntiforgery();
app.MapStaticAssets();
app.MapRazorComponents<App>().AddInteractiveServerRenderMode();
app.Run();
