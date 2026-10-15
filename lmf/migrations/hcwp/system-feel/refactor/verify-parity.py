#!/usr/bin/env python3
"""Reexecute all 53 approved reference/Convert cases into Refactor-owned evidence."""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from xml.sax.saxutils import escape

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
TARGET = HERE.parents[1]
PACKET = HERE.parent / 'characterise'
CONVERT = HERE.parent / 'convert'

def load(name, path):
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', required=True)
    args = parser.parse_args()
    dest = Path(args.evidence_dir).resolve()
    if not dest.is_relative_to(HERE / 'evidence'):
        parser.error('Refactor evidence directory required')
    dest.mkdir(parents=True, exist_ok=False)
    reference = load('slice_reference', PACKET / 'reference/run.py')
    port = load('slice_convert', CONVERT / 'verify')
    commands, observations, errors = [], [], []
    def run(argv, name, payload=None):
        result = subprocess.run(argv, cwd=TARGET, input=payload, capture_output=True, text=True)
        commands.append(dict(argv=argv, cwd=str(TARGET), exitCode=result.returncode))
        (dest / name).write_text(result.stdout + result.stderr)
        if result.returncode:
            raise ValueError('Failed: ' + name)
        return result.stdout
    try:
        run([sys.executable, str(HERE / 'check-prerequisites.py')], 'prerequisites.json')
        cases = reference.validate_contract(json.loads((PACKET / 'fixtures.json').read_text()), json.loads((PACKET / 'scenarios.json').read_text()))
        fixtures = json.loads((PACKET / 'fixtures.json').read_text())
        executable = [s for s in cases if s['operation'] != 'ordering-contract']
        payload = ''.join(json.dumps(reference.resolve(s, fixtures)) + '\n' for s in executable)
        (dest / 'requests.jsonl').write_text(payload)
        # The immutable Convert CLI protects the pre-Refactor target as well as
        # approval. Reuse its unchanged adapter under the Refactor-aware gate,
        # not that now-stale CLI. Compile original files by link, never edit them.
        harness = dest / 'convert-harness'
        harness.mkdir()
        sources = ''.join(f'<Compile Include="{escape(str(p))}" />' for p in sorted((CONVERT / 'src').glob('*.cs')))
        project = harness / 'Parity.csproj'
        project.write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><OutputType>Exe</OutputType><TargetFramework>net10.0</TargetFramework><ImplicitUsings>enable</ImplicitUsings><StartupObject>SliceRunner</StartupObject></PropertyGroup><ItemGroup>' + sources + '</ItemGroup></Project>')
        (harness / 'Runner.cs').write_text('''using System.Globalization;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
public static class SliceRunner {
 public static void Main() {
  CultureInfo.CurrentCulture = CultureInfo.GetCultureInfo("en-GB");
  CultureInfo.CurrentUICulture = CultureInfo.CurrentCulture;
  var observe = typeof(Hcwp.SystemFeel.Converted.Program).GetMethod("Observe", BindingFlags.Static | BindingFlags.NonPublic)!;
  string line;
  while ((line = Console.ReadLine()) != null) {
   try { Console.WriteLine(JsonSerializer.Serialize(observe.Invoke(null, new object[] { JsonNode.Parse(line)! }))); }
   catch (Exception e) { Console.WriteLine(JsonSerializer.Serialize(new { error = e.ToString() })); }
  }
 }
}
''')
        outputs = []
        for label, project, dll in [('reference', PACKET / 'reference/Reference.csproj', PACKET / 'reference/bin/Release/net10.0/Reference.dll'), ('convert', project, harness / 'bin/Release/net10.0/Parity.dll')]:
            run(['dotnet', 'build', str(project), '-c', 'Release'], label + '-build.log')
            lines = run(['dotnet', str(dll)], label + '.jsonl', payload).splitlines()
            if len(lines) != len(executable):
                raise ValueError('Incomplete runtime observations: ' + label)
            outputs.append(dict(zip([s['id'] for s in executable], map(json.loads, lines))))
        for case in cases:
            legacy = reference.ordering_observation() if case['operation'] == 'ordering-contract' else outputs[0][case['id']]
            converted = port.ordering_observation() if case['operation'] == 'ordering-contract' else outputs[1][case['id']]
            failures = reference.compare_observation(case['expected'], legacy) + reference.compare_observation(case['expected'], converted) + port.compare_complete(legacy, converted)
            if 'error' in legacy or 'error' in converted:
                failures.append('Runtime error')
            observations.append(dict(id=case['id'], expected=case['expected'], reference=legacy, converted=converted, failures=failures, passed=not failures))
        if len(observations) != 53:
            raise ValueError('Expected all 53 approved cases')
    except Exception as error:
        errors.append(str(error))
    report = dict(total=len(observations), passed=sum(o['passed'] for o in observations), failed=sum(not o['passed'] for o in observations) + len(errors), skipped=0, errors=errors, commands=commands, observations=observations)
    (dest / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'observations'}))
    return 0 if report['passed'] == 53 and not report['failed'] else 1

if __name__ == '__main__':
    sys.exit(main())
