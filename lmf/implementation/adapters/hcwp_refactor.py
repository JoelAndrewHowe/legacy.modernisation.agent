#!/usr/bin/env python3
"""Generate the scoped browser/persistence shell around the accepted Convert port."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

TEMPLATES = Path(__file__).with_name('refactor')


def generate(request):
    root = Path(request['OutputDirectory'])
    workspace = Path(request['Workspace'])
    revision = request.get('ApprovedRevision')
    if not revision:
        raise ValueError('Refactor requires revision-bound approval')
    port = workspace / 'convert/converted'
    if not (port / 'Converted.csproj').exists():
        raise ValueError('Accepted Convert port required')
    project = root / 'app'
    project.mkdir(parents=True, exist_ok=True)
    manifest = []
    for source in sorted(port.glob('*.cs')):
        content = source.read_text()
        destination = project / 'Legacy' / source.name
        destination.parent.mkdir(exist_ok=True)
        if source.name == 'Program.cs':
            # The approved observation adapter now runs within the final assembly.
            content = 'public static class SharedScenarios { public static void Run(string[] args) {\n' + content.replace('using System.Text.Json;\n', '').replace('using System.Text.Json.Nodes;\n', '').replace('using Orvex.Business.Validation;\n', '').replace('using Orvex.Messages.Faults;\n', '').replace('using Orvex.TransferObjects;\n', '') + '\n} }\n'
        destination.write_text(content)
        manifest.append({'source': 'convert/converted/' + source.name,
                         'target': str(destination.relative_to(root)),
                         'sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                         'adaptation': 'entry-point wrapper only' if source.name == 'Program.cs' else 'none'})
    for source in TEMPLATES.rglob('*'):
        if source.is_file():
            destination = project / source.relative_to(TEMPLATES)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    # UI option labels/codes are source-defined, not invented clinical assessments.
    from hcwp_characterise import method
    lookup_path = 'reference/original/Orvex.Contracts/HLX.BusinessTier/Common/Util/LookupsUtility.cs'
    contract = json.loads((workspace / 'characterise/stage.json').read_text())
    if lookup_path not in contract['reviewFiles']:
        raise ValueError('UI options require the approved original LookupsUtility.cs')
    lookups = (workspace / 'characterise' / lookup_path).read_text()
    bodies = '\n'.join(method(lookups, name, '') for name in ('PhysicalAssessment6To8Weeks', 'EvidenceOfXgm', 'DomesticViolenceConcern'))
    (project / 'RecordingOptions.cs').write_text('public static class RecordingOptions {\n' + bodies + '\n}\n')
    for name in ('scenarios.json', 'fixtures.json'):
        shutil.copyfile(workspace / 'characterise' / name, root / name)
    shutil.copyfile(Path(__file__).with_name('verify_refactor.py'), root / 'verify.py')
    shutil.copyfile(Path(__file__).with_name('refactor_browser.py'), root / 'browser.py')
    (root / 'refactor-manifest.json').write_text(json.dumps({'approvedRevision': revision, 'files': manifest}, indent=2) + '\n')
    (root / 'REFACTOR.md').write_text('''# Scoped KD03 Refactor

Launch: `dotnet run --project app/Hcwp.csproj -- --urls http://127.0.0.1:5080`.
Requires .NET 10, NuGet access for Microsoft.EntityFrameworkCore.InMemory 10.0.0,
and Python Playwright with Chromium for the browser gate (`pip install playwright`
then `python -m playwright install --with-deps chromium`). Run `python verify.py` to execute
build, formatting, approved observation parity, fresh-context persistence checks
and the browser add/read-back/reload/rejection checks. Missing browser prerequisites
fail verification, never produce a mocked success. Evidence is retained in logs,
parity-report.json, persistence-report.json and browser-report.json/screenshot.

Server-interactive Blazor wraps the accepted Convert sources. Shared scenarios run
inside this final assembly; the independent reference remains in Characterise.
Source bodies are unchanged; Program.cs has only an entry-point wrapper. The same
validator and delegate supply field/save validation, warning/calculation and decline
logic to the recording service. EF stores detached serialized DTOs, then deserializes
read-back using a new context. Repeat decisions use the extracted method over
selected-patient KD03 rows loaded through EF and are written back through EF.

Synthetic patient 1001 (boy, born 2025-01-01) is selected. Patient 2002 has a seeded
KD03 result with repeat=true for isolation checks. Clock is frozen at 2025-03-01.
Schedule 6–8 weeks, height 40–60, weight 3–6 and BMI 10–25 are invented reviewed demonstration
fixtures, not clinical data. Location SYNTH and used examiner SYNTH are fixture
lookup codes. Physical, XGM and domestic-violence dropdowns retain the approved original
LookupsUtility dictionary bodies and their labels/codes; missing resource text
is not invented. Blank is null. Source field/save validators remain authoritative;
no additional mandatory assessment or exact-age constraint is introduced.
The UI exposes only KD03/common fields, not excluded developmental/DSK/RSK fields.
Warnings are symbolic resource names. Duplicate-date errors stop save; duplicate-code
warnings require explicit confirmation. The selected synthetic patient's preschool
consent is true; recorded Consent is not an invented mandatory save predicate.
New drafts retain source defaults for reschedule, decline flags and unscheduled
origin. Preselected KD03 and 2025-02-20 date are explicit demonstration UI presets. Field head circumference validation remains stricter than direct
save validation; both paths remain visible in the approved shared suite.

No original Windows/Oracle parity, real lookup/service/transaction behaviour,
appointments, recalls, editing/deletion, production authentication, PostgreSQL or
real-agent migration is claimed. Storage survives reload during the running process
but is temporary and resets on restart. This is a local synthetic demonstration.
''')
    reviewed = ['REFACTOR.md', 'refactor-manifest.json', 'scenarios.json', 'fixtures.json', 'verify.py', 'browser.py']
    reviewed += [str(p.relative_to(root)) for p in project.rglob('*') if p.is_file() and 'obj' not in p.parts and 'bin' not in p.parts]
    (root / 'stage.json').write_text(json.dumps({'reviewFiles': reviewed, 'blockingGaps': [], 'checks': [
        {'command': {'executable': sys.executable, 'arguments': [str(root / 'verify.py')], 'timeoutSeconds': 600}, 'results': 'results.json'}]}, indent=2) + '\n')


if __name__ == '__main__':
    generate(json.loads(Path(sys.argv[1]).read_text()))
