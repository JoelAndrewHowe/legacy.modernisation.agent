#!/usr/bin/env python3
"""Runtime/dependency port of the approved extracted HCWP logic, not a redesign."""
import hashlib
import json
from pathlib import Path
import shutil
import sys


def generate(request):
    output = Path(request['OutputDirectory'])
    reference = Path(request['Workspace']) / 'characterise'
    revision = request.get('ApprovedRevision')
    if not revision:
        raise ValueError('Convert requires revision-bound approval')
    contract = json.loads((reference / 'stage.json').read_text())
    project = output / 'converted'
    project.mkdir(parents=True, exist_ok=True)
    # Compile a separate assembly; do not invoke/reference the baseline assembly.
    sources = sorted(p for p in (reference / 'reference').iterdir() if p.suffix == '.cs')
    if not sources:
        raise ValueError('Approved reference has no C# sources')
    manifest = []
    for source in sources:
        relative = str(source.relative_to(reference))
        if relative not in contract['reviewFiles']:
            raise ValueError('Unreviewed reference source: ' + relative)
        shutil.copyfile(source, project / source.name)
        manifest.append({'source': relative, 'target': 'converted/' + source.name,
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    (project / 'Converted.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <OutputType>Exe</OutputType>\n    <TargetFramework>net10.0</TargetFramework>\n    <ImplicitUsings>enable</ImplicitUsings>\n    <Nullable>disable</Nullable>\n  </PropertyGroup>\n</Project>\n')
    for name in ('scenarios.json', 'fixtures.json'):
        shutil.copyfile(reference / name, output / name)
    (output / 'port-manifest.json').write_text(json.dumps({'approvedRevision': revision, 'files': manifest}, indent=2) + '\n')
    (output / 'PORT.md').write_text('''# Convert: modern runtime/dependency port

This separately compiled .NET 10 executable retains the approved extracted C#
structure and business-rule bodies byte-for-byte. Characterise already made the
runtime/dependency substitutions needed for Linux execution; no further rule
substitution is necessary. port-manifest.json maps each source and its hash.

The copied Compatibility.cs and recording fixtures replace the same unavailable
Windows, service, lookup and repository dependencies as the approved reference.
See the approved characterise/reference/ADAPTATIONS.md for every substitution.
Program.cs remains a scenario adapter, not a UI. There is no reference assembly
link or reference invocation from the converted executable.

The verifier independently executes both assemblies with the exact approved
scenarios and fixtures and compares full ordered observations without
normalisation. Both must also match the approved expected outcomes. Missing,
extra, reordered, failed or skipped scenarios cannot pass. Build failures fail
verification. Reports retain commands, hashes and scenario-level differences.

Evidence is parity with extracted legacy logic, not the original Windows/Oracle
application. Recording doubles do not prove Windows lifecycle, live services,
transactions or persistence. Blazor and EF Core persistence belong to Refactor;
no browser or persistence read-back claim is made at Convert.
''')
    shutil.copyfile(Path(__file__).with_name('verify_convert.py'), output / 'verify.py')
    reviewed = ['PORT.md', 'port-manifest.json', 'scenarios.json', 'fixtures.json', 'verify.py', 'converted/Converted.csproj']
    reviewed += ['converted/' + p.name for p in sources]
    (output / 'stage.json').write_text(json.dumps({'reviewFiles': reviewed, 'blockingGaps': [],
        'checks': [{'command': {'executable': sys.executable, 'arguments': [str(output / 'verify.py')], 'timeoutSeconds': 600}, 'results': 'results.json'}]}, indent=2) + '\n')


if __name__ == '__main__':
    generate(json.loads(Path(sys.argv[1]).read_text()))
