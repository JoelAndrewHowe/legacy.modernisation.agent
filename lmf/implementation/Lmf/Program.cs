using System.Diagnostics;
using System.Security.Cryptography;
using System.Text.Json;

namespace Lmf;

public static class Program
{
    public static async Task<int> Main(string[] args)
    {
        try
        {
            if (args.Length == 0 || args[0] == "help")
            {
                Console.WriteLine("lmf characterise --workspace DIR --source FILE --target FILE --agent CONFIG [--repairs 2]\nlmf approve --workspace DIR --revision SHA256\nlmf resume --workspace DIR\nlmf status --workspace DIR");
                return 0;
            }
            var options = new Dictionary<string, string>(StringComparer.Ordinal);
            for (int i = 1; i < args.Length; i += 2)
            {
                if (!args[i].StartsWith("--", StringComparison.Ordinal) || i + 1 >= args.Length || !options.TryAdd(args[i][2..], args[i + 1]))
                    throw new InvalidOperationException("Options must be unique --name value pairs.");
            }
            string Required(string key) => options.TryGetValue(key, out var value) ? value : throw new InvalidOperationException($"Missing --{key}.");
            var runner = new Runner(Path.GetFullPath(Required("workspace")));
            // An exclusive lock covers the complete invocation, including agent and checks.
            Directory.CreateDirectory(runner.Workspace);
            using var workspaceLock = new FileStream(Path.Combine(runner.Workspace, ".lock"), FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None);
            switch (args[0])
            {
                case "characterise":
                    runner.Initialize(Required("source"), Required("target"), Required("agent"), options.TryGetValue("repairs", out var repairs) ? int.Parse(repairs) : 2);
                    return await runner.Characterise();
                case "approve": runner.Approve(Required("revision")); return 0;
                case "resume": return await runner.Resume();
                case "status": runner.Status(); return 0;
                default: throw new InvalidOperationException($"Unknown command: {args[0]}");
            }
        }
        catch (Exception error)
        {
            Console.Error.WriteLine(error.Message);
            return 1;
        }
    }
}

public sealed record Command(string Executable, string[] Arguments, int TimeoutSeconds = 600);
public sealed record AgentConfig(Command Command);
public sealed record Verification(Command Command, string Results);
public sealed record StageContract(string[] ReviewFiles, string[] BlockingGaps, Verification[] Checks);
public sealed record TestResults(
    [property: System.Text.Json.Serialization.JsonRequired] int Passed,
    [property: System.Text.Json.Serialization.JsonRequired] int Failed,
    [property: System.Text.Json.Serialization.JsonRequired] int Skipped);
public sealed record StageState(string Name, string Status, int Attempts, string? Diagnostic);
public sealed class MigrationState
{
    public string Source { get; set; } = "";
    public string Target { get; set; } = "";
    public AgentConfig Agent { get; set; } = new(new Command("", []));
    public int Repairs { get; set; }
    public string Status { get; set; } = "created";
    public string? Revision { get; set; }
    public string? ApprovedRevision { get; set; }
    public List<StageState> Stages { get; set; } = [];
}

public sealed class Runner(string workspace)
{
    private static readonly JsonSerializerOptions Json = new() { WriteIndented = true, PropertyNameCaseInsensitive = true };
    public string Workspace { get; } = workspace;
    private string StateFile => Path.Combine(Workspace, "state.json");
    private MigrationState state = new();
    private static T Load<T>(string path) => JsonSerializer.Deserialize<T>(File.ReadAllText(path), Json) ?? throw new InvalidOperationException($"Invalid JSON: {path}");
    private static void Write(string path, object value)
    {
        var temporary = path + ".tmp";
        File.WriteAllText(temporary, JsonSerializer.Serialize(value, Json));
        File.Move(temporary, path, true);
    }
    private void Save() => Write(StateFile, state);
    private void Load() => state = Load<MigrationState>(StateFile);

    public void Initialize(string source, string target, string config, int repairs)
    {
        if (File.Exists(StateFile)) throw new InvalidOperationException("Workspace already initialized; use resume or choose a new workspace.");
        if (repairs is < 0 or > 10) throw new InvalidOperationException("Repairs must be between 0 and 10.");
        source = Path.GetFullPath(source);
        target = Path.GetFullPath(target);
        if (!File.Exists(source) || !File.Exists(target)) throw new InvalidOperationException("Source and target description must be existing files.");
        var agent = Load<AgentConfig>(Path.GetFullPath(config));
        ValidateCommand(agent.Command);
        state = new() { Source = source, Target = target, Agent = agent, Repairs = repairs };
        Save();
    }

