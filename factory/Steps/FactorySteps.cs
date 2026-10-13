using System.Diagnostics;
using System.Text.Json;
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
    private string runName = "tetris";
    private string lineName = "careful";
    private string output = "";
    private int exitCode;
    private int commitsBefore;
    private bool omitTarget;
    private bool omitSeed;
    private bool answerInProse;
    private bool prosePlan;
    private bool writeSentinel;
    private bool talkFirst;
    private bool validatorNeverSatisfied;
    private bool validatorFailsFirst;
    private int attempts = 3;
    private string lens = "testability";
    private string? statusBefore;
    private readonly Dictionary<string, string> snapshots = [];
    private readonly Dictionary<string, RunDefinition> runs = [];

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

        agent = WriteAgent("chosen-agent", "chosen");
        WriteAgent("pi", "pi");

        RunGit(repository, "init", "--quiet");
        RunGit(repository, "config", "user.email", "test@example.invalid");
        RunGit(repository, "config", "user.name", "Factory Test");
        RunGit(repository, "add", ".");
        RunGit(repository, "commit", "--quiet", "-m", "test workspace");

    }

    [Given("a new target")]
    public void NewTarget() => Directory.CreateDirectory(target);

    [Given("a new target, with a seed describing a game of Tetris")]
    public void NewTetrisTarget()
    {
        target = Path.Combine(repository, runs.Count == 0 ? "output" : $"output-{runs.Count + 1}");
        seed = Path.Combine(repository, runs.Count == 0 ? "seed.md" : $"seed-{runs.Count + 1}.md");
        Directory.CreateDirectory(target);
        File.WriteAllText(seed, "Build a game of Tetris.\n");
    }

    [Given("a new target, with a seed describing a game of Snake")]
    public void NewSnakeTarget()
    {
        target = Path.Combine(repository, "snake-output");
        seed = Path.Combine(repository, "snake-seed.md");
        Directory.CreateDirectory(target);
        File.WriteAllText(seed, "Build a game of Snake.\n");
    }

    [Given("a seed describing a game of Tetris")]
    public void TetrisSeed() => File.WriteAllText(seed, "Build a game of Tetris.\n");

    [Given("the planner plans the tasks alpha and beta")]
    public void ConfigurePlanner() { }

    [Given("the doer does the next task in the plan")]
    public void ConfigureDoer() { }

    [Given("the validator is always satisfied")]
    public void ConfigureValidator() { }

    [Given("the target has the machines planner, doer and validator")]
    public void TargetHasMachines()
    {
        WriteMachineConfig("planner", agent);
        WriteMachineConfig("doer", agent);
        WriteMachineConfig("validator", agent, "testability");
    }

    [Given("the target has an assembly line {string} on which the doer's work is validated")]
    public void TargetHasValidatedLine(string name)
    {
        lineName = name;
        WriteLine(name, ValidatedLine());
    }

    [Given("the target has an assembly line {string} on which the doer goes straight to the planner")]
    public void TargetHasQuickLine(string name) => WriteLine(name, QuickLine());

    [Given("a run named {string}, on the {string} line, with that seed and target")]
    public void NamedRun(string name, string line)
    {
        runName = name;
        runs[name] = new(target, seed, line);
    }

    [Given("this assembly line:")]
    public void ThisAssemblyLine(string graph) => WriteLine(lineName, graph);

    [Given("the validator has been taken out, so the doer goes straight to the planner")]
    public void RemoveValidatorFromAssemblyLine()
    {
        var path = LinePath(lineName);
        var graph = File.ReadAllLines(path)
            .Where(line => !line.Contains("validator ->"))
            .Select(line => line.Replace("doer -> validator", "doer -> planner"));
        File.WriteAllLines(path, graph);
    }

    [Given("the validator has been taken out of the {string} line, so the doer goes straight to the planner")]
    public void RemoveValidatorFromNamedLine(string name)
    {
        lineName = name;
        RemoveValidatorFromAssemblyLine();
    }

    [Given("{string} is misspelt {string} throughout the assembly line")]
    public void MisspellMachineInAssemblyLine(string machine, string misspelling)
    {
        var path = LinePath(lineName);
        File.WriteAllText(path, File.ReadAllText(path).Replace(machine, misspelling));
    }

    [Given("{string} is misspelt {string} throughout the {string} line")]
    public void MisspellMachineInNamedLine(string machine, string misspelling, string line)
    {
        lineName = line;
        MisspellMachineInAssemblyLine(machine, misspelling);
    }

    [Given("the {string} line has been copied into the target")]
    public void CopyLineIntoTarget(string name)
    {
        var source = runs["tetris"].Target;
        Directory.CreateDirectory(Path.GetDirectoryName(LinePath(name))!);
        File.Copy(Path.Combine(source, ".assembly-lines", $"{name}.dot"), LinePath(name), true);
    }

    [Given("the edge from validator to planner has been taken out")]
    public void RemoveValidatorToPlannerEdge()
    {
        var path = LinePath(lineName);
        File.WriteAllLines(path, File.ReadAllLines(path).Where(line => !line.Contains("validator -> planner")));
    }

    [Given("the edges from validator are labelled {string} and {string}")]
    public void RelabelValidatorEdges(string positive, string negative)
    {
        var path = LinePath(lineName);
        var graph = File.ReadAllText(path)
            .Replace("label=\"not satisfied\"", $"label=\"{negative}\"")
            .Replace("label=\"satisfied\"", $"label=\"{positive}\"");
        File.WriteAllText(path, graph);
    }

    [Given("no harness is chosen")]
    public void NoHarness() { }

    [Given("no harness is chosen for the validator")]
    public void NoValidatorHarness() => WriteMachineConfig("validator", lens: lens);

    [Given("the agent is pi")]
    public void AgentIsPi() => EveryMachineRunsPi();

    [Given("every machine runs pi")]
    public void EveryMachineRunsPi()
    {
        WriteMachineConfig("planner", "pi");
        WriteMachineConfig("doer", "pi");
        WriteMachineConfig("validator", "pi", lens);
    }

    [Given("the doer cannot be run")]
    public void DoerCannotRun()
    {
        WriteMachineConfig("doer", Path.Combine(fakeBin, "missing-harness"));
    }

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

    [Given("a plan for each run with three tasks of its own, none of them done")]
    public void PlanForEachRun()
    {
        foreach (var name in runs.Keys) WritePlan("- [ ] alpha\n- [ ] beta\n- [ ] gamma\n", name);
    }

    [Given("the {string} run has been started")]
    public void RunHasStarted(string name)
    {
        runName = name;
        WriteRunSettings(name, runs[name]);
    }

    [Given("the doer writes a file called SENTINEL")]
    public void DoerWritesSentinel() => writeSentinel = true;

    [Given("the validator says {string} before its result")]
    public void ValidatorTalks(string _) => talkFirst = true;

    [Given("the validator answers in prose, with no result")]
    public void ValidatorAnswersInProse() => answerInProse = true;

    [Given("the planner keeps its plan in prose")]
    public void PlannerKeepsProsePlan() => prosePlan = true;

    [Given("the doer keeps its plan in prose")]
    public void DoerKeepsProsePlan() => prosePlan = true;

    [Given("the validator is never satisfied")]
    public void ValidatorNeverSatisfied() => validatorNeverSatisfied = true;

    [Given("the validator is not satisfied the first time")]
    public void ValidatorFailsFirst() => validatorFailsFirst = true;

    [Given("the factory allows at most three attempts per pass")]
    public void ThreeAttempts() => attempts = 3;

    [Given("the factory allows at most three attempts at a task")]
    public void ThreeTaskAttempts() => attempts = 3;

    [Given("the validator's lens is {word}")]
    public void ValidatorLens(string chosenLens)
    {
        lens = chosenLens;
        WriteMachineConfig("validator", agent, lens);
    }

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
        var previous = target;
        target = Path.Combine(workspace, "standalone");
        CopyDirectory(Path.Combine(previous, ".assembly-lines"), Path.Combine(target, ".assembly-lines"));
        runs[runName] = runs[runName] with { Target = target };
    }

    [Given("the factory has staged and unstaged changes")]
    public void UnrelatedChanges()
    {
        RunGit(repository, "add", Path.GetRelativePath(repository, Path.Combine(target, ".assembly-lines")),
            Path.GetRelativePath(repository, seed));
        RunGit(repository, "commit", "--quiet", "-m", "test target configuration");
        File.WriteAllText(Path.Combine(repository, "staged.txt"), "staged");
        RunGit(repository, "add", "staged.txt");
        File.WriteAllText(Path.Combine(repository, "unstaged.txt"), "unstaged");
        statusBefore = RunGit(repository, "status", "--porcelain");
    }

    [When("the factory runs one pass")]
    public void RunOnePass() => RunNamedFactory(runName);

    [When("the factory runs to completion")]
    public void RunToCompletion() => RunNamedFactory(runName);

    [When("the factory runs")]
    public void RunAssemblyLine() => RunNamedFactory(runName);

    [When("the factory runs the {string} run")]
    public void RunNamedFactory(string name)
    {
        runName = name;
        RunFactory(name, includeSettings: true);
    }

    [When("the factory runs the {string} run, given only its name")]
    public void RunByNameOnly(string name)
    {
        runName = name;
        RunFactory(name, includeSettings: false);
    }

    [When("the factory runs the {string} run with that target")]
    public void RunWithCurrentTarget(string name)
    {
        runName = name;
        RunFactory(name, includeSettings: false, targetOverride: target);
    }

    [When("the factory reads the assembly line")]
    public void ReadAssemblyLine()
    {
        const string name = "line-check";
        runs[name] = new(target, seed, lineName);
        RunNamedFactory(name);
    }

    [When("the factory builds the target {string} to completion")]
    public void BuildNamedTarget(string name)
    {
        var namedTarget = Path.Combine(repository, name);
        runs[name] = new(namedTarget, seed, lineName);
        RunNamedFactory(name);
        snapshots[name] = Snapshot(namedTarget);
    }

    [When("the factory builds the same target using its absolute path")]
    public void BuildSameTargetAbsolute()
    {
        var namedTarget = Path.Combine(repository, "a-generation");
        snapshots["a-generation-before"] = Snapshot(namedTarget);
        runs["a-generation"] = new(namedTarget, seed, lineName);
        RunNamedFactory("a-generation");
    }

    [Then("pi has been called")]
    public void PiCalled() => Assert.That(CallCount("pi"), Is.GreaterThan(0));

    [Then("the doer's chosen harness has been called")]
    public void ChosenCalled() => Assert.That(RoleCallCount("chosen", "doer"), Is.GreaterThan(0));

    [Then("it accepts it")]
    public void AcceptsAssemblyLine() => Assert.That(exitCode, Is.Zero, output);

    [Then("it refuses it")]
    public void RefusesAssemblyLine() => Assert.That(exitCode, Is.Not.Zero, output);

    [Then("the factory refuses")]
    public void FactoryRefuses() => Assert.That(exitCode, Is.Not.Zero, output);

    [Then("it says the {string} run already has a target")]
    public void ReportsRunAlreadyHasTarget(string name) =>
        Assert.That(output, Does.Contain($"\"{name}\" run already has a target").IgnoreCase);

    [Then("it reports that it has no machine called {string}")]
    public void ReportsMissingMachine(string machine) =>
        Assert.That(output, Does.Contain($"no machine called \"{machine}\"").IgnoreCase);

    [Then("it reports that finish cannot be reached from validator")]
    public void ReportsUnreachableFinish() =>
        Assert.That(output, Does.Contain("finish cannot be reached from validator").IgnoreCase);

    [Then("pi has not been called")]
    public void PiNotCalled() => Assert.That(CallCount("pi"), Is.Zero);

    [Then("no agent has been called")]
    public void NoAgentCalled() => Assert.That(TotalCalls(), Is.Zero);

    [Then("the doer has been called once")]
    public void DoerCalledOnce() => Assert.That(RoleCallCount("chosen", "doer") + RoleCallCount("pi", "doer"), Is.EqualTo(1));

    [Then("the doer has been called twice")]
    public void DoerCalledTwice() => Assert.That(RoleCallCount("chosen", "doer") + RoleCallCount("pi", "doer"), Is.EqualTo(2));

    [Then("the doer has been called three times")]
    public void DoerCalledThreeTimes() => Assert.That(RoleCallCount("chosen", "doer") + RoleCallCount("pi", "doer"), Is.EqualTo(3));

    [Then("the doer has been called four times")]
    public void DoerCalledFourTimes() => Assert.That(RoleCallCount("chosen", "doer") + RoleCallCount("pi", "doer"), Is.EqualTo(4));

    [Then("the doer has not been called")]
    public void DoerNotCalled() => Assert.That(RoleCallCount("chosen", "doer") + RoleCallCount("pi", "doer"), Is.Zero);

    [Then("the validator has not been called")]
    public void ValidatorNotCalled() =>
        Assert.That(RoleCallCount("chosen", "validator") + RoleCallCount("pi", "validator"), Is.Zero);

    [Then("the validator was called for the {string} run")]
    public void ValidatorCalledForRun(string name) => Assert.That(RunRoleCallCount(name, "validator"), Is.GreaterThan(0));

    [Then("the validator was not called for the {string} run")]
    public void ValidatorNotCalledForRun(string name) => Assert.That(RunRoleCallCount(name, "validator"), Is.Zero);

    [Then("it reports that it could not run the doer")]
    public void ReportsDoerFailure() => Assert.That(output, Does.Contain("Could not run the doer"));

    [Then("it reports that it could not read the validator's result")]
    public void ReportsUnreadableResult() => Assert.That(output, Does.Contain("Could not read the validator's result"));

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
    public void EveryTaskNotDone() => Assert.That(
        File.ReadAllLines(PlanPath()).Where(line => line.StartsWith("- ")),
        Has.All.Contains("[ ]"));

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

    [Then("the plan is plan.md in the factory's runs folder, under tetris")]
    public void PlanInRunsFolder()
    {
        Assert.That(PlanPath(), Is.EqualTo(Path.Combine(factory, "runs", "tetris", "plan.md")));
        Assert.That(File.Exists(PlanPath()), Is.True);
    }

    [Then("there is no plan in the target")]
    public void NoPlanInTarget() => Assert.That(File.Exists(Path.Combine(target, ".factory", "plan.md")), Is.False);

    [Then("there is no plan in the factory's folder")]
    public void NoPlanInFactory() => Assert.That(File.Exists(Path.Combine(factory, ".factory", "plan.md")), Is.False);

    [Then("there is one new work commit")]
    public void OneWorkCommit() => Assert.That(WorkCommits(), Is.EqualTo(1));

    [Then("there are three new work commits")]
    public void ThreeWorkCommits() => Assert.That(WorkCommits(), Is.EqualTo(3), output);

    [Then("there are two new work commits")]
    public void TwoWorkCommits() => Assert.That(WorkCommits(), Is.EqualTo(2), output);

    [Then("each new work commit contains the work for one task")]
    public void EachWorkCommitContainsOneTask()
    {
        var repo = RepositoryForTarget();
        var messages = RunGit(repo, "log", "--format=%H%x09%s", NewCommitsRange())
            .Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Where(line => !line.EndsWith("Factory: update plan"));
        foreach (var message in messages)
        {
            var hash = message.Split('\t')[0];
            var files = RunGit(repo, "show", "--format=", "--name-only", hash)
                .Split('\n', StringSplitOptions.RemoveEmptyEntries)
                .Where(file => !file.EndsWith(".factory/plan.md"))
                .ToArray();
            Assert.That(files, Has.Length.EqualTo(1));
        }
    }

    [Then("there are no new commits")]
    public void NoNewCommits() => Assert.That(CommitCount(), Is.EqualTo(commitsBefore));

    [Then("there are no new work commits")]
    public void NoNewWorkCommits() => Assert.That(WorkCommits(), Is.Zero);

    [Then("no new commit contains the work for the first task")]
    public void NoCommitContainsFirstTaskWork()
    {
        var repo = RepositoryForTarget();
        var files = RunGit(repo, "log", "--name-only", "--format=", NewCommitsRange());
        Assert.That(files, Does.Not.Contain("alpha.txt"));
    }

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

    [Then("the doer was pointed at the plan and at the seed")]
    public void PromptHasPaths()
    {
        var prompt = LastPrompt("doer");
        Assert.Multiple(() =>
        {
            Assert.That(prompt, Does.Contain(Path.GetFullPath(seed)));
            Assert.That(prompt, Does.Contain(Path.GetFullPath(PlanPath())));
        });
    }

    [Then("the planner was asked for a result with the field {string}")]
    public void PlannerPromptAsksForField(string field) => Assert.That(LastPrompt("planner"), Does.Contain($"field \"{field}\""));

    [Then("the validator was asked for a result with the fields {string} and {string}")]
    public void ValidatorPromptAsksForFields(string first, string second)
    {
        Assert.That(LastPrompt("validator"), Does.Contain($"\"{first}\"").And.Contain($"\"{second}\""));
    }

    [Then("it reports that the pass hit its limit")]
    public void ReportsLimit() => Assert.That(output, Does.Contain("hit its limit"));

    [Then("it reports that a task hit its limit")]
    public void ReportsTaskLimit() => Assert.That(output, Does.Contain("task hit its limit").IgnoreCase);

    [Then("it reports that the result of validator has no field {string}")]
    public void ReportsMissingResultField(string field) =>
        Assert.That(output, Does.Contain($"result of validator has no field \"{field}\"").IgnoreCase);

    [Then("the validator was given the work for the second task")]
    public void ValidatorGivenSecondWork() => Assert.That(FirstPrompt("validator"), Does.Contain("beta.txt"));

    [Then("it was not given the work for the first task")]
    public void ValidatorNotGivenFirstWork() => Assert.That(FirstPrompt("validator"), Does.Not.Contain("alpha.txt"));

    [Then("the validator was given {string}")]
    public void ValidatorGivenLens(string expected) => Assert.That(LastPrompt("validator"), Does.Contain(expected));

    [Then("the doer was given the validator's findings")]
    public void DoerGivenFindings() => Assert.That(
        Directory.GetFiles(calls, "*-doer-*.prompt").Any(path => File.ReadAllText(path).Contains("needs tests")), Is.True);

    [Then("the planner was called before the doer")]
    public void PlannerCalledBeforeDoer()
    {
        var plannerCall = Directory.GetFiles(calls, "*-planner-*.prompt").Min(File.GetCreationTimeUtc);
        var doerCall = Directory.GetFiles(calls, "*-doer-*.prompt").Min(File.GetCreationTimeUtc);
        Assert.That(plannerCall, Is.LessThanOrEqualTo(doerCall));
    }

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

    [Then("each run has its own plan")]
    public void EachRunHasOwnPlan()
    {
        foreach (var name in runs.Keys)
        {
            var path = PlanPath(name);
            Assert.That(File.Exists(path), Is.True, name);
            Assert.That(File.ReadAllLines(path), Has.All.Contains("[x]"), name);
        }
    }

    [Then("each target holds only its own run's work")]
    public void EachTargetHasOwnWork()
    {
        foreach (var (name, definition) in runs)
        {
            Assert.That(File.Exists(Path.Combine(definition.Target, "alpha.txt")), Is.True, name);
            Assert.That(File.ReadAllText(Path.Combine(definition.Target, "alpha.txt")), Does.StartWith($"{name}:"), name);
        }
        Assert.That(runs.Values.Select(run => run.Target), Is.Unique);
    }

    [AfterScenario]
    public void Cleanup()
    {
        if (Directory.Exists(workspace)) Directory.Delete(workspace, true);
    }

    private void RunFactory(string name, bool includeSettings, string? targetOverride = null)
    {
        var definition = runs[name];
        var selectedTarget = targetOverride ?? definition.Target;
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
        start.ArgumentList.Add("--run");
        start.ArgumentList.Add(name);
        if (includeSettings && !omitSeed)
        {
            start.ArgumentList.Add("--seed");
            start.ArgumentList.Add(definition.Seed);
        }
        if ((includeSettings || targetOverride is not null) && !omitTarget)
        {
            start.ArgumentList.Add("--target");
            start.ArgumentList.Add(selectedTarget);
        }
        if (includeSettings)
        {
            start.ArgumentList.Add("--line");
            start.ArgumentList.Add(definition.Line);
        }
        start.ArgumentList.Add("--attempts");
        start.ArgumentList.Add(attempts.ToString());
        start.Environment["PATH"] = $"{fakeBin}:{Environment.GetEnvironmentVariable("PATH")}";
        start.Environment["FACTORY_CALLS"] = calls;
        start.Environment["FACTORY_ANSWER_PROSE"] = answerInProse ? "1" : "0";
        start.Environment["FACTORY_PROSE_PLAN"] = prosePlan ? "1" : "0";
        start.Environment["FACTORY_SENTINEL"] = writeSentinel ? "1" : "0";
        start.Environment["FACTORY_TALK"] = talkFirst ? "1" : "0";
        start.Environment["FACTORY_NEVER_SATISFIED"] = validatorNeverSatisfied ? "1" : "0";
        start.Environment["FACTORY_FAIL_FIRST"] = validatorFailsFirst ? "1" : "0";
        start.Environment["FACTORY_TEST_RUN"] = name;

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
            prompt="$*"
            role=$(printf '%s' "$prompt" | sed -n 's/.*You are the \(planner\|doer\|validator\).*/\1/p' | head -1)
            number=$(($(find "$FACTORY_CALLS" -name '{{identity}}-'"$FACTORY_TEST_RUN"'-'"$role"'-*.prompt' | wc -l) + 1))
            printf '%s' "$prompt" > "$FACTORY_CALLS/{{identity}}-$FACTORY_TEST_RUN-$role-$number.prompt"
            plan=$(printf '%s\n' "$prompt" | sed -n 's/^You are .* and the plan is at \(.*\)\.$/\1/p' | head -1)
            mkdir -p "$(dirname "$plan")"

            if [ "$role" = planner ]; then
              if [ ! -f "$plan" ]; then
                if [ "$FACTORY_PROSE_PLAN" = 1 ]; then printf 'alpha is pending\nbeta is pending\n' > "$plan";
                else printf '%s\n' '- [ ] alpha' '- [ ] beta' > "$plan"; fi
                echo '{"complete":false}'; exit 0
              fi
              if printf '%s' "$prompt" | grep -q 'validated work has been committed'; then
                if grep -q '\[ \]' "$plan"; then sed -i '0,/\[ \]/{s/\[ \]/[x]/}' "$plan";
                elif grep -q ' is pending' "$plan"; then task=$(grep ' is pending' "$plan" | head -1 | sed 's/ is pending//'); sed -i "0,/$task is pending/{s/$task is pending/$task is done/}" "$plan"; fi
              fi
              if grep -Eq '\[ \]| is pending' "$plan"; then echo '{"complete":false}'; else echo '{"complete":true}'; fi
              exit 0
            fi

            if [ "$role" = doer ]; then
              if grep -q '\[ \]' "$plan"; then task=$(grep '\[ \]' "$plan" | head -1 | sed 's/.*] //');
              else task=$(grep ' is pending' "$plan" | head -1 | sed 's/ is pending//'); fi
              if [ "$FACTORY_SENTINEL" = 1 ]; then touch SENTINEL; else printf '%s: %s\n' "$FACTORY_TEST_RUN" "$task" > "$task.txt"; fi
              if printf '%s' "$prompt" | grep -q 'needs tests'; then printf '  - validator: needs tests\n' >> "$plan"; fi
              echo '{"worked":true}'; exit 0
            fi

            if [ "$FACTORY_ANSWER_PROSE" = 1 ]; then echo 'I cannot provide a result'; exit 0; fi
            [ "$FACTORY_TALK" = 1 ] && echo 'looks good to me'
            validation_number=$(find "$FACTORY_CALLS" -name '{{identity}}-'"$FACTORY_TEST_RUN"'-validator-*.prompt' | wc -l)
            if [ "$FACTORY_NEVER_SATISFIED" = 1 ] || { [ "$FACTORY_FAIL_FIRST" = 1 ] && [ "$validation_number" -eq 1 ]; }; then
              echo '{"satisfied":false,"findings":["needs tests"]}'
            else
              echo '{"satisfied":true,"findings":[]}'
            fi
            """);
        File.SetUnixFileMode(path, UnixFileMode.UserRead | UnixFileMode.UserWrite | UnixFileMode.UserExecute);
        return path;
    }

    private void WriteMachineConfig(string name, string? harness = null, string? lens = null)
    {
        var machine = Path.Combine(target, ".assembly-lines", ".machines", name);
        Directory.CreateDirectory(machine);
        File.WriteAllText(Path.Combine(machine, "config.json"), JsonSerializer.Serialize(new { harness, lens }));
    }

    private void WritePlan(string text, string? name = null)
    {
        var path = PlanPath(name ?? runName);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, text);
    }

    private string PlanPath() => PlanPath(runName);
    private string PlanPath(string name) => Path.Combine(factory, "runs", name, "plan.md");
    private int CallCount(string identity) => Directory.GetFiles(calls, $"{identity}-*.prompt").Length;
    private int RoleCallCount(string identity, string role) => Directory.GetFiles(calls, $"{identity}-*-{role}-*.prompt").Length;
    private int RunRoleCallCount(string name, string role) => Directory.GetFiles(calls, $"*-{name}-{role}-*.prompt").Length;
    private int TotalCalls() => Directory.GetFiles(calls, "*.prompt").Length;
    private string LastPrompt(string role) => File.ReadAllText(Directory.GetFiles(calls, $"*-*-{role}-*.prompt").Order().Last());
    private string FirstPrompt(string role) => File.ReadAllText(Directory.GetFiles(calls, $"*-*-{role}-*.prompt").Order().First());
    private int CommitCount() => int.Parse(RunGit(RepositoryForTarget(), "rev-list", "--count", "HEAD").Trim());
    private int WorkCommits() => RunGit(RepositoryForTarget(), "log", $"--format=%s", NewCommitsRange())
        .Split('\n', StringSplitOptions.RemoveEmptyEntries).Count(message => message != "Factory: update plan");
    private string NewCommitsRange()
    {
        var count = CommitCount() - commitsBefore;
        return commitsBefore == 0 ? "HEAD" : $"HEAD~{count}..HEAD";
    }
    private string RepositoryForTarget() => RunGit(target, "rev-parse", "--show-toplevel").Trim();

    private string LinePath(string name) => Path.Combine(target, ".assembly-lines", $"{name}.dot");

    private void WriteLine(string name, string graph)
    {
        var path = LinePath(name);
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        File.WriteAllText(path, graph);
    }

    private void WriteRunSettings(string name, RunDefinition definition)
    {
        var directory = Path.Combine(factory, "runs", name);
        Directory.CreateDirectory(directory);
        File.WriteAllText(Path.Combine(directory, "run.json"), JsonSerializer.Serialize(new
        {
            target = definition.Target,
            line = definition.Line,
            seed = definition.Seed
        }));
    }

    private static string ValidatedLine() => """
        digraph assembly_line {
          start -> planner
          planner -> doer        [label="not complete"]
          planner -> finish      [label="complete"]
          doer -> validator
          validator -> doer      [label="not satisfied"]
          validator -> planner   [label="satisfied"]
        }
        """;

    private static string QuickLine() => """
        digraph assembly_line {
          start -> planner
          planner -> doer   [label="not complete"]
          planner -> finish [label="complete"]
          doer -> planner
        }
        """;

    private static void CopyDirectory(string source, string destination)
    {
        Directory.CreateDirectory(destination);
        foreach (var file in Directory.GetFiles(source)) File.Copy(file, Path.Combine(destination, Path.GetFileName(file)));
        foreach (var directory in Directory.GetDirectories(source))
            CopyDirectory(directory, Path.Combine(destination, Path.GetFileName(directory)));
    }

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

    private sealed record RunDefinition(string Target, string Seed, string Line);
}
