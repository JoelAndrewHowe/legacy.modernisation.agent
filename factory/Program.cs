using System.Diagnostics;
using System.Text.Json;

return await FactoryProgram.RunAsync(args);

internal static class FactoryProgram
{
    public static async Task<int> RunAsync(string[] args)
    {
        var options = Options.Parse(args);
        if (options.Target is null) return Fail("A target is required.");
        if (options.Seed is null || !File.Exists(options.Seed)) return Fail("There is no seed.");

        Directory.CreateDirectory(options.Target);
        var repository = Git.FindContainingRepository(options.Target) ?? Git.Initialize(options.Target);
        var plan = Path.Combine(options.Target, ".factory", "plan.md");

        do
        {
            MachineResult planner;
            try
            {
                planner = await Call(options, "planner", PlannerPrompt(options.Seed, plan));
            }
            catch (MachineException error) { return Fail(error.Message); }
            if (!planner.TryBoolean("complete", out var complete))
                return Fail("Could not read the planner's result.");

            if (!File.Exists(plan)) return Fail("The planner did not write a plan.");
            if (Git.HasTargetChanges(repository, options.Target))
            {
                Git.CommitTarget(repository, options.Target, "Factory: update plan");
                Console.WriteLine(planner.Json);
                if (!options.All) return 0;
                continue;
            }

            if (complete)
            {
                Console.WriteLine(planner.Json);
                Console.WriteLine("factory stopped");
                return 0;
            }

            var findings = Array.Empty<string>();
            var satisfied = false;
            for (var attempt = 1; attempt <= options.Attempts; attempt++)
            {
                try
                {
                    await Call(options, "doer", DoerPrompt(options.Seed, plan, findings));
                }
                catch (MachineException error) { return Fail(error.Message); }

                var work = Git.TargetDiff(repository, options.Target);
                MachineResult validator;
                try
                {
                    validator = await Call(options, "validator", ValidatorPrompt(plan, options.Lens, work));
                }
                catch (MachineException error) { return Fail(error.Message); }

                if (!validator.TryBoolean("satisfied", out satisfied) ||
                    !validator.TryStrings("findings", out findings))
                    return Fail("Could not read the validator's result.");
                if (satisfied) break;
            }

            if (!satisfied)
                return Fail($"The pass hit its limit of {options.Attempts} attempts.");

            Git.CommitTarget(repository, options.Target, "Factory: completed task");

            MachineResult updatedPlan;
            try
            {
                updatedPlan = await Call(options, "planner", PlannerUpdatePrompt(options.Seed, plan));
            }
            catch (MachineException error) { return Fail(error.Message); }
            if (!updatedPlan.TryBoolean("complete", out complete))
                return Fail("Could not read the planner's result.");
            Git.CommitTarget(repository, options.Target, "Factory: update plan");
            Console.WriteLine(updatedPlan.Json);

            if (complete)
            {
                Console.WriteLine("factory stopped");
                return 0;
            }
        } while (options.All);

        return 0;
    }

    private static string PlannerPrompt(string seed, string plan) => $"""
        You are the planner. The seed is at {seed} and your plan is at {plan}.
        If no plan exists, read only the seed and create a short task list. Do no product work.
        Otherwise inspect your plan without changing completed work.
        End with one line of JSON containing the boolean field "complete".
        """;

    private static string PlannerUpdatePrompt(string seed, string plan) => $"""
        You are the planner. The seed is at {seed} and your plan is at {plan}.
        The current task's validated work has been committed. Mark that task done.
        End with one line of JSON containing the boolean field "complete".
        """;

    private static string DoerPrompt(string seed, string plan, string[] findings) => $"""
        You are the doer. The seed is at {seed} and the plan is at {plan}.
        Do the next unfinished task without marking the task done; the planner owns completion.
        Record every validator finding below as a subtask of the task in progress and address it:
        {string.Join("\n", findings.Select(finding => $"- {finding}"))}
        End with one line of JSON describing what you did.
        """;

    private static string ValidatorPrompt(string plan, string lens, string work) => $"""
        You are the validator. Inspect only the doer's current uncommitted work shown below.
        Do not change the plan at {plan} or any work. Your validation lens is {lens}.
        Current work:
        {work}
        End with one line of JSON containing boolean "satisfied" and array "findings".
        """;

    private static async Task<MachineResult> Call(Options options, string role, string prompt)
    {
        var start = new ProcessStartInfo(options.Agent)
        {
            WorkingDirectory = options.Target!,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        if (Path.GetFileName(options.Agent) == "pi") start.ArgumentList.Add("-p");
        start.ArgumentList.Add(prompt);

        try
        {
            using var process = Process.Start(start) ?? throw new MachineException($"Could not run the {role}.");
            var output = await process.StandardOutput.ReadToEndAsync();
            var error = await process.StandardError.ReadToEndAsync();
            await process.WaitForExitAsync();
            if (process.ExitCode != 0)
                throw new MachineException($"Could not run the {role}: {error.Trim()}");
            return MachineResult.From(output);
        }
        catch (System.ComponentModel.Win32Exception error)
        {
            throw new MachineException($"Could not run the {role}: {error.Message}");
        }
    }

    private static int Fail(string message) { Console.Error.WriteLine(message); return 1; }
}

internal sealed record Options(string? Seed, string? Target, string Agent, bool All, int Attempts, string Lens)
{
    public static Options Parse(string[] args)
    {
        string? seed = null;
        string? target = null;
        var agent = "pi";
        var all = false;
        var attempts = 3;
        var lens = "testability";
        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--seed" when index + 1 < args.Length: seed = Path.GetFullPath(args[++index]); break;
                case "--target" when index + 1 < args.Length: target = Path.GetFullPath(args[++index]); break;
                case "--agent" when index + 1 < args.Length: agent = Path.GetFullPath(args[++index]); break;
                case "--attempts" when index + 1 < args.Length: attempts = int.Parse(args[++index]); break;
                case "--lens" when index + 1 < args.Length: lens = args[++index]; break;
                case "--all": all = true; break;
            }
        }
        return new Options(seed, target, agent, all, attempts, lens);
    }
}

internal sealed record MachineResult(JsonElement? Root, string Json)
{
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
