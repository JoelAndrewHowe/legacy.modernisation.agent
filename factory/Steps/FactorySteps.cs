using System.Diagnostics;
using NUnit.Framework;
using Reqnroll;

namespace Factory.Steps;

[Binding]
public sealed class FactorySteps
{
    private string workspace = "";
    private string repository = "";
    private string factory = "";
    private string target = "";
    private string seed = "";
    private string agent = "";
    private string fakeBin = "";
    private string calls = "";
    private string output = "";
    private int exitCode;
    private int commitsBefore;
    private bool omitTarget;
    private bool omitSeed;
    private bool omitAgent;
    private bool answerInProse;
    private bool prosePlan;
    private bool writeSentinel;
    private bool talkFirst;
    private string? statusBefore;
    private readonly Dictionary<string, string> snapshots = [];

    [Given("a copy of the factory")]
    public void CopyFactory()
    {
        workspace = Path.Combine(Path.GetTempPath(), $"factory-test-{Guid.NewGuid():N}");
        repository = Path.Combine(workspace, "repo");
        factory = Path.Combine(repository, "factory");
        target = Path.Combine(repository, "output");
        seed = Path.Combine(repository, "seed.md");
        fakeBin = Path.Combine(workspace, "bin");
        calls = Path.Combine(workspace, "calls");
        Directory.CreateDirectory(factory);
        Directory.CreateDirectory(fakeBin);
        Directory.CreateDirectory(calls);

        var source = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../.."));
        File.Copy(Path.Combine(source, "Factory.csproj"), Path.Combine(factory, "Factory.csproj"));
        File.Copy(Path.Combine(source, "Program.cs"), Path.Combine(factory, "Program.cs"));
        File.Copy(Path.Combine(source, ".gitignore"), Path.Combine(factory, ".gitignore"));
        RunGit(repository, "init", "--quiet");
        RunGit(repository, "config", "user.email", "test@example.invalid");
        RunGit(repository, "config", "user.name", "Factory Test");
        RunGit(repository, "add", ".");
        RunGit(repository, "commit", "--quiet", "-m", "test workspace");

        agent = WriteAgent("chosen-agent", "chosen");
        WriteAgent("pi", "pi");
    }

    [Given("a new target")]
    public void NewTarget() => Directory.CreateDirectory(target);

    [Given("a seed describing a game of Tetris")]
    public void TetrisSeed() => File.WriteAllText(seed, "Build a game of Tetris.\n");

    [Given("the agent plans the tasks alpha and beta, and does one task a pass")]
    public void ConfigureAgent() { }

    [Given("no harness is chosen")]
    public void NoHarness() => omitAgent = true;

    [Given("the agent is pi")]
    public void AgentIsPi() => omitAgent = true;

    [Given("the agent cannot be run")]
    public void AgentCannotRun() => agent = Path.Combine(workspace, "missing-agent");

    [Given("no plan")]
    public void NoPlan()
    {
        var plan = PlanPath();
        if (File.Exists(plan)) File.Delete(plan);
    }

    [Given("a plan with three tasks, none of them done")]
    public void ThreeTaskPlan() => WritePlan("- [ ] alpha\n- [ ] beta\n- [ ] gamma\n");

    [Given("a plan whose first task is done")]
    public void FirstTaskDone() => WritePlan("- [x] alpha\n- [ ] beta\n- [ ] gamma\n");

    [Given("a plan in which every task is done")]
    public void EveryTaskDone() => WritePlan("- [x] alpha\n- [x] beta\n");

    [Given("the agent writes a file called SENTINEL")]
    public void AgentWritesSentinel() => writeSentinel = true;

    [Given("the agent says {string} before its result")]
    public void AgentTalks(string _) => talkFirst = true;

    [Given("the agent answers in prose, with no result")]
    public void AgentAnswersInProse() => answerInProse = true;

    [Given("the agent keeps its plan in prose")]
    public void AgentKeepsProsePlan() => prosePlan = true;

