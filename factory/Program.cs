using System.Diagnostics;
using System.Text.Json;

return await FactoryProgram.RunAsync(args);

internal static class FactoryProgram
{
    public static async Task<int> RunAsync(string[] args)
    {
        var options = Options.Parse(args);
        if (options.Target is null)
            return Fail("A target is required.");
        if (options.Seed is null || !File.Exists(options.Seed))
            return Fail("There is no seed.");

        Directory.CreateDirectory(options.Target);
        var repository = Git.FindContainingRepository(options.Target) ?? Git.Initialize(options.Target);
        var plan = Path.Combine(options.Target, ".factory", "plan.md");

        do
        {
            AgentResult result;
            try
            {
                result = await CallAgent(options.Agent, options.Target, options.Seed, plan);
            }
            catch (Exception error) when (error is System.ComponentModel.Win32Exception or FileNotFoundException)
            {
                return Fail($"Could not run the agent: {error.Message}");
            }

            if (!result.Readable)
                return Fail("Could not read the agent's result.");

            Git.CommitTarget(repository, options.Target,
                result.Task is null ? "Factory: update plan" : $"Factory: {result.Task}");
            Console.WriteLine(result.Json);

            if (result.Complete)
            {
                Console.WriteLine("factory stopped");
                return 0;
            }
        } while (options.All);

        return 0;
    }

    private static async Task<AgentResult> CallAgent(string agent, string target, string seed, string plan)
    {
        var prompt = $"""
            Work in the current directory. The seed is at {seed} and the plan is at {plan}.
            If the plan does not exist, read the seed and write a short task list to the plan. Do no product work yet.
            Otherwise, do the first unfinished task and mark it done in the plan.
            Do exactly one task per call. Do not read a task into the factory; you own and maintain the plan.
            End with one line of JSON containing the boolean field "complete". Include a string field "task" when you did a task.
            Set "complete" to true only when no tasks remain.
            """;

        var start = new ProcessStartInfo(agent)
        {
            WorkingDirectory = target,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        if (Path.GetFileName(agent) == "pi")
            start.ArgumentList.Add("-p");
        start.ArgumentList.Add(prompt);

        using var process = Process.Start(start)
            ?? throw new InvalidOperationException("The agent did not start.");
        var output = await process.StandardOutput.ReadToEndAsync();
        var error = await process.StandardError.ReadToEndAsync();
        await process.WaitForExitAsync();
        if (process.ExitCode != 0)
            throw new System.ComponentModel.Win32Exception(
                string.IsNullOrWhiteSpace(error) ? $"exit code {process.ExitCode}" : error.Trim());

        return AgentResult.From(output);
    }

    private static int Fail(string message)
    {
        Console.Error.WriteLine(message);
        return 1;
    }
}

internal sealed record Options(string? Seed, string? Target, string Agent, bool All)
{
    public static Options Parse(string[] args)
    {
        string? seed = null;
        string? target = null;
        var agent = "pi";
        var all = false;

        for (var index = 0; index < args.Length; index++)
        {
            switch (args[index])
            {
                case "--seed" when index + 1 < args.Length:
                    seed = Path.GetFullPath(args[++index]);
                    break;
                case "--target" when index + 1 < args.Length:
                    target = Path.GetFullPath(args[++index]);
                    break;
                case "--agent" when index + 1 < args.Length:
                    agent = Path.GetFullPath(args[++index]);
                    break;
                case "--all":
                    all = true;
                    break;
            }
        }

        return new Options(seed, target, agent, all);
    }
}

internal sealed record AgentResult(bool Readable, bool Complete, string? Task, string Json)
{
    public static AgentResult From(string output)
    {
        foreach (var line in output.Split('\n').Reverse())
        {
            try
            {
                using var document = JsonDocument.Parse(line);
                if (!document.RootElement.TryGetProperty("complete", out var complete) ||
                    complete.ValueKind is not (JsonValueKind.True or JsonValueKind.False))
                    continue;

                var task = document.RootElement.TryGetProperty("task", out var taskElement)
                    ? taskElement.GetString()
                    : null;
                return new AgentResult(true, complete.GetBoolean(), task, line.Trim());
            }
            catch (JsonException)
            {
            }
        }

        return new AgentResult(false, false, null, "");
    }
}

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

    public static void CommitTarget(string repository, string target, string message)
    {
        var relativeTarget = Path.GetRelativePath(repository, target);
        var pathspec = relativeTarget == "." ? "." : relativeTarget;
        var status = RunChecked(repository, "status", "--porcelain", "--untracked-files=all", "--", pathspec);
        if (string.IsNullOrWhiteSpace(status))
            return;

        RunChecked(repository, "add", "--", pathspec);
        RunChecked(repository, "commit", "--quiet", "--only", "-m", message, "--", pathspec);
    }

    private static string RunChecked(string directory, params string[] arguments)
    {
        var result = Run(directory, arguments);
        if (result.ExitCode != 0)
            throw new InvalidOperationException(result.Error);
        return result.Output;
    }

    private static CommandResult Run(string directory, params string[] arguments)
    {
        var start = new ProcessStartInfo("git")
        {
            WorkingDirectory = directory,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            UseShellExecute = false,
        };
        foreach (var argument in arguments)
            start.ArgumentList.Add(argument);

        using var process = Process.Start(start)!;
        var output = process.StandardOutput.ReadToEnd();
        var error = process.StandardError.ReadToEnd();
        process.WaitForExit();
        return new CommandResult(process.ExitCode, output, error);
    }

    private sealed record CommandResult(int ExitCode, string Output, string Error);
}