    public async Task<int> Characterise()
    {
        Load();
        if (!await RunStage("characterise")) return 1;
        state.Revision = Revision();
        state.ApprovedRevision = null;
        state.Status = "awaiting-approval";
        Save();
        Console.WriteLine($"Awaiting human approval: {state.Revision}");
        return 0;
    }

    public void Approve(string revision)
    {
        Load();
        if (state.Status != "awaiting-approval" || !Accepted("characterise")) throw new InvalidOperationException("Characterisation must pass before approval.");
        var current = Revision();
        if (revision != current || state.Revision != current) throw new InvalidOperationException("Reviewed inputs changed; resume to re-characterise before approval.");
        var contract = Contract("characterise");
        if (contract.BlockingGaps.Length != 0) throw new InvalidOperationException("Resolve blocking gaps before approval: " + string.Join("; ", contract.BlockingGaps));
        state.ApprovedRevision = current;
        state.Status = "approved";
        Save();
        Console.WriteLine($"Approved {current}");
    }

    public async Task<int> Resume()
    {
        Load();
        if (Accepted("characterise") && state.Revision != Revision())
        {
            state.ApprovedRevision = null;
            state.Stages.Clear();
            state.Status = "approval-invalidated";
            Save();
        }
        if (!Accepted("characterise")) return await Characterise();
        if (state.ApprovedRevision != Revision())
        {
            state.ApprovedRevision = null;
            state.Status = "awaiting-approval";
            Save();
            Console.WriteLine($"Awaiting human approval: {state.Revision}");
            return 0;
        }
        foreach (var stage in new[] { "convert", "refactor" })
        {
            if (!Accepted(stage) && !await RunStage(stage)) return 1;
        }
        state.Status = "completed";
        Save();
        Console.WriteLine("Migration completed.");
        return 0;
    }

    public void Status()
    {
        Load();
        Console.WriteLine(JsonSerializer.Serialize(new { State = state, CurrentRevision = Accepted("characterise") ? Revision() : null }, Json));
    }

    private bool Accepted(string name) => state.Stages.Any(s => s.Name == name && s.Status == "accepted");
    private string StageDirectory(string name) => Path.Combine(Workspace, name);
    private StageContract Contract(string name)
    {
        var contract = Load<StageContract>(Path.Combine(StageDirectory(name), "stage.json"));
        if (contract.ReviewFiles is null || contract.BlockingGaps is null || contract.Checks is null)
            throw new InvalidOperationException("stage.json requires reviewFiles, blockingGaps and checks arrays.");
        return contract;
    }
    private static string ContainedFile(string directory, string relative)
    {
        var full = Path.GetFullPath(relative, directory);
        if (Path.IsPathRooted(relative) || !full.StartsWith(directory + Path.DirectorySeparatorChar, StringComparison.Ordinal))
            throw new InvalidOperationException($"Artifact must be inside stage directory: {relative}");
        if (File.Exists(full) && new FileInfo(full).LinkTarget is not null) throw new InvalidOperationException("Linked artifacts are not allowed.");
        return full;
    }
    private string Revision()
    {
        var directory = StageDirectory("characterise");
        var contract = Contract("characterise");
        var paths = new[] { state.Source, state.Target, Path.Combine(directory, "stage.json") }
            .Concat(contract.ReviewFiles.Select(f => ContainedFile(directory, f))).Distinct().Order(StringComparer.Ordinal);
        using var hash = IncrementalHash.CreateHash(HashAlgorithmName.SHA256);
        foreach (var path in paths)
        {
            var identity = System.Text.Encoding.UTF8.GetBytes(path);
            var bytes = File.ReadAllBytes(path);
            hash.AppendData(BitConverter.GetBytes(identity.Length));
            hash.AppendData(identity);
            hash.AppendData(BitConverter.GetBytes((long)bytes.Length));
            hash.AppendData(bytes);
        }
        return Convert.ToHexString(hash.GetHashAndReset()).ToLowerInvariant();
    }

