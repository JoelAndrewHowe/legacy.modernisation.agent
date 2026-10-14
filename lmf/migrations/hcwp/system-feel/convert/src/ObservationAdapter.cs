// Port of the approved scenario-independent adapter. Never reads expectations.
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;
namespace Hcwp.SystemFeel.Converted;

public static class Program {
    static T Read<T>(JsonNode n) => n.Deserialize<T>();
    static object R(string id, params object[] args) => Resource.Format(id, args);
    public static void Main(string[] args) {
        // Refuse direct DLL execution without current revision-bound approval.
        if (args.Length != 2 || args[0] != "--evidence-prefix") {
            Console.Error.WriteLine("Required: --evidence-prefix <fresh-prefix>");
            Environment.ExitCode = 2;
            return;
        }
        var gatePath = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../../../check-prerequisites.py"));
        var start = new System.Diagnostics.ProcessStartInfo("python3") {
            RedirectStandardOutput = true, UseShellExecute = false
        };
        start.ArgumentList.Add(gatePath);
        start.ArgumentList.Add("--evidence-prefix");
        start.ArgumentList.Add(args[1]);
        start.Environment["PYTHONDONTWRITEBYTECODE"] = "1";
        using (var gate = System.Diagnostics.Process.Start(start)) {
            // Large prerequisite report is already retained by the gate; drain it.
            gate.StandardOutput.ReadToEnd();
            gate.WaitForExit();
            if (gate.ExitCode != 0) { Environment.ExitCode = gate.ExitCode; return; }
        }
        CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("en-GB");
        CultureInfo.CurrentUICulture = CultureInfo.CurrentCulture;
        string line;
        while ((line = Console.ReadLine()) != null) {
            try { Console.WriteLine(JsonSerializer.Serialize(Observe(JsonNode.Parse(line)))); }
            catch (Exception e) { Console.WriteLine(JsonSerializer.Serialize(new { error = e.ToString() })); }
        }
    }
    static AlertModel Alerts(ChildGeneral p) => new() {
        CurrentStatusCode = p.CurrentStatus,
        ChildAlerts = p.ChildAlertCodes.Select(a => a.AlertCodes.AlertText).ToList()
    };
    static object Observe(JsonNode request) {
        string op = (string)request["operation"];
        var input = request["inputs"];
        switch (op) {
        case "name": return new { value = Legacy.Name(Read<ChildGeneral>(input)) };
        case "address": return new { value = Legacy.Address(Read<ChildGeneral>(input)) };
        case "span-text": return new { text = Legacy.SpanText((string)input["value"], (string)input["format"], (bool)input["leaveBlankIfNull"]) };
        case "age":
            ReferenceClock.Now = DateTime.Parse((string)input["clock"]);
            return new { AgeString = Legacy.GetAge(DateTime.Parse((string)input["DateOfBirth"]), input["DateOfDeath"] == null ? null : DateTime.Parse((string)input["DateOfDeath"])) };
        case "summary": {
            // Graph repository adapter retains GetClientSummary's selected-ID/single-row predicate.
            var id = (long)input["ClientId"];
            var p = Read<List<ChildGeneral>>(input["repositoryPatients"]).SingleOrDefault(x => x.ClientId == id)
                ?? throw new InvalidOperationException("Requested patient absent");
            ReferenceClock.Now = DateTime.Parse((string)input["clock"]);
            var alerts = Alerts(p);
            var age = Legacy.GetAge(p.DateOfBirth, p.DateOfDeath);
            var result = new Dictionary<string,object> {
                ["ClientId"] = p.ClientId, ["Fullname"] = Legacy.Name(p), ["NhsNumber"] = p.NhsNumber,
                ["DateOfBirth"] = p.DateOfBirth.ToString("yyyy-MM-ddTHH:mm:ss"),
                ["birthDateText"] = p.DateOfBirth.ToString("dd-MMM-yyyy"), ["AgeString"] = age,
                ["ageDisplay"] = p.CurrentStatus != "7" ? age : "-",
                ["ageLabelResource"] = p.DateOfDeath.HasValue ? "AgeAtDeath" : "AgeLabel",
                ["FullAddress"] = Legacy.Address(p),
                ["School"] = Legacy.School(p.ChildCentres.FirstOrDefault(s => s.ChildLocationType == LookupsUtility.CENTRE_TYPES.SCHOOL)),
                ["Organisation"] = Legacy.GetOrganisationValue(p.ChildCentres, new UnitOfWork { Locations = Read<List<ChildLocations>>(input["authorityLocations"]) }),
                ["ChildAlerts"] = alerts.ChildAlerts, ["ShowAlert"] = alerts.ShowAlert,
                ["genderRequest"] = new { @enum = "GENDER", value = p.Sex, member = p.Sex switch { 0=>"NOTKNOWN", 1=>"MALE", 2=>"FEMALE", 9=>"NOTSPECIFIED", _=>throw new InvalidOperationException("Unknown enum input") } },
                ["childAlertCalls"] = alerts.ChildAlerts.Select(text => new { headingResource = "CommunityIndexHeading", message = R("ChildAlerts",text) }).ToList()
            };
            // Missing CurrentStatusText and EnumResolver prose: record requests, never fabricate labels.
            if (!string.IsNullOrEmpty(p.CurrentStatus)) result["statusRequest"] = new { resolver="CurrentStatusText", arguments=new[] {p.CurrentStatus} };
            else result["statusText"] = string.Empty;
            // _ClientAlerts markup adaptation. Preserve inner date-format call before outer message call.
            var status = p.CurrentStatus switch {
                LookupsUtility.CurrentStatus_Died => ("ChildDied", p.DateOfDeath),
                LookupsUtility.CurrentStatus_MovementOut => ("ChildMovedOut", p.CurrentStatusDate),
                LookupsUtility.CurrentStatus_TransferredOut => ("ChildTransferredOut", p.CurrentStatusDate),
                LookupsUtility.CurrentStatus_Stillbirth => ("ChildStillborn", (DateTime?)p.DateOfBirth),
                _ => ((string)null, (DateTime?)null)
            };
            if (status.Item1 != null) {
                var date = status.Item2?.ToString("yyyy-MM-ddTHH:mm:ss");
                result["statusAlert"] = new { headingResource = status.Item1+"AlertHeading", messageResource = status.Item1+"AlertMessage", date, dateFormatResource = "DateFormatStandard", messageCall = R(status.Item1+"AlertMessage", R("DateFormatStandard",date)) };
            }
            result["dependencyCalls"] = new object[] { new { boundary="DefaultAccessForChild", clientId=id, adaptation="recorded-no-op; excluded" }, new { boundary="EF6-Include", adaptation="supplied navigation graph; no provider" } };
            return result;
        }
        case "alert-setup": {
            var a = Alerts(Read<ChildGeneral>(input["patient"]));
            return new { ShowAlert=a.ShowAlert, setupAlertDialogs=a.ShowAlert && (string)input["showAlertsQuery"] != "false", ChildAlerts=a.ChildAlerts };
        }
        case "results": {
            var rows = Read<List<Row>>(input["rows"]);
            var service = new ResultService { entities = rows.Select(r => new ChildExamination { ClientId=r.ClientId, ExaminationDescriptions=new Description { FkExamDescriptionType=r.ExamType }, ChildExaminationGiven=new Given { ExaminationDate=r.ExaminationDate }, Saved=r }).ToList() };
            var d = new LegacyDelegate { service=service };
            d.GetKdpResults((long)input["ClientId"]);
            var observed = d.listOfKdpExaminationResultDelegates;
            // Explicit slice adapter AFTER original all-KDP query/delegate ordering.
            if ((string)input["scope"] == "KD03") observed = observed.Where(r => r.ExaminationCode == "KD03").ToList();
            else if ((string)input["scope"] != "all-KDP") throw new InvalidOperationException("Unknown result scope");
            return new { count=observed.Count, rows=observed };
        }
        case "physical-values": case "facets": {
            if ((string)input["ExaminationCode"] != "KD03") throw new InvalidOperationException("Only KD03 physical applicability characterised");
            string[] fields = { "Heart", "Hips", "Eyes", "Testes", "PhysicalGeneral" };
            var choices = Legacy.PhysicalAssessment6To8Weeks();
            var physical = new Dictionary<string,object>();
            bool concern = false;
            foreach (var f in fields) {
                byte? value = input[f] == null ? null : (byte)input[f];
                // Empty lookup choice remains absent in the observation protocol, not value 3.
                var choice = value.HasValue ? choices.Single(kv => kv.Value == value).Key : null;
                physical[f] = new { raw=value, choice };
                concern |= value == 2;
            }
            // Intentional display predicates, NOT a legacy persisted aggregate clinical status.
            return new { physical, hasConcern=concern, persistedAggregateStatus=false,
                examinationState = input["ReasonNotExamined"] == null ? "Recorded" : "Not examined",
                repeatLabel = input["IsRepeat"] != null && (bool)input["IsRepeat"] ? "Repeat" : "Initial",
                inputAfter = input.DeepClone() };
        }
        default: throw new InvalidOperationException("Unknown operation " + op);
        }
    }
}
