#!/usr/bin/env python3
"""Real integrity/citation checks in isolated output directories; never replace gates."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[4]

def snapshot(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.iterdir() if p.is_file()}

def wrapper(module, destination):
    return ("import importlib.util; from pathlib import Path; "
            f"s=importlib.util.spec_from_file_location('gate', {str(OUT/module)!r}); "
            "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
            f"m.OUT=Path({str(destination)!r}); "
            "raise SystemExit(m.main())")

def main():
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'tests': []}
    original = snapshot(OUT)
    with tempfile.TemporaryDirectory(dir=OUT, prefix='.retention-test-') as directory:
        temp = Path(directory)
        for name in ('input-files.sha256', 'input-membership.json', 'behaviour.md',
                     'dependencies.md', 'gaps.md', 'source-citations.json'):
            shutil.copyfile(OUT/name, temp/name)
        # The citation verifier executes this adapter, which redirects only outputs.
        (temp/'inventory-inputs.py').write_text(wrapper('inventory-inputs.py', temp))
        inventory = [sys.executable, '-c', wrapper('inventory-inputs.py', temp)]
        citation = [sys.executable, '-c', wrapper('verify-source-citations.py', temp)]
        def check(name, command, expected, unchanged=True):
            before = snapshot(temp)
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            retained = all(snapshot(temp).get(p) == digest for p, digest in before.items())
            no_writes = before == snapshot(temp)
            report['tests'].append({'name': name, 'command': command, 'cwd': str(ROOT),
                'exitCode': result.returncode, 'expectedExitCode': expected,
                'output': result.stdout+result.stderr, 'retainedArtifactsUnchanged': retained,
                'passed': result.returncode == expected and retained and (no_writes or not unchanged)})
        check('default writes nothing', inventory, 0)
        check('reserved Task-1 destination rejected', inventory+['--results', 'input-gate-results.json'], 2)
        check('existing capture rejected before writing', inventory+['--capture'], 1)
        check('first Task-2 retention succeeds', inventory+['--results', 'task-2-input-gate-results.json'], 0, False)
        check('second Task-2 run cannot overwrite any retained artifact', inventory+['--results', 'task-2-input-gate-results.json'], 1)
        # A missing results file is not permission to replace any associated log.
        for name in ('input-hash-check.log', 'baseline-revision-check.log', 'baseline-hash-check.log'):
            orphan = temp/('orphan-'+name)
            orphan.write_text('retained orphan evidence\n')
            check('orphan '+name+' rejected before any write', inventory+['--results', 'orphan-gate-results.json'], 1)
            orphan.unlink()
        check('default citation rerun cannot overwrite Task-2 evidence', citation, 1)
        check('distinct Task-6 citation evidence passes real gates', citation+['--evidence-prefix', 'task-6'], 0, False)
        check('second Task-6 citation run preserves all evidence', citation+['--evidence-prefix', 'task-6'], 1)
    report['originalArtifactsUnchanged'] = original == snapshot(OUT)
    report['passed'] = report['originalArtifactsUnchanged'] and all(t['passed'] for t in report['tests'])
    report['finishedAt'] = datetime.now(timezone.utc).isoformat()
    with (OUT/'evidence-retention-followup-test-results-v2.json').open('x') as evidence:
        evidence.write(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'passed': report['passed'], 'tests': len(report['tests']),
                      'originalArtifactsUnchanged': report['originalArtifactsUnchanged']}))
    return 0 if report['passed'] else 1

if __name__ == '__main__':
    sys.exit(main())
