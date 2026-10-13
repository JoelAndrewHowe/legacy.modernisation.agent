using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Storage;
using Orvex.Model;

namespace Hcwp.Persistence;

// Actual EF entities, not a JSON document store. Navigations are assembled by
// Store.Link after loading scalar rows, retaining the reviewed mapping boundary.
public sealed class RecordingContext(DbContextOptions<RecordingContext> options) : DbContext(options)
{
    public static readonly Type[] EntityTypes =
    [
        typeof(ChildGeneral), typeof(Consent), typeof(ExaminationDescriptions),
        typeof(ChildLocations), typeof(HealthCareProfessionals), typeof(Examiner),
        typeof(ExamNotExaminedReason), typeof(PreschoolScheduleExams),
        typeof(SystemGeneralOptions), typeof(DeviationsCentile),
        typeof(ChildExamination), typeof(ChildExaminationGiven),
        typeof(ChildExaminationKdp), typeof(ChildMeasurement)
    ];

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        foreach (var type in EntityTypes)
        {
            var entity = modelBuilder.Entity(type);
            foreach (var property in type.GetProperties())
            {
                if (!Store.Scalar(property.PropertyType)) entity.Ignore(property.Name);
            }
            // Synthetic storage identity also supports repeated operational fixture
            // rows without inventing unavailable Oracle keys or constraints.
            entity.Property<long>("StorageId").ValueGeneratedOnAdd();
            entity.HasKey("StorageId");
        }
    }
}

public sealed class RecordingDatabase
{
    private readonly InMemoryDatabaseRoot root = new();
    private readonly string name = Guid.NewGuid().ToString("N");
    public RecordingContext Open() => new(new DbContextOptionsBuilder<RecordingContext>()
        .UseInMemoryDatabase(name, root).Options);
}