    [Given("no seed is chosen")]
    public void NoSeedChosen() => omitSeed = true;

    [Given("the seed has been deleted")]
    public void SeedDeleted() => File.Delete(seed);

    [Given("no target is chosen")]
    public void NoTargetChosen() => omitTarget = true;

    [Given("the target folder does not exist")]
    public void TargetMissing()
    {
        if (Directory.Exists(target)) Directory.Delete(target, true);
    }

    [Given("the target is outside any Git repository")]
    public void StandaloneTarget()
    {
        target = Path.Combine(workspace, "standalone");
        Directory.CreateDirectory(target);
    }

    [Given("the factory has staged and unstaged changes")]
    public void UnrelatedChanges()
    {
        File.WriteAllText(Path.Combine(repository, "staged.txt"), "staged");
        RunGit(repository, "add", "staged.txt");
        File.WriteAllText(Path.Combine(repository, "unstaged.txt"), "unstaged");
        statusBefore = RunGit(repository, "status", "--porcelain");
    }

    [When("the factory runs one pass")]
    public void RunOnePass() => RunFactory(target, all: false, absolute: true);

    [When("the factory runs to completion")]
    public void RunToCompletion() => RunFactory(target, all: true, absolute: true);

    [When("the factory builds the target {string} to completion")]
    public void BuildNamedTarget(string name)
    {
        var namedTarget = Path.Combine(repository, name);
        RunFactory(namedTarget, all: true, absolute: false);
        snapshots[name] = Snapshot(namedTarget);
    }

    [When("the factory builds the same target using its absolute path")]
    public void BuildSameTargetAbsolute()
    {
        var namedTarget = Path.Combine(repository, "a-generation");
        snapshots["a-generation-before"] = Snapshot(namedTarget);
        RunFactory(namedTarget, all: true, absolute: true);
    }

    [Then("pi has been called")]
    public void PiCalled() => Assert.That(CallCount("pi"), Is.GreaterThan(0));

    [Then("the chosen agent has been called")]
    public void ChosenCalled() => Assert.That(CallCount("chosen"), Is.GreaterThan(0));

    [Then("pi has not been called")]
    public void PiNotCalled() => Assert.That(CallCount("pi"), Is.Zero);

    [Then("no agent has been called")]
    public void NoAgentCalled() => Assert.That(TotalCalls(), Is.Zero);

    [Then("the agent has been called once")]
    public void AgentCalledOnce() => Assert.That(TotalCalls(), Is.EqualTo(1));

    [Then("it reports that it could not run the agent")]
    public void ReportsAgentFailure() => Assert.That(output, Does.Contain("Could not run the agent"));

    [Then("it reports that it could not read the agent's result")]
    public void ReportsUnreadableResult() => Assert.That(output, Does.Contain("Could not read the agent's result"));

    [Then("it reports that there is no seed")]
    public void ReportsNoSeed() => Assert.That(output, Does.Contain("There is no seed"));

    [Then("it reports that a target is required")]
    public void ReportsTargetRequired() => Assert.That(output, Does.Contain("A target is required"));

    [Then("there is no plan")]
    public void ThereIsNoPlan() => Assert.That(File.Exists(PlanPath()), Is.False);

    [Then("there is a plan")]
    public void ThereIsAPlan() => Assert.That(File.Exists(PlanPath()), Is.True);

    [Then("the plan has the tasks {string} and {string}, and no others")]
    public void PlanHasTwoTasks(string first, string second)
    {
        var plan = File.ReadAllText(PlanPath());
        Assert.Multiple(() =>
        {
            Assert.That(plan, Does.Contain(first));
            Assert.That(plan, Does.Contain(second));
            Assert.That(plan, Does.Not.Contain("gamma"));
        });
    }

    [Then("the plan shows every task as not done")]
    public void EveryTaskNotDone() => Assert.That(File.ReadAllLines(PlanPath()), Has.All.Contains("[ ]"));

