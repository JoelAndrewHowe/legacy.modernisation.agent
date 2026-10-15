using NUnit.Framework;

namespace Factory.Steps;

[TestFixture]
public sealed class MachineResultTests
{
    [Test]
    public void ReadsThePlanReviewLimit()
    {
        var options = Options.Parse(["--run", "example", "--plan-reviews", "2"]);

        Assert.That(options.PlanReviews, Is.EqualTo(2));
    }

    [Test]
    public void ReadsAnOpenRouterModelFromMachineConfiguration()
    {
        var directory = Path.Combine(Path.GetTempPath(), $"factory-machine-{Guid.NewGuid():N}");
        Directory.CreateDirectory(directory);
        var path = Path.Combine(directory, "config.json");
        try
        {
            File.WriteAllText(path, """
                {"harness":"openrouter-reviewer","role":"validator","model":"openai/gpt-6.1-sol"}
                """);

            var configuration = MachineConfiguration.Read(path);

            Assert.Multiple(() =>
            {
                Assert.That(configuration.Harness, Is.EqualTo("openrouter-reviewer"));
                Assert.That(configuration.Role, Is.EqualTo("validator"));
                Assert.That(configuration.Model, Is.EqualTo("openai/gpt-6.1-sol"));
            });
        }
        finally
        {
            Directory.Delete(directory, true);
        }
    }

    [Test]
    public void ReadsStringFindings()
    {
        var result = MachineResult.From("{\"findings\":[\"needs tests\"]}");

        Assert.That(result.TryStrings("findings", out var findings), Is.True);
        Assert.That(findings, Is.EqualTo(new[] { "needs tests" }));
    }

    [Test]
    public void PreservesStructuredFindingsAsJson()
    {
        var result = MachineResult.From("{\"findings\":[{\"problem\":\"mixed responsibilities\"}]}");

        Assert.That(result.TryStrings("findings", out var findings), Is.True);
        Assert.That(findings, Is.EqualTo(new[] { "{\"problem\":\"mixed responsibilities\"}" }));
    }

    [Test]
    public void ReadsAMultilineFencedResult()
    {
        var result = MachineResult.From("""
            Review complete.
            ```json
            {
              "satisfied": true,
              "findings": []
            }
            ```
            """);

        Assert.Multiple(() =>
        {
            Assert.That(result.TryBoolean("satisfied", out var satisfied), Is.True);
            Assert.That(satisfied, Is.True);
            Assert.That(result.TryStrings("findings", out var findings), Is.True);
            Assert.That(findings, Is.Empty);
        });
    }
}
