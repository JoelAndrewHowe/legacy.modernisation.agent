using System.Text.Json;
using Hcwp.Application;
using Converted = Hcwp.SystemFeel.Converted;

namespace Hcwp.Persistence;

// A separate synthetic graph, not a fabricated join to recording-only entities.
public sealed class DemoPatientSummaryRepository(string json) : IPatientSummaryRepository
{
    readonly JsonElement fixtures = JsonDocument.Parse(json).RootElement.Clone();
    public Converted.ChildGeneral Find(long selectedPatient) => ReadFixture("selected", selectedPatient);
    public Converted.ChildGeneral ReadFixture(string name, long selectedPatient)
    {
        var patient = fixtures.GetProperty(name).Deserialize<Converted.ChildGeneral>();
        return patient?.ClientId == selectedPatient ? patient : null;
    }
    public IEnumerable<Converted.ChildLocations> AuthorityLocations() =>
        fixtures.GetProperty("authorityLocations").Deserialize<List<Converted.ChildLocations>>();
}
