using System.Diagnostics;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;

return await FactoryProgram.RunAsync(args);

internal static class FactoryProgram
{
    public static async Task<int> RunAsync(string[] args)
    {
        var options = Options.Parse(args);
        var factory = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../.."));
        if (options.Run is null) return Fail("A run is required.");

        RunConfiguration run;
        try
        {
            run = RunConfiguration.Resolve(factory, options);
        }
        catch (MachineException error) { return Fail(error.Message); }
        if (!File.Exists(run.Seed)) return Fail("There is no seed.");

        Directory.CreateDirectory(run.Target);
        AssemblyLine line;
        try
        {
            line = AssemblyLine.Read(
                Path.Combine(run.Target, ".assembly-lines", $"{run.Line}.dot"),
                Path.Combine(run.Target, ".assembly-lines", ".machines"));
        }
        catch (MachineException error) { return Fail(error.Message); }

        run.Save();
        var repository = Git.FindContainingRepository(run.Target) ?? Git.Initialize(run.Target);
        var plan = Path.Combine(run.Directory, "plan.md");
        var current = line.First;
        var progress = RunProgress.Load(run.Directory);
        var findings = progress.LatestPlanReviewFindings;
        var attempts = 0;
        var planReviewRejections = progress.PlanReviewRejections;
        var updatePlan = false;
        var workWaiting = false;
        string? currentTask = null;
        var reviewContext = "";

        while (current != "finish")
        {
            if (current == "doer" && attempts == options.Attempts)
                return Fail($"A task hit its limit of {options.Attempts} attempts.");
            if (current == "plan-review-dispatch" && planReviewRejections >= options.PlanReviews)
                return Fail(PlanReviewLimitMessage(options.PlanReviews, findings, run));

            var configuration = MachineConfiguration.Read(Path.Combine(
                run.Target, ".assembly-lines", ".machines", current, "config.json"));
            var role = configuration.Role ?? current;
            var planExistedBeforeCall = File.Exists(plan);
            var prompt = Prompt(current, role, run.Seed, plan, configuration.Lens, findings, line.FieldsFrom(current),
                updatePlan, role == "validator" ? Git.TargetDiff(repository, run.Target) : "", currentTask,
                reviewContext);
            MachineResult result;
            try
            {
                result = await Call(configuration.Harness ?? "pi", configuration.Model, run.Target, current, prompt);
            }
            catch (MachineException error) { return Fail(error.Message); }

            if (current == "planner")
            {
                if (!File.Exists(plan)) return Fail("The planner did not write a plan.");
                if (!planExistedBeforeCall && result.TryBoolean("complete", out var complete) && complete)
                    return Fail("The planner cannot complete a run while creating its plan.");
                updatePlan = false;
            }
            else if (role == "task-selector")
            {
                if (!result.TryString("task", out var selectedTask) || string.IsNullOrWhiteSpace(selectedTask))
                    return Fail($"Could not read the {current}'s selected task.");
                currentTask = selectedTask;
            }
            else if (role == "context-selector")
            {
                if (!result.TryString("context", out reviewContext))
                    return Fail($"Could not read the {current}'s review context.");
                findings = result.TryStrings("findings", out var contextFindings) ? contextFindings : [];
            }
            else if (current == "doer")
            {
                attempts++;
                workWaiting = true;
            }
            else if (role == "validator" && !result.TryStrings("findings", out findings))
            {
                return Fail($"Could not read the {current}'s result.");
            }

            try
            {
                if (line.FanOutFrom(current) is { } fanOut)
                {
                    var work = Git.TargetDiff(repository, run.Target);
                    var branchTasks = fanOut.Branches.Select(async branch =>
                    {
                        var branchConfiguration = MachineConfiguration.Read(Path.Combine(
                            run.Target, ".assembly-lines", ".machines", branch, "config.json"));
                        var branchRole = branchConfiguration.Role ?? branch;
                        var branchPrompt = Prompt(branch, branchRole, run.Seed, plan, branchConfiguration.Lens,
                            [], line.FieldsFrom(branch), false, branchRole == "validator" ? work : "", currentTask,
                            reviewContext);
                        var branchResult = await Call(branchConfiguration.Harness ?? "pi", branchConfiguration.Model,
                            run.Target, branch, branchPrompt);
                        if (!branchResult.HasJson)
                            throw new MachineException($"Could not read {branch}'s result.");
                        return new BranchResult(branch, branchResult);
                    }).ToArray();

                    BranchResult[] branchResults;
                    try { branchResults = await Task.WhenAll(branchTasks); }
                    catch (MachineException error) { return Fail(error.Message); }
                    foreach (var branch in branchResults) Console.WriteLine(branch.Result.Json);

                    var joinConfiguration = MachineConfiguration.Read(Path.Combine(
                        run.Target, ".assembly-lines", ".machines", fanOut.Join, "config.json"));
                    var joinRole = joinConfiguration.Role ?? fanOut.Join;
                    var joinPrompt = FanInPrompt(fanOut.Join, joinRole, joinConfiguration.Lens,
                        branchResults, line.FieldsFrom(fanOut.Join));
                    MachineResult joinResult;
                    try
                    {
                        joinResult = await Call(joinConfiguration.Harness ?? "pi", joinConfiguration.Model,
                            run.Target, fanOut.Join, joinPrompt);
                    }
                    catch (MachineException error) { return Fail(error.Message); }
                    if (joinRole == "validator" && !joinResult.TryStrings("findings", out findings))
                        return Fail($"Could not read the {fanOut.Join}'s result.");

                    var nextAfterJoin = line.Next(fanOut.Join, joinResult);
                    if (fanOut.Join == "plan-review-synthesiser")
                    {
                        run.RecordPlanReview(branchResults, joinResult, nextAfterJoin);
                        if (nextAfterJoin == "planner") planReviewRejections++;
                        else
                        {
                            planReviewRejections = 0;
                            findings = [];
                        }
                        RunProgress.Save(run.Directory, new(planReviewRejections, findings));
                        if (nextAfterJoin == "planner" && planReviewRejections >= options.PlanReviews)
                            return Fail(PlanReviewLimitMessage(options.PlanReviews, findings, run));
                    }
                    if (nextAfterJoin == "planner" && workWaiting)
                    {
                        Git.CommitTarget(repository, run.Target, "Factory: completed task");
                        workWaiting = false;
                        updatePlan = true;
                        attempts = 0;
                    }
                    current = nextAfterJoin;
                    Console.WriteLine(joinResult.Json);
                    continue;
                }

                var next = line.Next(current, result);
                if (next == "planner" && workWaiting)
                {
                    Git.CommitTarget(repository, run.Target, "Factory: completed task");
                    workWaiting = false;
                    updatePlan = true;
                    attempts = 0;
                }
                current = next;
            }
            catch (MachineException error) { return Fail(error.Message); }
            Console.WriteLine(result.Json);
        }

        Console.WriteLine("factory stopped");
        return 0;
    }

