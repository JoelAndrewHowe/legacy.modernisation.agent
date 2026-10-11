using NUnit.Framework;

namespace Factory.Steps;

[TestFixture]
public sealed class MachineResultTests
{
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
}
