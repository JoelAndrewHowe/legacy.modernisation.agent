using Hcwp.Application;
using Microsoft.AspNetCore.WebUtilities;
using System.Globalization;

namespace Hcwp.Presentation;

// Only recognised filter keys and selected-patient lookup values cross this boundary.
public sealed record ResultsUrlState(ResultsFilter Filter, string[] Notices)
{
    public static ResultsUrlState Parse(string uri, ResultsChoices choices)
    {
        var query = QueryHelpers.ParseQuery(new Uri(uri).Query);
        var notices = new List<string>();
        string[] Values(string key, IEnumerable<string> allowed)
        {
            var values = query.TryGetValue(key, out var supplied) ? supplied.ToArray() : [];
            var valid = values.Where(v => allowed.Contains(v)).Distinct().ToArray();
            if (values.Length != valid.Length) notices.Add("Invalid or unavailable " + key + " values ignored.");
            return valid;
        }
        DateOnly? Date(string key)
        {
            if (!query.ContainsKey(key) || string.IsNullOrEmpty(query[key])) return null;
            if (DateOnly.TryParseExact(query[key], "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var date)) return date;
            notices.Add("Invalid " + key + " date ignored."); return null;
        }
        int Number(string key, int fallback, Func<int, bool> valid)
        {
            if (!query.ContainsKey(key)) return fallback;
            if (int.TryParse(query[key], out var n) && valid(n)) return n;
            notices.Add("Invalid " + key + " ignored."); return fallback;
        }
        var from = Date("from"); var to = Date("to");
        if (from > to) { notices.Add("Reversed date range ignored."); from = to = null; }
        return new(new()
        {
            States = Values("state", Enum.GetNames<ExaminationState>()).Select(Enum.Parse<ExaminationState>).ToArray(),
            Repeats = Values("repeat", ["initial", "repeat"]).Select(v => v == "repeat").ToArray(),
            Findings = Values("finding", Enum.GetNames<PhysicalFinding>()).Select(Enum.Parse<PhysicalFinding>).ToArray(),
            Locations = Values("location", choices.Locations.Select(c => c.Code)),
            Examiners = Values("examiner", choices.Examiners.Select(c => c.Code)),
            From = from, To = to, Page = Number("page", 1, n => n > 0),
            PageSize = Number("size", 10, n => n is 10 or 25 or 50)
        }, notices.ToArray());
    }

    public static string Url(ResultsFilter f, int? page = null)
    {
        var values = new List<KeyValuePair<string, string>>();
        void Add(string key, string value) { if (value != null) values.Add(new(key, value)); }
        foreach (var v in f.States) Add("state", v.ToString());
        foreach (var v in f.Repeats) Add("repeat", v ? "repeat" : "initial");
        foreach (var v in f.Findings) Add("finding", v.ToString());
        foreach (var v in f.Locations) Add("location", v);
        foreach (var v in f.Examiners) Add("examiner", v);
        Add("from", f.From?.ToString("yyyy-MM-dd")); Add("to", f.To?.ToString("yyyy-MM-dd"));
        Add("size", f.PageSize.ToString()); Add("page", (page ?? f.Page).ToString());
        return "/results?" + string.Join("&", values.Select(p => Uri.EscapeDataString(p.Key) + "=" + Uri.EscapeDataString(p.Value)));
    }
}