    private static string PlanReviewLimitMessage(int limit, string[] findings, RunConfiguration run)
    {
        var detail = findings.Length == 0 ? "No findings were retained." : string.Join("; ", findings);
        return $"Plan review hit its persisted limit of {limit} rejections. Latest findings: {detail} " +
               $"See {Path.Combine(run.Directory, "plan-review-latest.json")}.";
    }

    private static string Prompt(string machine, string role, string seed, string plan, string? lens, string[] findings,
        string[] fields, bool updatePlan, string work, string? currentTask, string reviewContext)
    {
        var reviewTask = currentTask ?? (File.Exists(plan) ? TaskContext.ExtractFirstUnfinished(File.ReadAllText(plan)) : "");
        var boundedContext = string.IsNullOrWhiteSpace(reviewContext)
            ? "No machine-resolved acceptance or guidance context was supplied."
            : reviewContext;
        var job = role switch
        {
            "planner" when updatePlan => "The current task's validated work has been committed. Mark that task done.",
            "planner" when findings.Length > 0 => $"Revise only the first unfinished task to resolve these concrete blockers, without doing product work. Keep the task concise: state its outcome, necessary inputs and outputs, and proportionate acceptance evidence. Add bounded local references in backticks on indented `Acceptance:` or `Guidance:` lines. Acceptance references select scenario IDs or Gherkin tags; guidance references select Markdown headings. Do not copy review prose, the original iteration, or reference contents into the plan, add later-stage work, or alter later tasks. If a finding is already covered, make no extra plan entry. Return complete false.\n{string.Join("\n", findings.Select(finding => $"- {finding}"))}",
            "planner" => "If no plan exists, read the delta seed and create a short task list. Each task that reaches review must cite its applicable executable behaviour and implementation guidance using bounded local references in backticks on indented `Acceptance:` and `Guidance:` lines. Acceptance references select JSON scenario IDs or Gherkin tags; guidance references select Markdown headings. Keep earlier iterations as provenance instead of copying their text into this plan. Do no product work. A newly created plan cannot complete the run: return complete false. Otherwise inspect your plan and return complete true only when no work remains.",
            "task-selector" => $"Extract the first unfinished task from the plan without changing any file. Return that task verbatim.\nPLAN_PATH: {plan}",
            "context-selector" => $"Resolve only the bounded Acceptance and Guidance references in this task. Change no files.\nACTIVE_TASK_BEGIN\n{reviewTask}\nACTIVE_TASK_END",
            "doer" => $"Do only the active task below without marking it done. Treat the resolved acceptance scenarios as the everyday behavioural specification; use the original seed or earlier iteration only when the task leaves an explicit provenance or scope question. Record and address these validator findings:\n{string.Join("\n", findings.Select(finding => $"- {finding}"))}\n\nACTIVE TASK:\n{reviewTask}\n\nRESOLVED ACCEPTANCE AND GUIDANCE:\n{boundedContext}",
            "validator" when machine.StartsWith("plan-review-", StringComparison.Ordinal) =>
                $"Review only the active task against its resolved executable acceptance and guidance context. You have intentionally not been given the rest of the plan or the original iteration narrative. Change neither the plan nor product code. A task is implementable when the doer can discover details from its bounded references and source inputs; do not require the task to repeat provenance, precompute hashes or source line references, prescribe implementation internals, or include evidence belonging to later tasks. Reject only a concrete blocker that prevents this task from being implemented or verified now. Optional improvements must not be findings. Your review lens is {lens}.\n\nACTIVE TASK:\n{reviewTask}\n\nRESOLVED ACCEPTANCE AND GUIDANCE:\n{boundedContext}",
            "validator" when machine.StartsWith("code-review-", StringComparison.Ordinal) =>
                $"Review the current uncommitted change against the active task and its resolved executable acceptance and guidance context. You have intentionally not been given the rest of the plan or the original iteration narrative. Change neither the plan nor product code. Your review lens is {lens}.\n\nACTIVE TASK:\n{reviewTask}\n\nRESOLVED ACCEPTANCE AND GUIDANCE:\n{boundedContext}\n\nCURRENT CHANGE:\n{work}",
            "validator" => $"Inspect only the current uncommitted work below. Change neither the plan nor the work. Your validation lens is {lens}.\n{work}",
            _ => "Do your configured job."
        };
        var result = ResultInstruction(fields, role);
        return $"You are the {machine}, with the role {role}. The seed is at {seed} and the plan is at {plan}.\n{job}\n{result}";
    }

