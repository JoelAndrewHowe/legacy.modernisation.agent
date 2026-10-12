#!/usr/bin/env python3
"""Adapt LMF's appended request path to a local, non-interactive Pi agent."""
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: pi_agent.py /absolute/path/to/request.json')
    request_path = Path(sys.argv[1]).resolve(strict=True)
    request = json.loads(request_path.read_text())
    stage = request['Stage']
    if stage not in ('characterise', 'convert', 'refactor'):
        raise SystemExit('Unsupported LMF stage: ' + stage)
    adapter = Path(__file__).with_name('hcwp_characterise.py').resolve()
    prompt = f'''You are the coding agent for one LMF stage, not its planner or operator.
Read the attached request JSON. Work only inside its OutputDirectory.
Inspect the supplied source and target and the local source-bound HCWP adapter
at {adapter}. This run explicitly permits reuse of that adapter; report its use
honestly, not as independently authored migration logic. You may run it with
Python and the request path to generate this stage's artifacts. Inspect the
resulting stage.json and relevant generated documents for the requested scope.
For downstream stages preserve every approved Characterise artifact and all
shared scenario expectations. Never approve a revision, edit state.json, or
invoke LMF approve/resume. Do not alter repository source or other workspaces.
Produce the required stage.json and artifacts; do not fabricate verification
counts. The LMF runner, not you, will execute the configured verification checks.
If generation cannot succeed, explain the blocker and do not create success
artifacts. Finish with a concise account of actions and limitations.
'''
    command = [os.environ.get('LMF_PI_EXECUTABLE', 'pi'), '--print',
               '--no-session', '--no-extensions', '--no-skills',
               '--no-prompt-templates', '--no-context-files', '--no-mcp',
               '--offline', '--tools', 'read,bash,edit,write']
    provider = os.environ.get('LMF_PI_PROVIDER')
    model = os.environ.get('LMF_PI_MODEL')
    if provider and not model:
        raise SystemExit('LMF_PI_PROVIDER requires LMF_PI_MODEL')
    if provider:
        command += ['--provider', provider]
    if model:
        command += ['--model', model]
    command += ['@' + str(request_path), prompt]
    # Inherit stdout/stderr so LMF retains the agent transcript in its attempt.
    # LMF owns the process timeout and verifies generated artifacts independently.
    return subprocess.call(command, cwd=request['OutputDirectory'])


if __name__ == '__main__':
    sys.exit(main())
