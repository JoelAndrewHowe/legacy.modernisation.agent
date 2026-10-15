using System.Globalization;
using System.Text.Json;

namespace Hcwp.Presentation;

// Presentation only. Never translate or reinterpret unavailable legacy clinical prose.
public sealed class InterfaceLanguage
{
    private readonly Dictionary<string, string> welsh;
    public InterfaceLanguage(string inventory)
    {
        welsh = JsonSerializer.Deserialize<Dictionary<string, string>>(inventory)
            ?? throw new InvalidOperationException("Empty bilingual inventory");
    }
    public string Code { get; private set; } = "en";
    public event Action Changed;
    public void Select(string code)
    {
        var next = code == "cy" ? "cy" : "en";
        if (next == Code) return;
        Code = next;
        Changed?.Invoke();
    }
    public string Text(string english) => Code == "cy" && english != null
        && welsh.TryGetValue(english, out var translated) && !string.IsNullOrWhiteSpace(translated)
        ? translated : english;
    public string Format(string english, params object[] values) => string.Format(
        CultureInfo.GetCultureInfo(Code == "cy" ? "cy-GB" : "en-GB"), Text(english), values);
}