    [Then("the plan still has those three tasks")]
    public void StillThreeTasks() => Assert.That(File.ReadAllLines(PlanPath()), Has.Length.EqualTo(3));

    [Then("the plan shows the first task as done")]
    public void FirstDone() => Assert.That(File.ReadAllLines(PlanPath())[0], Does.Contain("[x]"));

    [Then("the plan shows the first two tasks as done")]
    public void FirstTwoDone() => Assert.That(File.ReadAllLines(PlanPath()).Take(2), Has.All.Contains("[x]"));

    [Then("the plan shows the other two as not done")]
    public void OtherTwoNotDone() => Assert.That(File.ReadAllLines(PlanPath()).Skip(1), Has.All.Contains("[ ]"));

    [Then("the plan shows every task as done")]
    public void AllDone() => Assert.That(File.ReadAllLines(PlanPath()), Has.All.Contains("[x]"));

    [Then(@"the plan is \.factory/plan\.md in the target")]
    public void PlanInTarget() => Assert.That(File.Exists(Path.Combine(target, ".factory", "plan.md")), Is.True);

    [Then("there is no plan in the factory's folder")]
    public void NoPlanInFactory() => Assert.That(File.Exists(Path.Combine(factory, ".factory", "plan.md")), Is.False);

    [Then("there is one new work commit")]
    public void OneWorkCommit() => Assert.That(WorkCommits(), Is.EqualTo(1));

    [Then("there are three new work commits")]
    public void ThreeWorkCommits() => Assert.That(WorkCommits(), Is.EqualTo(3));

    [Then("there are no new commits")]
    public void NoNewCommits() => Assert.That(CommitCount(), Is.EqualTo(commitsBefore));

    [Then("there are no new work commits")]
    public void NoNewWorkCommits() => Assert.That(WorkCommits(), Is.Zero);

    [Then("it contains the work for the first task")]
    public void ContainsFirstWork() => Assert.That(File.Exists(Path.Combine(target, "alpha.txt")), Is.True);

    [Then("it contains the work for the second task")]
    public void ContainsSecondWork() => Assert.That(File.Exists(Path.Combine(target, "beta.txt")), Is.True);

    [Then("its only product file is SENTINEL")]
    public void OnlySentinel()
    {
        var products = Directory.GetFiles(target, "*", SearchOption.AllDirectories)
            .Where(path => !path.Contains($"{Path.DirectorySeparatorChar}.factory{Path.DirectorySeparatorChar}"))
            .Select(Path.GetFileName);
        Assert.That(products, Is.EquivalentTo(new[] { "SENTINEL" }));
    }

    [Then("the agent was pointed at the plan and at the seed")]
    public void PromptHasPaths()
    {
        var prompt = LastPrompt();
        Assert.Multiple(() =>
        {
            Assert.That(prompt, Does.Contain(Path.GetFullPath(seed)));
            Assert.That(prompt, Does.Contain(Path.GetFullPath(PlanPath())));
        });
    }

    [Then("the agent was asked for a result with the field {string}")]
    public void PromptAsksForField(string field) => Assert.That(LastPrompt(), Does.Contain($"field \"{field}\""));

    [Then("the factory has stopped")]
    public void FactoryStopped() => Assert.That(exitCode, Is.Not.EqualTo(int.MinValue));

    [Then("the committed plan matches the plan on disk")]
    public void CommittedPlanMatches()
    {
        var repo = RepositoryForTarget();
        var relative = Path.GetRelativePath(repo, PlanPath());
        Assert.That(RunGit(repo, "show", $"HEAD:{relative}"), Is.EqualTo(File.ReadAllText(PlanPath())));
    }

    [Then("the target has no uncommitted changes")]
    public void TargetClean()
    {
        var repo = RepositoryForTarget();
        var relative = Path.GetRelativePath(repo, target);
        Assert.That(RunGit(repo, "status", "--porcelain", "--", relative), Is.Empty);
    }

