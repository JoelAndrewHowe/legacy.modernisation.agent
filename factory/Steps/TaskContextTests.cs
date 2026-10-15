using NUnit.Framework;

[TestFixture]
public sealed class TaskContextTests
{
    [Test]
    public void ExtractsOnlyTheFirstUnfinishedTask()
    {
        var task = TaskContext.ExtractFirstUnfinished("""
            # Plan
            - [x] Completed task containing SECRET-ONE.
            - [ ] Active task.
              Supporting detail for the active task.
              - [ ] Nested acceptance check.
            - [ ] Later task containing SECRET-TWO.
            """);

        Assert.That(task, Does.Contain("Active task"));
        Assert.That(task, Does.Contain("Supporting detail"));
        Assert.That(task, Does.Contain("Nested acceptance check"));
        Assert.That(task, Does.Not.Contain("SECRET-ONE"));
        Assert.That(task, Does.Not.Contain("SECRET-TWO"));
    }

    [Test]
    public void ReturnsEmptyWhenNoTaskRemains()
    {
        Assert.That(TaskContext.ExtractFirstUnfinished("- [x] Complete"), Is.Empty);
    }
}
