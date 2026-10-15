using System.Globalization;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
public static class SliceRunner {
 public static void Main() {
  CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("en-GB");
  CultureInfo.CurrentUICulture = CultureInfo.CurrentCulture;
  var observe = typeof(Hcwp.SystemFeel.Converted.Program).GetMethod("Observe", BindingFlags.Static | BindingFlags.NonPublic)!;
  string line;
  while ((line = Console.ReadLine()) != null) {
   try { Console.WriteLine(JsonSerializer.Serialize(observe.Invoke(null, new object[] { JsonNode.Parse(line)! }))); }
   catch (Exception e) { Console.WriteLine(JsonSerializer.Serialize(new { error = e.ToString() })); }
  }
 }
}