    [Then("the work for alpha and beta has been committed")]
    public void AlphaAndBetaCommitted()
    {
        Assert.Multiple(() =>
        {
            Assert.That(File.Exists(Path.Combine(target, "alpha.txt")), Is.True);
            Assert.That(File.Exists(Path.Combine(target, "beta.txt")), Is.True);
            Assert.That(WorkCommits(), Is.EqualTo(2));
        });
    }

    [Then("the target uses the containing repository")]
    public void UsesContainingRepository() => Assert.That(RepositoryForTarget(), Is.EqualTo(repository));

    [Then("the target is a Git repository")]
    public void TargetIsRepository() => Assert.That(RepositoryForTarget(), Is.EqualTo(target));

    [Then("the factory's own files and unrelated uncommitted changes are as they were")]
    public void UnrelatedUnchanged() => Assert.That(RunGit(repository, "status", "--porcelain"), Is.EqualTo(statusBefore));

    [Then("the target {string} is unchanged")]
    public void NamedTargetUnchanged(string name)
    {
        var key = name == "a-generation" && snapshots.ContainsKey("a-generation-before")
            ? "a-generation-before" : name;
        Assert.That(Snapshot(Path.Combine(repository, name)), Is.EqualTo(snapshots[key]));
    }

    [Then("the targets {string} and {string} each have their own completed plan and committed work")]
    public void TargetsIndependent(string first, string second)
    {
        foreach (var name in new[] { first, second })
        {
            var path = Path.Combine(repository, name);
            Assert.That(File.ReadAllLines(Path.Combine(path, ".factory", "plan.md")), Has.All.Contains("[x]"));
            Assert.That(File.Exists(Path.Combine(path, "alpha.txt")), Is.True);
        }
    }

    [AfterScenario]
    public void Cleanup()
    {
        if (Directory.Exists(workspace)) Directory.Delete(workspace, true);
    }