    private static string FanInPrompt(string machine, string role, string? lens, BranchResult[] branches, string[] fields)
    {
        var reports = string.Join("\n", branches.Select(branch => $"{branch.Name}: {branch.Result.Json}"));
        var lensInstruction = role == "validator" ? $" Your validation lens is {lens}." : "";
        return $"You are the {machine}, with the role {role}. Synthesise these branch results and nothing else.{lensInstruction}\n{reports}\n{ResultInstruction(fields, role)}";
    }

    private static string ResultInstruction(string[] fields, string role)
    {
        var requested = fields.Concat(role == "validator" ? ["findings"] : []).Distinct().ToArray();
        var result = requested.Length == 0
            ? "End with one line of JSON describing what you did."
            : requested.Length == 1
                ? $"End with one line of JSON containing the field \"{requested[0]}\"."
                : $"End with one line of JSON containing the fields {string.Join(" and ", requested.Select(field => $"\"{field}\""))}.";
        return result;
    }

    private static async Task<MachineResult> Call(string harness, string? model, string target, string machine, string prompt)
    {
        var isPi = Path.GetFileName(harness) == "pi";
        var readsPromptFromStandardInput = isPi || Path.GetFileName(harness) == "openrouter-reviewer";
        var start = new ProcessStartInfo(harness)
        {
            WorkingDirectory = target,
            RedirectStandardInput = readsPromptFromStandardInput,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        if (isPi) start.ArgumentList.Add("-p");
        else
        {
            if (model is not null)
            {
                start.ArgumentList.Add("--model");
                start.ArgumentList.Add(model);
            }
            if (!readsPromptFromStandardInput) start.ArgumentList.Add(prompt);
        }

        try
        {
            using var process = Process.Start(start) ?? throw new MachineException($"Could not run the {machine}.");
            if (readsPromptFromStandardInput)
            {
                await process.StandardInput.WriteAsync(prompt);
                process.StandardInput.Close();
            }
            var outputTask = process.StandardOutput.ReadToEndAsync();
            var errorTask = process.StandardError.ReadToEndAsync();
            await Task.WhenAll(outputTask, errorTask, process.WaitForExitAsync());
            var output = await outputTask;
            var error = await errorTask;
            if (process.ExitCode != 0)
                throw new MachineException($"Could not run the {machine}: {error.Trim()}");
            return MachineResult.From(output);
        }
        catch (System.ComponentModel.Win32Exception error)
        {
            throw new MachineException($"Could not run the {machine}: {error.Message}");
        }
    }

    private static int Fail(string message) { Console.Error.WriteLine(message); return 1; }
}

