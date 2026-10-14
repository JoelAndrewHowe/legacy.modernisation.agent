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
        var findings = Array.Empty<string>();
        var attempts = 0;
        var updatePlan = false;
        var workWaiting = false;

        while (current != "finish")
        {
            if (current == "doer" && attempts == options.Attempts)
                return Fail($"A task hit its limit of {options.Attempts} attempts.");

            var configuration = MachineConfiguration.Read(Path.Combine(
                run.Target, ".assembly-lines", ".machines", current, "config.json"));
            var role = configuration.Role ?? current;
            var prompt = Prompt(current, role, run.Seed, plan, configuration.Lens, findings, line.FieldsFrom(current),
                updatePlan, role == "validator" ? Git.TargetDiff(repository, run.Target) : "");
            MachineResult result;
            try
            {
                result = await Call(configuration.Harness ?? "pi", run.Target, current, prompt);
            }
            catch (MachineException error) { return Fail(error.Message); }

            if (current == "planner")
            {
                if (!File.Exists(plan)) return Fail("The planner did not write a plan.");
                updatePlan = false;
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
                            [], line.FieldsFrom(branch), false, branchRole == "validator" ? work : "");
                        var branchResult = await Call(branchConfiguration.Harness ?? "pi", run.Target, branch, branchPrompt);
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
                        joinResult = await Call(joinConfiguration.Harness ?? "pi", run.Target, fanOut.Join, joinPrompt);
                    }
                    catch (MachineException error) { return Fail(error.Message); }
                    if (joinRole == "validator" && !joinResult.TryStrings("findings", out findings))
                        return Fail($"Could not read the {fanOut.Join}'s result.");

                    var nextAfterJoin = line.Next(fanOut.Join, joinResult);
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

    private static string Prompt(string machine, string role, string seed, string plan, string? lens, string[] findings,
        string[] fields, bool updatePlan, string work)
    {
        var job = role switch
        {
            "planner" when updatePlan => "The current task's validated work has been committed. Mark that task done.",
            "planner" => "If no plan exists, read only the seed and create a short task list. Do no product work. Otherwise inspect your plan.",
            "doer" => $"Do the next unfinished task without marking it done. Record and address these validator findings:\n{string.Join("\n", findings.Select(finding => $"- {finding}"))}",
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

    private static async Task<MachineResult> Call(string harness, string target, string machine, string prompt)
    {
        var isPi = Path.GetFileName(harness) == "pi";
        var start = new ProcessStartInfo(harness)
        {
            WorkingDirectory = target,
            RedirectStandardInput = isPi,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        if (isPi) start.ArgumentList.Add("-p");
        else start.ArgumentList.Add(prompt);

        try
        {
            using var process = Process.Start(start) ?? throw new MachineException($"Could not run the {machine}.");
            if (isPi)
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
    [property: JsonPropertyName("role")] string? Role)
{
    public static MachineConfiguration Read(string path) =>
        JsonSerializer.Deserialize<MachineConfiguration>(File.ReadAllText(path)) ?? new(null, null, null);
}

internal sealed record Options(string? Run, string? Seed, string? Target, string? Line, int Attempts)
{
    public static Options Parse(string[] args)
    {
        string? run = null;
        string? seed = null;
        string? target = null;
        string? line = null;
        var attempts = 3;
        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--run" when index + 1 < args.Length: run = args[++index]; break;
                case "--seed" when index + 1 < args.Length: seed = Path.GetFullPath(args[++index]); break;
                case "--target" when index + 1 < args.Length: target = Path.GetFullPath(args[++index]); break;
                case "--line" when index + 1 < args.Length: line = args[++index]; break;
                case "--attempts" when index + 1 < args.Length: attempts = int.Parse(args[++index]); break;
            }
        }
        return new Options(run, seed, target, line, attempts);
    }
}

internal sealed record RunSettings(
    [property: JsonPropertyName("target")] string Target,
    [property: JsonPropertyName("line")] string Line,
    [property: JsonPropertyName("seed")] string Seed);

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
        var tracked = RunChecked(repository, "diff", "--", pathspec, exclusion);
        var untracked = RunChecked(repository, "ls-files", "--others", "--exclude-standard", "--", pathspec, exclusion);
        return tracked + "\nUntracked files:\n" + untracked;
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
