using Hcwp.Components;
using Hcwp.Application;
using Hcwp.Persistence;
using Hcwp.Presentation;
using System.Text.Json.Nodes;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
var fixtures = JsonNode.Parse(File.ReadAllText(Path.Combine(builder.Environment.ContentRootPath, "demo-fixtures.json"))).AsObject();
ReferenceClock.Now = DateTime.Parse((string)fixtures["clock"]["now"]);
var store = DemoData.Seed(fixtures);
using (store.Open()) { }
builder.Services.AddSingleton(store);
builder.Services.AddSingleton<Kd03Recording>();
builder.Services.AddScoped<RecordingPageModel>();
var app = builder.Build();
app.UseAntiforgery();
app.MapStaticAssets();
app.MapRazorComponents<App>().AddInteractiveServerRenderMode();
app.Run();
