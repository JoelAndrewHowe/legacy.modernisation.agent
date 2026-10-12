using Microsoft.EntityFrameworkCore;

public class SavedRecording
{
    public long Id { get; set; }
    public long PatientId { get; set; }
    public string Data { get; set; }
}

public class RecordingContext(DbContextOptions<RecordingContext> options) : DbContext(options)
{
    public DbSet<SavedRecording> Recordings => Set<SavedRecording>();
}

public record SaveOutcome(bool Saved, string[] Errors, string[] Warnings, KdpExaminationResultTO ReadBack);

public class RecordingService(IDbContextFactory<RecordingContext> contexts)
{
    public const long SelectedPatient = 1001;
    public static readonly DateTime Birth = new(2025, 1, 1);
    private readonly object gate = new();

    public void Seed()
    {
        using var context = contexts.CreateDbContext();
        if (context.Recordings.Any()) return;
        var sibling = new KdpExaminationResultTO
        {
            ClientId = 2002,
            PkChildExaminationId = 1,
            ExaminationCode = "KD03",
            ExaminationDate = new(2025, 1, 2),
            IsRepeat = true,
            Heart = 1
        };
        context.Add(new SavedRecording { Id = 1, PatientId = 2002, Data = JsonSerializer.Serialize(sibling) });
        context.SaveChanges();
    }

    // Every read is detached and goes through a fresh persistence context.
    public List<KdpExaminationResultTO> Read(long patient = SelectedPatient)
    {
        using var context = contexts.CreateDbContext();
        return context.Recordings.AsNoTracking().Where(r => r.PatientId == patient).OrderBy(r => r.Id)
            .Select(r => r.Data).ToList().Select(data => JsonSerializer.Deserialize<KdpExaminationResultTO>(data)).ToList();
    }

    public KdpExaminationResultTO New() => new()
    {
        ClientId = SelectedPatient,
        ExaminationCode = "KD03",
        ExaminationDate = new(2025, 2, 20),
        Reschedule = "N",
        HeightMeasurementDeclined = "N",
        WeightMeasurementDeclined = "N",
        HeadMeasurementDeclined = "N",
        EnabledPropChangeEvents = true,
        Origin = 2,
        ResultEnteredDate = new(2025, 3, 1, 12, 0, 0)
    };

    public SaveOutcome Save(KdpExaminationResultTO supplied, bool confirmed = false)
    {
        lock (gate)
        {
            var errors = new List<string>();
            var dto = JsonSerializer.Deserialize<KdpExaminationResultTO>(JsonSerializer.Serialize(supplied));
            // Boundary checks precede any mutation of stored data.
            if (dto.ClientId != SelectedPatient) errors.Add("SelectedPatientRequired");
            if (dto.ExaminationCode != "KD03") errors.Add("UnsupportedContact");
            if (dto.PkChildExaminationId != 0) errors.Add("AddOnly");
            if (errors.Count > 0) return new(false, errors.ToArray(), [], null);
            var existing = Read();
            var rules = new ExtractedInteractions();
            rules.Populate(dto, "M", Birth, null, existing);
            rules.prescribedRanges = new(() => [new("BMI", 10, 25)]);
            if (dto.HeightMeasurementDeclined == "Y") rules.IsHeightDeclined = true;
            if (dto.WeightMeasurementDeclined == "Y") rules.IsWeightDeclined = true;
            if (dto.HeadMeasurementDeclined == "Y") rules.IsHeadCircumferenceDeclined = true;
            // Retain KD03 applicability and source field-validation path, not only save validation.
            dto.ExaminationCode = null;
            rules.ExamCodeValidated = true;
            rules.ExaminationCode = "KD03";
            rules.deviationRanges = new(() => [new("Height", 40, 60), new("Weight", 3, 6)]);
            rules.ValidateExaminationDate(dto.ExaminationDate);
            rules.ValidateHeight(dto.Height);
            rules.ValidateWeight(dto.Weight);
            if (dto.HeadCircumference.HasValue) rules.ValidateHeadCircumference(dto.HeadCircumference.Value);
            if (dto.Height > 0 && dto.Weight.HasValue)
                rules.CheckBmi(rules, new System.ComponentModel.PropertyChangedEventArgs(nameof(ExtractedInteractions.Bmi)));
            rules.ValidateLocationCode(dto.LocationCode);
            rules.ValidateExaminerCode(dto.ExaminerHcpCode);
            try { rules.validator.ValidateOnSave(dto, Birth, null, existing); }
            catch (ValidationFault fault) { errors.Add(fault.Message); }
            errors.AddRange(rules.Messenger.Errors);
            var warnings = rules.Messenger.Warnings;
            try { rules.validator.ValidateExamCodeForDuplicates(existing, dto.ExaminationCode, 0); }
            catch (ValidationWarningFault fault) { warnings.Add(fault.Message); }
            if (errors.Count > 0 || (warnings.Count > 0 && !confirmed))
                return new(false, errors.ToArray(), warnings.ToArray(), null);
            using (var context = contexts.CreateDbContext())
            {
                dto.PkChildExaminationId = context.Recordings.Max(r => (long?)r.Id).GetValueOrDefault() + 1;
                context.Add(new SavedRecording { Id = dto.PkChildExaminationId, PatientId = SelectedPatient, Data = JsonSerializer.Serialize(dto) });
                context.SaveChanges();
                var stored = context.Recordings.Where(r => r.PatientId == SelectedPatient).ToList();
                var rows = stored.Select(r => JsonSerializer.Deserialize<KdpExaminationResultTO>(r.Data)).Where(r => r.ExaminationCode == "KD03").ToList();
                var uow = new RepeatUnitOfWork();
                foreach (var row in rows)
                {
                    var exam = new ChildExamination { PkChildExaminationId = row.PkChildExaminationId, ClientId = row.ClientId, FkExaminationId = row.ExaminationCode, IsRepeat = row.IsRepeat ? "Y" : "N" };
                    uow.Exams.Add(exam);
                    uow.Given.Add(new ChildExaminationGiven { PkFkChildExamGivenId = exam.PkChildExaminationId, ExaminationDate = row.ExaminationDate, ChildExamination = exam });
                }
                ExtractedRepeatFlags.UpdateRepeatFlags(uow, SelectedPatient, "KD03");
                foreach (var row in rows)
                {
                    row.IsRepeat = uow.Exams.Single(e => e.PkChildExaminationId == row.PkChildExaminationId).IsRepeat == "Y";
                    stored.Single(r => r.Id == row.PkChildExaminationId).Data = JsonSerializer.Serialize(row);
                }
                context.SaveChanges();
            }
            return new(true, [], warnings.ToArray(), Read().Single(r => r.PkChildExaminationId == dto.PkChildExaminationId));
        }
    }
}