    private void RunFactory(string selectedTarget, bool all, bool absolute)
    {
        target = selectedTarget;
        commitsBefore = Directory.Exists(Path.Combine(selectedTarget, ".git")) ||
                        Directory.Exists(Path.Combine(repository, ".git")) && selectedTarget.StartsWith(repository)
            ? CommitCount()
            : 0;
        var start = new ProcessStartInfo("dotnet")
        {
            WorkingDirectory = repository,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        start.ArgumentList.Add("run");
        start.ArgumentList.Add("--project");
        start.ArgumentList.Add(Path.Combine(factory, "Factory.csproj"));
        start.ArgumentList.Add("--");
        if (!omitSeed)
        {
            start.ArgumentList.Add("--seed");
            start.ArgumentList.Add(absolute ? seed : Path.GetRelativePath(repository, seed));
        }
        if (!omitTarget)
        {
            start.ArgumentList.Add("--target");
            start.ArgumentList.Add(absolute ? selectedTarget : Path.GetRelativePath(repository, selectedTarget));
        }
        if (!omitAgent)
        {
            start.ArgumentList.Add("--agent");
            start.ArgumentList.Add(agent);
        }
        if (all) start.ArgumentList.Add("--all");
        start.Environment["PATH"] = $"{fakeBin}:{Environment.GetEnvironmentVariable("PATH")}";
        start.Environment["FACTORY_CALLS"] = calls;
        start.Environment["FACTORY_ANSWER_PROSE"] = answerInProse ? "1" : "0";
        start.Environment["FACTORY_PROSE_PLAN"] = prosePlan ? "1" : "0";
        start.Environment["FACTORY_SENTINEL"] = writeSentinel ? "1" : "0";
        start.Environment["FACTORY_TALK"] = talkFirst ? "1" : "0";

        using var process = Process.Start(start)!;
        output = process.StandardOutput.ReadToEnd() + process.StandardError.ReadToEnd();
        process.WaitForExit();
        exitCode = process.ExitCode;
    }

    private string WriteAgent(string name, string identity)
    {
        var path = Path.Combine(fakeBin, name);
        File.WriteAllText(path, $$"""
            #!/usr/bin/env bash
            set -euo pipefail
            mkdir -p "$FACTORY_CALLS"
            number=$(($(find "$FACTORY_CALLS" -name '{{identity}}-*.prompt' | wc -l) + 1))
            printf '%s' "$*" > "$FACTORY_CALLS/{{identity}}-$number.prompt"
            if [ "$FACTORY_ANSWER_PROSE" = 1 ]; then echo 'I cannot provide a result'; exit 0; fi
            mkdir -p .factory
            plan=.factory/plan.md
            if [ ! -f "$plan" ]; then
              if [ "$FACTORY_PROSE_PLAN" = 1 ]; then
                printf 'alpha is pending\nbeta is pending\n' > "$plan"
              else
                printf '%s\n' '- [ ] alpha' '- [ ] beta' > "$plan"
              fi
              echo '{"complete":false}'
              exit 0
            fi
            if grep -q '\[ \]' "$plan"; then
              task=$(grep '\[ \]' "$plan" | head -1 | sed 's/.*] //')
              sed -i '0,/\[ \]/{s/\[ \]/[x]/}' "$plan"
            elif grep -q ' is pending' "$plan"; then
              task=$(grep ' is pending' "$plan" | head -1 | sed 's/ is pending//')
              sed -i "0,/$task is pending/{s/$task is pending/$task is done/}" "$plan"
            else
              echo '{"complete":true}'
              exit 0
            fi
            if [ "$FACTORY_SENTINEL" = 1 ]; then touch SENTINEL; else printf '%s\n' "$task" > "$task.txt"; fi
            [ "$FACTORY_TALK" = 1 ] && echo 'nothing left to do'
            if grep -Eq '\[ \]| is pending' "$plan"; then complete=false; else complete=true; fi
            printf '{"complete":%s,"task":"%s"}\n' "$complete" "$task"
            """);
        File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
        return path;
    }

    private void WritePlan(string text)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(PlanPath())!);
        File.WriteAllText(PlanPath(), text);
        RunGit(repository, "add", ".");
        RunGit(repository, "commit", "--quiet", "-m", "starting plan");
    }

    private string PlanPath() => Path.Combine(target, ".factory", "plan.md");
    private int CallCount(string identity) => Directory.GetFiles(calls, $"{identity}-*.prompt").Length;
    private int TotalCalls() => Directory.GetFiles(calls, "*.prompt").Length;
    private string LastPrompt() => File.ReadAllText(Directory.GetFiles(calls, "*.prompt").Order().Last());
    private int CommitCount() => int.Parse(RunGit(RepositoryForTarget(), "rev-list", "--count", "HEAD").Trim());
    private int WorkCommits() => RunGit(RepositoryForTarget(), "log", $"--format=%s", $"HEAD~{CommitCount() - commitsBefore}..HEAD")
        .Split('\n', StringSplitOptions.RemoveEmptyEntries).Count(message => message != "Factory: update plan");
    private string RepositoryForTarget() => RunGit(target, "rev-parse", "--show-toplevel").Trim();
    private static string Snapshot(string path) => Directory.Exists(path)
        ? string.Join("\n", Directory.GetFiles(path, "*", SearchOption.AllDirectories)
            .Where(file => !file.Contains($"{Path.DirectorySeparatorChar}.git{Path.DirectorySeparatorChar}"))
            .Order().Select(file => $"{Path.GetRelativePath(path, file)}:{File.ReadAllText(file)}"))
        : "<missing>";

    private static string RunGit(string directory, params string[] arguments)
    {
        Directory.CreateDirectory(directory);
        var start = new ProcessStartInfo("git")
        {
            WorkingDirectory = directory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        using var process = Process.Start(start)!;
        var stdout = process.StandardOutput.ReadToEnd();
        var stderr = process.StandardError.ReadToEnd();
        process.WaitForExit();
        if (process.ExitCode != 0) throw new InvalidOperationException(stderr);
        return stdout;
    }
}
