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
        if (options.Target is null) return Fail("A target is required.");
        if (options.Seed is null || !File.Exists(options.Seed)) return Fail("There is no seed.");

        var factory = Path.GetFullPath(Path.Combine(AppContext.BaseDirectory, "../../.."));
        AssemblyLine line;
        try
        {
            line = AssemblyLine.Read(Path.Combine(factory, "assembly-line.dot"), Path.Combine(factory, "machines"));
        }
        catch (MachineException error) { return Fail(error.Message); }

        Directory.CreateDirectory(options.Target);
        var repository = Git.FindContainingRepository(options.Target) ?? Git.Initialize(options.Target);
        var plan = Path.Combine(options.Target, ".factory", "plan.md");
        var current = line.First;
        var findings = Array.Empty<string>();
        var attempts = 0;
        var updatePlan = false;
        var workWaiting = false;

        while (current != "finish")
        {
            if (current == "doer" && attempts == options.Attempts)
                return Fail($"A task hit its limit of {options.Attempts} attempts.");

            var configuration = MachineConfiguration.Read(Path.Combine(factory, "machines", $"{current}.json"));
            var prompt = Prompt(current, options.Seed, plan, configuration.Lens, findings, line.FieldsFrom(current),
                updatePlan, current == "validator" ? Git.TargetDiff(repository, options.Target) : "");
            MachineResult result;
            try
            {
                result = await Call(configuration.Harness ?? "pi", options.Target, current, prompt);
            }
            catch (MachineException error) { return Fail(error.Message); }

            if (current == "planner")
            {
                if (!File.Exists(plan)) return Fail("The planner did not write a plan.");
                Git.CommitTarget(repository, options.Target, "Factory: update plan");
                updatePlan = false;
            }
            else if (current == "doer")
            {
                attempts++;
                workWaiting = true;
            }
            else if (current == "validator" && !result.TryStrings("findings", out findings))
            {
                return Fail("Could not read the validator's result.");
            }

            try
            {
                var next = line.Next(current, result);
                if (next == "planner" && workWaiting)
                {
                    Git.CommitTarget(repository, options.Target, "Factory: completed task");
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

    private static string Prompt(string machine, string seed, string plan, string? lens, string[] findings,
        string[] fields, bool updatePlan, string work)
    {
        var job = machine switch
        {
            "planner" when updatePlan => "The current task's validated work has been committed. Mark that task done.",
            "planner" => "If no plan exists, read only the seed and create a short task list. Do no product work. Otherwise inspect your plan.",
            "doer" => $"Do the next unfinished task without marking it done. Record and address these validator findings:\n{string.Join("\n", findings.Select(finding => $"- {finding}"))}",
            "validator" => $"Inspect only the current uncommitted work below. Change neither the plan nor the work. Your validation lens is {lens}.\n{work}",
            _ => "Do your configured job."
        };
        var requested = fields.Concat(machine == "validator" ? ["findings"] : []).Distinct().ToArray();
        var result = requested.Length == 0
            ? "End with one line of JSON describing what you did."
            : requested.Length == 1
                ? $"End with one line of JSON containing the field \"{requested[0]}\"."
                : $"End with one line of JSON containing the fields {string.Join(" and ", requested.Select(field => $"\"{field}\""))}.";
        return $"You are the {machine}. The seed is at {seed} and the plan is at {plan}.\n{job}\n{result}";
    }

    private static async Task<MachineResult> Call(string harness, string target, string machine, string prompt)
    {
        var start = new ProcessStartInfo(harness)
        {
            WorkingDirectory = target,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        if (Path.GetFileName(harness) == "pi") start.ArgumentList.Add("-p");
        start.ArgumentList.Add(prompt);

        try
        {
            using var process = Process.Start(start) ?? throw new MachineException($"Could not run the {machine}.");
            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
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

        var machines = Directory.GetFiles(machinesDirectory, "*.json").Select(Path.GetFileNameWithoutExtension).ToHashSet();
        foreach (var node in edges.SelectMany(edge => new[] { edge.From, edge.To }).Distinct())
            if (node is not "start" and not "finish" && !machines.Contains(node))
                throw new MachineException($"The factory has no machine called \"{node}\".");

        foreach (var node in edges.Select(edge => edge.From).Where(node => node != "start").Distinct().Reverse())
            if (!CanReachFinish(node, edges, []))
                throw new MachineException($"Finish cannot be reached from {node}.");

        return new AssemblyLine(edges);
    }

    public string[] FieldsFrom(string machine) => edges.Where(edge => edge.From == machine && edge.Label is not null)
        .Select(edge => edge.Label!.StartsWith("not ") ? edge.Label[4..] : edge.Label)
        .Distinct().ToArray();

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
    [property: JsonPropertyName("lens")] string? Lens)
{
    public static MachineConfiguration Read(string path) =>
        JsonSerializer.Deserialize<MachineConfiguration>(File.ReadAllText(path)) ?? new(null, null);
}

internal sealed record Options(string? Seed, string? Target, int Attempts)
{
    public static Options Parse(string[] args)
    {
        string? seed = null;
        string? target = null;
        var attempts = 3;
        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--seed" when index + 1 < args.Length: seed = Path.GetFullPath(args[++index]); break;
                case "--target" when index + 1 < args.Length: target = Path.GetFullPath(args[++index]); break;
                case "--attempts" when index + 1 < args.Length: attempts = int.Parse(args[++index]); break;
            }
        }
        return new Options(seed, target, attempts);
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
        !string.IsNullOrWhiteSpace(RunChecked(repository, "status", "--porcelain", "--untracked-files=all", "--", Pathspec(repository, target)));

    public static string TargetDiff(string repository, string target)
    {
        var pathspec = Pathspec(repository, target);
        var tracked = RunChecked(repository, "diff", "--", pathspec);
        var untracked = RunChecked(repository, "ls-files", "--others", "--exclude-standard", "--", pathspec);
        return tracked + "\nUntracked files:\n" + untracked;
    }

    public static void CommitTarget(string repository, string target, string message)
    {
        var pathspec = Pathspec(repository, target);
        if (!HasTargetChanges(repository, target)) return;
        RunChecked(repository, "add", "--", pathspec);
        RunChecked(repository, "commit", "--quiet", "--only", "-m", message, "--", pathspec);
    }

    private static string Pathspec(string repository, string target) =>
        Path.GetRelativePath(repository, target) is "." ? "." : Path.GetRelativePath(repository, target);

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
