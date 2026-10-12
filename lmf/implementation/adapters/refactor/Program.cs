using Microsoft.EntityFrameworkCore;
using Hcwp.Components;

if (args.Length == 3 && args[0].EndsWith("scenarios.json"))
{
    SharedScenarios.Run(args);
    return;
}
if (args.Length == 2 && args[0] == "--persistence-check")
{
    PersistenceChecks.Run(args[1]);
    return;
}
var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseStaticWebAssets();
builder.Services.AddRazorComponents().AddInteractiveServerComponents();
builder.Services.AddDbContextFactory<RecordingContext>(options => options.UseInMemoryDatabase("synthetic-hcwp"));
builder.Services.AddSingleton<RecordingService>();
var app = builder.Build();
app.Services.GetRequiredService<RecordingService>().Seed();
app.UseAntiforgery();
app.MapStaticAssets();
app.MapRazorComponents<App>().AddInteractiveServerRenderMode();
app.Run();