    private async Task<bool> RunStage(string name)
    {
        var directory = StageDirectory(name);
        Directory.CreateDirectory(directory);
        for (var repair = 0; repair <= state.Repairs; repair++)
        {
            var previous = state.Stages.LastOrDefault(s => s.Name == name);
            var attemptsDirectory = Path.Combine(directory, "attempts");
            var historicalAttempts = Directory.Exists(attemptsDirectory)
                ? Directory.EnumerateDirectories(attemptsDirectory).Select(path => int.TryParse(Path.GetFileName(path), out var number) ? number : 0).DefaultIfEmpty().Max()
                : 0;
            var attempt = Math.Max(previous?.Attempts ?? 0, historicalAttempts) + 1;
            var evidence = Path.Combine(directory, "attempts", attempt.ToString("D4"));
            Directory.CreateDirectory(evidence);
            state.Stages.RemoveAll(s => s.Name == name);
            state.Stages.Add(new(name, "running", attempt, previous?.Diagnostic));
            state.Status = name;
            Save();
            try
            {
                var request = Path.Combine(evidence, "request.json");
                Write(request, new { Stage = name, Workspace, OutputDirectory = directory, state.Source, state.Target, state.ApprovedRevision, PreviousDiagnostic = previous?.Diagnostic,
                    Contract = "Produce stage.json with reviewFiles, blockingGaps, checks (command and results). Each check writes JSON passed/failed/skipped counts. No empty or skipped checks. Characterise must include behaviour.md, dependencies.md, gaps.md, fixtures.json, migration-plan.md, scenarios.json, reference files in reviewFiles. Do not alter accepted stages or approved inputs." });
                var agentCommand = state.Agent.Command with { Arguments = state.Agent.Command.Arguments.Concat([request]).ToArray() };
                await Execute(agentCommand, directory, Path.Combine(evidence, "agent"));
                var contract = Contract(name);
                if (contract.Checks.Length == 0 || contract.ReviewFiles.Length == 0) throw new InvalidOperationException("Nonempty artifacts and verification checks required.");
                if (name == "characterise")
                {
                    foreach (var required in new[] { "behaviour.md", "dependencies.md", "gaps.md", "fixtures.json", "migration-plan.md", "scenarios.json" })
                        if (!contract.ReviewFiles.Contains(required)) throw new InvalidOperationException($"Missing reviewed artifact: {required}");
                    if (!contract.ReviewFiles.Any(f => f.StartsWith("reference/", StringComparison.Ordinal))) throw new InvalidOperationException("Missing reviewed reference harness.");
                }
                foreach (var artifact in contract.ReviewFiles)
                    if (new FileInfo(ContainedFile(directory, artifact)).Length == 0) throw new InvalidOperationException($"Empty artifact: {artifact}");
                for (int i = 0; i < contract.Checks.Length; i++)
                {
                    var check = contract.Checks[i];
                    var results = ContainedFile(directory, check.Results);
                    File.Delete(results); // A previous or agent-authored success is not verification.
                    await Execute(check.Command, directory, Path.Combine(evidence, $"check-{i}"));
                    File.Copy(results, Path.Combine(evidence, $"results-{i}.json"));
                    var counts = Load<TestResults>(results);
                    if (counts.Passed <= 0 || counts.Failed != 0 || counts.Skipped != 0) throw new InvalidOperationException($"Check {i} was empty, failed or skipped.");
                }
                if (name != "characterise" && state.ApprovedRevision != Revision()) throw new InvalidOperationException("Approved inputs were modified; approval is invalid. Restore reviewed files or re-characterise.");
                state.Stages[^1] = new(name, "accepted", attempt, null);
                Save();
                return true;
            }
            catch (Exception error)
            {
                File.WriteAllText(Path.Combine(evidence, "failure.txt"), error.ToString());
                state.Stages[^1] = new(name, "failed", attempt, error.Message);
                state.Status = "failed";
                Save();
                Console.Error.WriteLine($"{name} attempt {attempt}: {error.Message} (evidence: {evidence})");
            }
        }
        return false;
    }

    private static void ValidateCommand(Command command)
    {
        if (string.IsNullOrWhiteSpace(command.Executable) || command.Arguments is null || command.TimeoutSeconds is < 1 or > 86400)
            throw new InvalidOperationException("Command needs executable, arguments and timeoutSeconds in 1..86400.");
    }
    private static async Task Execute(Command command, string directory, string log)
    {
        ValidateCommand(command);
        Write(log + ".command.json", command);
        var start = new ProcessStartInfo(command.Executable) { WorkingDirectory = directory, RedirectStandardOutput = true, RedirectStandardError = true, UseShellExecute = false };
        foreach (var argument in command.Arguments) start.ArgumentList.Add(argument);
        using var process = Process.Start(start) ?? throw new InvalidOperationException("Could not start command.");
        await using var stdout = File.Create(log + ".stdout.txt");
        await using var stderr = File.Create(log + ".stderr.txt");
        var output = process.StandardOutput.BaseStream.CopyToAsync(stdout);
        var errors = process.StandardError.BaseStream.CopyToAsync(stderr);
        using var timeout = new CancellationTokenSource(TimeSpan.FromSeconds(command.TimeoutSeconds));
        try { await process.WaitForExitAsync(timeout.Token); }
        catch (OperationCanceledException)
        {
            process.Kill(entireProcessTree: true);
            await process.WaitForExitAsync();
            await Task.WhenAll(output, errors);
            throw new InvalidOperationException($"Command timed out: {command.Executable}");
        }
        await Task.WhenAll(output, errors);
        if (process.ExitCode != 0) throw new InvalidOperationException($"Command exited {process.ExitCode}: {command.Executable}");
    }
}