internal sealed record Edge(string From, string To, string? Label);
internal sealed record FanOut(string[] Branches, string Join);
internal sealed record BranchResult(string Name, MachineResult Result);

internal sealed class AssemblyLine(List<Edge> edges)
{
    public string First => edges.Single(edge => edge.From == "start").To;

    public static AssemblyLine Read(string path, string machinesDirectory)
    {
        var edges = new List<Edge>();
        foreach (var line in File.ReadLines(path))
        {
            var match = Regex.Match(line, "^\\s*([A-Za-z][\\w-]*)\\s*->\\s*([A-Za-z][\\w-]*)(?:\\s*\\[label=\"([^\"]+)\"\\])?");
            if (match.Success) edges.Add(new Edge(match.Groups[1].Value, match.Groups[2].Value,
                match.Groups[3].Success ? match.Groups[3].Value : null));
        }

        var machines = Directory.Exists(machinesDirectory)
            ? Directory.GetDirectories(machinesDirectory).Select(Path.GetFileName).ToHashSet()
            : [];
        foreach (var node in edges.SelectMany(edge => new[] { edge.From, edge.To }).Distinct())
            if (node is not "start" and not "finish" && !machines.Contains(node))
                throw new MachineException($"The factory has no machine called \"{node}\".");

        foreach (var source in edges.Select(edge => edge.From).Distinct())
        {
            var outgoing = edges.Where(edge => edge.From == source).ToArray();
            if (outgoing.Length < 2 || outgoing.All(edge => edge.Label is not null)) continue;
            var branchEdges = outgoing.Select(edge => edges.Where(candidate => candidate.From == edge.To).ToArray()).ToArray();
            if (outgoing.Any(edge => edge.Label is not null) ||
                branchEdges.Any(branch => branch.Length != 1 || branch[0].Label is not null) ||
                branchEdges.Select(branch => branch[0].To).Distinct().Count() != 1)
                throw new MachineException($"The branches from {source} do not meet.");
        }

        foreach (var node in edges.Select(edge => edge.From).Where(node => node != "start").Distinct().Reverse())
            if (!CanReachFinish(node, edges, []))
                throw new MachineException($"Finish cannot be reached from {node}.");

        return new AssemblyLine(edges);
    }

    public string[] FieldsFrom(string machine) => edges.Where(edge => edge.From == machine && edge.Label is not null)
        .Select(edge => edge.Label!.StartsWith("not ") ? edge.Label[4..] : edge.Label)
        .Distinct().ToArray();

    public FanOut? FanOutFrom(string machine)
    {
        var outgoing = edges.Where(edge => edge.From == machine).ToArray();
        if (outgoing.Length < 2 || outgoing.Any(edge => edge.Label is not null)) return null;
        var branches = outgoing.Select(edge => edge.To).ToArray();
        var join = edges.Single(edge => edge.From == branches[0]).To;
        return new FanOut(branches, join);
    }

