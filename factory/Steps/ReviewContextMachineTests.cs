using System.Diagnostics;
using System.Text.Json;
using NUnit.Framework;

[TestFixture]
public sealed class ReviewContextMachineTests
{
    private string directory = null!;

    [SetUp]
    public void SetUp()
    {
        directory = Path.Combine(Path.GetTempPath(), $"review-context-{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        File.WriteAllText(Path.Combine(directory, "scenarios.json"), """
            {"scenarios":[
              {"id":"CASE-001","expected":"selected"},
              {"id":"CASE-002","expected":"not selected"}
            ]}
            """);
        File.WriteAllText(Path.Combine(directory, "guidance.md"), """
            # Guidance

            ## Relevant rules

            Use the accessible component.

            ## Later rules

            This must not be selected.
            """);
    }

    [TearDown]
    public void TearDown() => Directory.Delete(directory, true);

    [Test]
    public void ResolvesOnlyExplicitScenarioIdsAndGuidanceSections()
    {
        var result = Run("""
            ACTIVE_TASK_BEGIN
            - [ ] Implement the capability.
              - Acceptance: `scenarios.json#CASE-001`
              - Guidance: `guidance.md#relevant-rules`
            ACTIVE_TASK_END
            """);

        Assert.That(result.GetProperty("ready").GetBoolean(), Is.True);
        var context = result.GetProperty("context").GetString();
        Assert.That(context, Does.Contain("CASE-001"));
        Assert.That(context, Does.Contain("accessible component"));
        Assert.That(context, Does.Contain("sha256:"));
        Assert.That(context, Does.Not.Contain("CASE-002"));
        Assert.That(context, Does.Not.Contain("must not be selected"));
    }

    [Test]
    public void RejectsATaskWithoutBoundedReferences()
    {
        var result = Run("""
            ACTIVE_TASK_BEGIN
            - [ ] Implement an unbounded capability.
            ACTIVE_TASK_END
            """);

        Assert.That(result.GetProperty("ready").GetBoolean(), Is.False);
        Assert.That(result.GetProperty("findings").GetArrayLength(), Is.EqualTo(1));
    }

    private JsonElement Run(string prompt)
    {
        var factory = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../.."));
        var executable = Path.GetFullPath(Path.Combine(factory, "../bin/factory-review-context"));
        var start = new ProcessStartInfo(executable)
        {
            WorkingDirectory = directory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false
        };
        start.ArgumentList.Add(prompt);
        using var process = Process.Start(start)!;
        var output = process.StandardOutput.ReadToEnd();
        var error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        Assert.That(process.ExitCode, Is.Zero, error);
        using var document = JsonDocument.Parse(output);
        return document.RootElement.Clone();
    }
}
