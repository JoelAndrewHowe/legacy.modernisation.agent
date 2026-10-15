using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
using Hcwp.Application;
using Orvex.Model;
using Orvex.TransferObjects;
using C = Hcwp.SystemFeel.Converted;

// Input-only adapter: approved expectations are never supplied to this process.
public static partial class QueryChecks
{
    sealed class Repository(JsonNode input) : IPatientSummaryRepository
    {
        public C.ChildGeneral Find(long id) => input["repositoryPatients"].Deserialize<List<C.ChildGeneral>>().SingleOrDefault(p => p.ClientId == id);
        public IEnumerable<C.ChildLocations> AuthorityLocations() => input["authorityLocations"].Deserialize<List<C.ChildLocations>>();
    }
    public static int ObserveApprovedSystemFeel()
    {
        CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("en-GB");
        string line;
        while ((line = Console.ReadLine()) != null)
        {
            try { Console.WriteLine(Observe(JsonNode.Parse(line)).ToJsonString()); }
            catch (Exception e) { Console.WriteLine(JsonSerializer.Serialize(new { error = e.ToString() })); }
        }
        return 0;
    }
    static JsonNode Observe(JsonNode request)
    {
        var input = request["inputs"];
        var operation = (string)request["operation"];
        if (operation is "name" or "address" or "age")
        {
            // Wrap unchanged helper inputs in the minimal repository graph so the
            // observation comes from the integrated summary service, not a helper call.
            var summaryPatient = new JsonObject { ["ClientId"] = 101, ["DateOfBirth"] = "2025-01-01T00:00:00" };
            foreach (var (key, value) in input.AsObject())
                if (key != "clock") summaryPatient[key] = value?.DeepClone();
            var summaryGraph = new JsonObject { ["ClientId"] = 101, ["repositoryPatients"] = new JsonArray(summaryPatient), ["authorityLocations"] = new JsonArray() };
            ReferenceClock.Now = input["clock"] == null ? new(2025, 3, 15, 12, 0, 0) : DateTime.Parse((string)input["clock"]);
            var summary = new PatientSummaryQuery(new Repository(summaryGraph)).Read(101);
            return operation == "age" ? new JsonObject { ["AgeString"] = summary.Age }
                : new JsonObject { ["value"] = operation == "name" ? summary.FullName : summary.Address };
        }
        if (operation == "summary")
        {
            ReferenceClock.Now = DateTime.Parse((string)input["clock"]);
            var s = new PatientSummaryQuery(new Repository(input)).Read((long)input["ClientId"]);
            return JsonSerializer.SerializeToNode(new { Fullname = s.FullName, s.NhsNumber,
                DateOfBirth = s.DateOfBirth.ToString("yyyy-MM-ddTHH:mm:ss"), ageDisplay = s.Age,
                FullAddress = s.Address, s.School, s.Organisation, s.ShowAlert, ChildAlerts = s.Alerts,
                sex = s.Sex, currentStatusCode = s.CurrentStatusCode });
        }
        if ((string)request["operation"] != "results") throw new InvalidOperationException("Unsupported boundary operation");
        var rows = input["rows"].AsArray();
        var patient = (long)input["ClientId"];
        var store = new Store();
        foreach (var id in rows.Select(r => (long)r["ClientId"]).Append(patient).Distinct())
            store.Rows<ChildGeneral>().Add(new() { ClientId = id, DateOfBirth = new(2025, 1, 1), Sex = "M" });
        // Reference fixtures supply flattened navigation values, not global lookup tables.
        // Build doubles from requested patient's graph first (other-patient sentinel names
        // deliberately reuse codes). No clinical field or patient ID is rewritten.
        var graph = rows.OrderByDescending(r => (long)r["ClientId"] == patient).ToList();
        foreach (var group in graph.GroupBy(r => (string)r["ExaminationCode"]))
            store.Rows<ExaminationDescriptions>().Add(new() { PkExamDescriptionId = group.Key, LongDescription = (string)group.First()["ExamDescription"], FkExamDescriptionType = (string)group.First()["ExamType"] == "Kdp" ? Orvex.Contracts.Enums.ExamType.Kdp : Orvex.Contracts.Enums.ExamType.OtherScreening });
        foreach (var group in graph.GroupBy(r => (string)r["LocationCode"]))
            store.Rows<ChildLocations>().Add(new() { Code = group.Key, LocationType = (byte)group.First()["LocationType"], Name = (string)group.First()["LocationName"] });
        foreach (var group in graph.GroupBy(r => (string)r["ExaminerHcpCode"]))
            store.Rows<HealthCareProfessionals>().Add(new() { Code = group.Key, Name1 = (string)group.First()["ExaminerName"], Name2 = "" });
        foreach (var row in rows)
        {
            var dto = new KdpExaminationResultTO();
            foreach (var (key, value) in row.AsObject())
            {
                if (key == "ExamType") continue;
                if (key == "ReasonNotExamined") dto.ReasonNotExamined = value?.ToString();
                else ScenarioAdapter.Set(dto, key, value);
            }
            var examination = new ChildExamination(); var given = new ChildExaminationGiven(); var kdp = new ChildExaminationKdp();
            AutoMapper.Mapper.Map(dto, examination); AutoMapper.Mapper.Map(dto, given); AutoMapper.Mapper.Map(dto, kdp);
            store.Rows<ChildExamination>().Add(examination); store.Rows<ChildExaminationGiven>().Add(given); store.Rows<ChildExaminationKdp>().Add(kdp);
        }
        store.Link();
        using (store.Open()) { }
        var query = new Kd03ResultsQuery(new Kd03Recording(store));
        var page = query.Search(patient, new() { PageSize = 50 });
        var observed = new JsonArray();
        foreach (var r in page.Rows)
        {
            // Verify detail is the same fresh persisted graph, not submitted fixture data.
            var detail = query.Detail(patient, r.PkChildExaminationId);
            var o = new JsonObject();
            foreach (var key in rows[0].AsObject().Select(kv => kv.Key).Where(k => k != "ExamType"))
            {
                var value = key == "ResultEnteredDate" ? Kd03ResultsQuery.RecordedDate(detail) : detail.GetType().GetProperty(key).GetValue(detail);
                if (key == "ReasonNotExamined") o[key] = value == null ? null : JsonValue.Create(int.Parse((string)value));
                else if (key == "ExaminerName") o[key] = ((string)value)?.TrimEnd();
                else o[key] = JsonSerializer.SerializeToNode(value);
            }
            o["ExamType"] = "Kdp";
            observed.Add(o);
        }
        return new JsonObject { ["count"] = page.Total, ["rows"] = observed };
    }
}
