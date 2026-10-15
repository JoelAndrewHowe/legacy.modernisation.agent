using Orvex.TransferObjects;

namespace Hcwp.Application;

public enum ExaminationState { Recorded, NotExamined }
public enum PhysicalFinding { Satisfactory = 1, Concern = 2, NotAssessed = 3, HasConcern = 4 }
public sealed record ResultsFilter
{
    public ExaminationState[] States { get; init; } = [];
    public bool[] Repeats { get; init; } = [];
    public PhysicalFinding[] Findings { get; init; } = [];
    public DateOnly? From { get; init; }
    public DateOnly? To { get; init; }
    public string[] Locations { get; init; } = [];
    public string[] Examiners { get; init; } = [];
    public int Page { get; init; } = 1;
    public int PageSize { get; init; } = 10;
}
public sealed record ResultsPage(IReadOnlyList<KdpExaminationResultTO> Rows, int Total, int Page, int PageSize)
{
    public int Pages => Math.Max(1, (int)Math.Ceiling((double)Total / PageSize));
    public int First => Total == 0 ? 0 : (Page - 1) * PageSize + 1;
    public int Last => Total == 0 ? 0 : First + Rows.Count - 1;
}

// Patient scoping is mandatory for both overview and detail. Storage reads and
// mapping remain behind this application boundary, never in a Razor component.
public sealed class Kd03ResultsQuery(Kd03Recording recording)
{
    // Presentation-only nullable-date adapter. Do not invoke or alter the shared
    // legacy getter: it unboxes stored null as DateTime and throws.
    public static DateTime? RecordedDate(KdpExaminationResultTO result) =>
        (DateTime?)result.getProperty(KdpExaminationResultTO.PropertyNames.ResultEnteredDate);

    public static byte?[] PhysicalValues(KdpExaminationResultTO r) => [r.Heart, r.Hips, r.Eyes, r.Testes, r.PhysicalGeneral];
    public static bool HasConcern(KdpExaminationResultTO r) => PhysicalValues(r).Contains((byte)2);
    IEnumerable<KdpExaminationResultTO> Read(long patient) => recording.ReadResults(patient)
        .Where(r => r.ClientId == patient && r.ExaminationCode == "KD03");

    public KdpExaminationResultTO Detail(long selectedPatient, long resultId) => Read(selectedPatient)
        .SingleOrDefault(r => r.PkChildExaminationId == resultId);

    public ResultsPage Search(long selectedPatient, ResultsFilter filter)
    {
        ArgumentNullException.ThrowIfNull(filter);
        // URL parsing/error summaries belong to presentation. This boundary fails
        // safely even if called directly with an unsupported page size or page.
        var size = filter.PageSize is 10 or 25 or 50 ? filter.PageSize : 10;
        var query = Read(selectedPatient)
            .Where(r => filter.States.Length == 0 || filter.States.Contains(r.ReasonNotExamined == null ? ExaminationState.Recorded : ExaminationState.NotExamined))
            .Where(r => filter.Repeats.Length == 0 || filter.Repeats.Contains(r.IsRepeat))
            .Where(r => filter.Findings.Length == 0 || filter.Findings.Any(f => f == PhysicalFinding.HasConcern ? HasConcern(r) : PhysicalValues(r).Contains((byte)f)))
            .Where(r => !filter.From.HasValue || DateOnly.FromDateTime(r.ExaminationDate) >= filter.From.Value)
            .Where(r => !filter.To.HasValue || DateOnly.FromDateTime(r.ExaminationDate) <= filter.To.Value)
            .Where(r => filter.Locations.Length == 0 || filter.Locations.Contains(r.LocationCode))
            .Where(r => filter.Examiners.Length == 0 || filter.Examiners.Contains(r.ExaminerHcpCode))
            .OrderByDescending(r => r.ExaminationDate).ThenByDescending(RecordedDate).ThenByDescending(r => r.PkChildExaminationId)
            .ToList();
        var pages = Math.Max(1, (int)Math.Ceiling((double)query.Count / size));
        var page = Math.Clamp(filter.Page, 1, pages);
        return new(query.Skip((page - 1) * size).Take(size).ToList().AsReadOnly(), query.Count, page, size);
    }
}