    public string Next(string machine, MachineResult result)
    {
        var outgoing = edges.Where(edge => edge.From == machine).ToArray();
        var unconditional = outgoing.FirstOrDefault(edge => edge.Label is null);
        if (unconditional is not null) return unconditional.To;
        if (!result.HasJson) throw new MachineException($"Could not read the {machine}'s result.");

        foreach (var edge in outgoing)
        {
            var negative = edge.Label!.StartsWith("not ");
            var field = negative ? edge.Label[4..] : edge.Label;
            if (!result.TryBoolean(field, out var value))
                throw new MachineException($"The result of {machine} has no field \"{field}\".");
            if (value != negative) return edge.To;
        }
        throw new MachineException($"The result of {machine} did not select an edge.");
    }

    private static bool CanReachFinish(string node, List<Edge> edges, HashSet<string> visited)
    {
        if (node == "finish") return true;
        if (!visited.Add(node)) return false;
        return edges.Where(edge => edge.From == node).Any(edge => CanReachFinish(edge.To, edges, new HashSet<string>(visited)));
    }
}

internal sealed record MachineConfiguration(
    [property: JsonPropertyName("harness")] string? Harness,
    [property: JsonPropertyName("lens")] string? Lens,
    [property: JsonPropertyName("role")] string? Role,
    [property: JsonPropertyName("model")] string? Model)
{
    public static MachineConfiguration Read(string path) =>
        JsonSerializer.Deserialize<MachineConfiguration>(File.ReadAllText(path)) ?? new(null, null, null, null);
}

internal sealed record Options(string? Run, string? Seed, string? Target, string? Line, int Attempts, int PlanReviews)
{
    public static Options Parse(string[] args)
    {
        string? run = null;
        string? seed = null;
        string? target = null;
        string? line = null;
        var attempts = 3;
        var planReviews = 3;
        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--run" when index + 1 < args.Length: run = args[++index]; break;
                case "--seed" when index + 1 < args.Length: seed = Path.GetFullPath(args[++index]); break;
                case "--target" when index + 1 < args.Length: target = Path.GetFullPath(args[++index]); break;
                case "--line" when index + 1 < args.Length: line = args[++index]; break;
                case "--attempts" when index + 1 < args.Length: attempts = int.Parse(args[++index]); break;
                case "--plan-reviews" when index + 1 < args.Length: planReviews = int.Parse(args[++index]); break;
            }
        }
        return new Options(run, seed, target, line, attempts, planReviews);
    }
}

internal sealed record RunSettings(
    [property: JsonPropertyName("target")] string Target,
    [property: JsonPropertyName("line")] string Line,
    [property: JsonPropertyName("seed")] string Seed);

internal sealed record RunProgress(
    [property: JsonPropertyName("planReviewRejections")] int PlanReviewRejections,
    [property: JsonPropertyName("latestPlanReviewFindings")] string[] LatestPlanReviewFindings)
{
    public static RunProgress Load(string directory)
    {
        var path = Path.Combine(directory, "progress.json");
        if (!File.Exists(path)) return new(0, []);
        var progress = JsonSerializer.Deserialize<RunProgress>(File.ReadAllText(path));
        return progress is null
            ? new(0, [])
            : new(progress.PlanReviewRejections, progress.LatestPlanReviewFindings ?? []);
    }

    public static void Save(string directory, RunProgress progress)
    {
        Directory.CreateDirectory(directory);
        File.WriteAllText(Path.Combine(directory, "progress.json"),
            JsonSerializer.Serialize(progress, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine);
    }
}

internal sealed record RunConfiguration(string Name, string Directory, string Target, string Line, string Seed)
{
    public static RunConfiguration Resolve(string factory, Options options)
    {
        var directory = Path.Combine(factory, "runs", options.Run!);
        var path = Path.Combine(directory, "run.json");
        if (File.Exists(path))
        {
            var settings = JsonSerializer.Deserialize<RunSettings>(File.ReadAllText(path))
                ?? throw new MachineException($"Could not read the {options.Run} run.");
            if (options.Target is not null && options.Target != settings.Target)
                throw new MachineException($"The \"{options.Run}\" run already has a target.");
            if (options.Line is not null && options.Line != settings.Line)
                throw new MachineException($"The \"{options.Run}\" run already has an assembly line.");
            if (options.Seed is not null && options.Seed != settings.Seed)
                throw new MachineException($"The \"{options.Run}\" run already has a seed.");
            return new(options.Run!, directory, settings.Target, settings.Line, settings.Seed);
        }

        if (options.Target is null) throw new MachineException("A target is required.");
        if (options.Line is null) throw new MachineException("An assembly line is required.");
        if (options.Seed is null) throw new MachineException("There is no seed.");
        return new(options.Run!, directory, options.Target, options.Line, options.Seed);
    }

    public void Save()
    {
        System.IO.Directory.CreateDirectory(Directory);
        var json = JsonSerializer.Serialize(new RunSettings(Target, Line, Seed), new JsonSerializerOptions { WriteIndented = true });
        File.WriteAllText(Path.Combine(Directory, "run.json"), json + Environment.NewLine);
    }

    public void RecordPlanReview(BranchResult[] branches, MachineResult synthesis, string next)
    {
        var reviewDirectory = Path.Combine(Directory, "plan-reviews");
        System.IO.Directory.CreateDirectory(reviewDirectory);
        var number = System.IO.Directory.GetFiles(reviewDirectory, "*.json").Count(path =>
            Path.GetFileNameWithoutExtension(path).All(char.IsDigit)) + 1;
        var report = JsonSerializer.Serialize(new
        {
            review = number,
            outcome = next == "planner" ? "rejected" : "accepted",
            branches = branches.Select(branch => new { machine = branch.Name, result = branch.Result.Json }),
            synthesis = synthesis.Json
        }, new JsonSerializerOptions { WriteIndented = true }) + Environment.NewLine;
        File.WriteAllText(Path.Combine(reviewDirectory, $"{number:0000}.json"), report);
        File.WriteAllText(Path.Combine(Directory, "plan-review-latest.json"), report);
    }
}

internal sealed record MachineResult(JsonElement? Root, string Json)
{
    public bool HasJson => Root is not null;
    public static MachineResult From(string output)
    {
        foreach (var line in output.Split('\n').Reverse())
        {
            try
            {
                using var document = JsonDocument.Parse(line);
                return new MachineResult(document.RootElement.Clone(), line.Trim());
            }
            catch (JsonException) { }
        }

        // Some harnesses format their final object across several lines or in a
        // Markdown fence. Try JSON object suffixes as a fallback while still
        // preferring the final one-line result contract above.
        var end = output.LastIndexOf('}');
        var start = end >= 0 ? output.LastIndexOf('{', end) : -1;
        while (start >= 0)
        {
            try
            {
                var candidate = output[start..(end + 1)];
                using var document = JsonDocument.Parse(candidate);
                return new MachineResult(document.RootElement.Clone(), candidate.Trim());
            }
            catch (JsonException) { }
            if (start == 0) break;
            start = output.LastIndexOf('{', start - 1);
        }
        return new MachineResult(null, "");
    }

    public bool TryBoolean(string name, out bool value)
    {
        value = false;
        return Root is { } root && root.TryGetProperty(name, out var element) &&
               element.ValueKind is JsonValueKind.True or JsonValueKind.False && (value = element.GetBoolean()) == value;
    }

    public bool TryStrings(string name, out string[] values)
    {
        values = [];
        if (Root is not { } root || !root.TryGetProperty(name, out var element) || element.ValueKind != JsonValueKind.Array)
            return false;
        values = element.EnumerateArray()
            .Select(item => item.ValueKind == JsonValueKind.String
                ? item.GetString() ?? ""
                : item.GetRawText())
            .ToArray();
        return true;
    }

    public bool TryString(string name, out string value)
    {
        value = "";
        if (Root is not { } root || !root.TryGetProperty(name, out var element) ||
            element.ValueKind != JsonValueKind.String)
            return false;
        value = element.GetString() ?? "";
        return true;
    }
}

internal static class TaskContext
{
    private static readonly Regex Checkbox = new(@"^(?<indent>\s*)[-*+]\s+\[(?<state>[ xX])\]\s+", RegexOptions.Compiled);

    public static string ExtractFirstUnfinished(string plan)
    {
        var lines = plan.Replace("\r\n", "\n").Split('\n');
        for (var index = 0; index < lines.Length; index++)
        {
            var match = Checkbox.Match(lines[index]);
            if (!match.Success || !string.IsNullOrWhiteSpace(match.Groups["state"].Value)) continue;

            var indent = match.Groups["indent"].Value.Length;
            var task = new List<string> { lines[index] };
            for (var next = index + 1; next < lines.Length; next++)
            {
                var nextMatch = Checkbox.Match(lines[next]);
                if (nextMatch.Success && nextMatch.Groups["indent"].Value.Length <= indent) break;
                task.Add(lines[next]);
            }
            while (task.Count > 1 && string.IsNullOrWhiteSpace(task[^1])) task.RemoveAt(task.Count - 1);
            return string.Join("\n", task);
        }
        return "";
    }
}

internal sealed class MachineException(string message) : Exception(message);

internal static class Git
{
    public static string? FindContainingRepository(string target)
    {
        var result = Run(target, "rev-parse", "--show-toplevel");
        return result.ExitCode == 0 ? result.Output.Trim() : null;
    }

    public static string Initialize(string target)
    {
        RunChecked(target, "init", "--quiet");
        RunChecked(target, "config", "user.email", "factory@example.invalid");
        RunChecked(target, "config", "user.name", "Software Factory");
        return target;
    }

    public static bool HasTargetChanges(string repository, string target) =>
        !string.IsNullOrWhiteSpace(RunChecked(repository, "status", "--porcelain", "--untracked-files=all", "--",
            Pathspec(repository, target), AssemblyLinesExclusion(repository, target)));

    public static string TargetDiff(string repository, string target)
    {
        var pathspec = Pathspec(repository, target);
        var exclusion = AssemblyLinesExclusion(repository, target);
        var baseline = Run(repository, "rev-parse", "--verify", "HEAD").ExitCode == 0 ? new[] { "HEAD" } : [];
        var tracked = RunChecked(repository, ["diff", .. baseline, "--", pathspec, exclusion]);
        var status = RunChecked(repository, "status", "--short", "--untracked-files=all", "--", pathspec, exclusion);
        if (tracked.Length <= 250_000)
            return tracked + "\nChanged and untracked files:\n" + status;

        var summary = RunChecked(repository, ["diff", .. baseline, "--stat", "--", pathspec, exclusion]);
        var reviewable = RunChecked(repository, ["diff", .. baseline, "--", pathspec, exclusion,
            DescendantExclusion(repository, target, "evidence"),
            DescendantExclusion(repository, target, "bin"),
            DescendantExclusion(repository, target, "obj")]);
        if (reviewable.Length > 250_000)
            reviewable = RunChecked(repository, ["diff", .. baseline, "--name-status", "--", pathspec, exclusion]);
        return $"The complete tracked patch is {tracked.Length} bytes, so bulk evidence/build contents are omitted from this prompt. " +
               "Inspect listed files directly when their contents matter.\n\nCHANGE SUMMARY:\n" + summary +
               "\nCHANGED AND UNTRACKED FILES:\n" + status + "\nREVIEWABLE PATCH:\n" + reviewable;
    }

    public static void CommitTarget(string repository, string target, string message)
    {
        var pathspec = Pathspec(repository, target);
        if (!HasTargetChanges(repository, target)) return;
        var exclusion = AssemblyLinesExclusion(repository, target);
        RunChecked(repository, "add", "--", pathspec, exclusion);
        RunChecked(repository, "commit", "--quiet", "--only", "-m", message, "--", pathspec, exclusion);
    }

    private static string Pathspec(string repository, string target) =>
        Path.GetRelativePath(repository, target) is "." ? "." : Path.GetRelativePath(repository, target);

    private static string AssemblyLinesExclusion(string repository, string target)
    {
        var path = Path.GetRelativePath(repository, Path.Combine(target, ".assembly-lines"));
        return $":(exclude){path}";
    }

    private static string DescendantExclusion(string repository, string target, string directory)
    {
        var path = Pathspec(repository, target);
        var prefix = path == "." ? "" : path.Replace('\\', '/') + "/";
        return $":(exclude){prefix}**/{directory}/**";
    }

    private static string RunChecked(string directory, params string[] arguments)
    {
        var result = Run(directory, arguments);
        if (result.ExitCode != 0) throw new InvalidOperationException(result.Error);
        return result.Output;
    }

    private static CommandResult Run(string directory, params string[] arguments)
    {
        var start = new ProcessStartInfo("git") { WorkingDirectory = directory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false };
        foreach (var argument in arguments) start.ArgumentList.Add(argument);
        using var process = Process.Start(start)!;
        var output = process.StandardOutput.ReadToEnd();
        var error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return new CommandResult(process.ExitCode, output, error);
    }

    private sealed record CommandResult(int ExitCode, string Output, string Error);
}
