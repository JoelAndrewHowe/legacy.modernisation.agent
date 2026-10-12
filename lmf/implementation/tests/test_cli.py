"""Dependency-free orchestration smoke tests; no HCWP parity claim."""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DLL = ROOT / "Lmf/bin/Debug/net10.0/Lmf.dll"
AGENT = r'''
import json, pathlib, sys
request = json.loads(pathlib.Path(sys.argv[1]).read_text())
out = pathlib.Path(request["OutputDirectory"])
workspace = pathlib.Path(request["Workspace"])
stage = request["Stage"]
mode = (workspace / "mode").read_text() if (workspace / "mode").exists() else "ok"
with (workspace / "calls").open("a") as f: f.write(stage + "\n")
if mode == "agent-fails" or (mode == "convert-fails" and stage == "convert"):
    print("deliberate agent failure", file=sys.stderr)
    sys.exit(7)
files = ["behaviour.md", "dependencies.md", "gaps.md", "fixtures.json", "migration-plan.md", "scenarios.json", "reference/check.py"] if stage == "characterise" else ["implementation.txt"]
for name in files:
    path = out / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists(): path.write_text("synthetic orchestration fixture\n")
counts = {"passed": 1, "failed": 0, "skipped": 0}
if mode == "empty": counts["passed"] = 0
if mode == "skipped": counts["skipped"] = 1
if mode == "failed-check": counts["failed"] = 1
checker = out / "check.py"
result_text = json.dumps(counts)
if mode == "custom-result": result_text = (workspace / "custom-result.json").read_text()
checker.write_text("import pathlib\npathlib.Path('results.json').write_text(" + repr(result_text) + ")\n")
contract = {"reviewFiles": files, "blockingGaps": ["missing schedule"] if mode == "gap" else [], "checks": [{"command": {"executable": sys.executable, "arguments": [str(checker)], "timeoutSeconds": 10}, "results": "results.json"}]}
if stage == "refactor" and mode.startswith("gate-"):
    contract["checks"] = []
    for gate in ("build", "style", "parity"):
        script = out / (gate + ".py")
        result = gate + "-results.json"
        # Agent-authored counts must never substitute for executing a gate.
        (out / result).write_text(json.dumps(counts))
        body = "import json, pathlib, sys\nprint(" + repr(gate + " executed") + ")\n"
        if mode == "gate-" + gate and gate != "parity":
            body += "print('deliberate gate failure', file=sys.stderr)\nsys.exit(9)\n"
        elif mode == "gate-stale" and gate == "parity":
            body += "pass\n"
        else:
            gate_counts = {"passed": 1, "failed": int(mode == "gate-parity" and gate == "parity"), "skipped": 0}
            body += "pathlib.Path(" + repr(result) + ").write_text(" + repr(json.dumps(gate_counts)) + ")\n"
            if gate == "parity":
                body += "pathlib.Path('parity-report.json').write_text(" + repr(json.dumps({"id": "synthetic-mismatch", "matches": not gate_counts["failed"]})) + ")\n"
        script.write_text(body)
        contract["checks"].append({"command": {"executable": sys.executable, "arguments": [str(script)], "timeoutSeconds": 10}, "results": result})
if mode == "missing-check": contract["checks"] = []
if mode == "stale":
    (out / "results.json").write_text(json.dumps(counts))
    checker.write_text("pass\n")
(out / "stage.json").write_text(json.dumps(contract))
'''


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run(["dotnet", "build", str(ROOT / "Lmf/Lmf.csproj"), "--nologo"], check=True, capture_output=True)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.workspace = self.root / "migration"
        self.workspace.mkdir()
        self.source = self.root / "legacy.txt"
        self.source.write_text("synthetic source")
        self.target = self.root / "target.txt"
        self.target.write_text("synthetic target")
        agent = self.root / "agent.py"
        agent.write_text(AGENT)
        self.config = self.root / "agent.json"
        self.config.write_text(json.dumps({"command": {"executable": sys.executable, "arguments": [str(agent)], "timeoutSeconds": 10}}))

    def cli(self, command, *options, code=0):
        result = subprocess.run(["dotnet", str(DLL), command, "--workspace", str(self.workspace), *map(str, options)], capture_output=True, text=True)
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        return result

    def characterise(self, code=0, repairs=0):
        return self.cli("characterise", "--source", self.source, "--target", self.target, "--agent", self.config, "--repairs", repairs, code=code)

    def state(self):
        return json.loads((self.workspace / "state.json").read_text())

    def mode(self, value):
        (self.workspace / "mode").write_text(value)

    def approve(self):
        self.cli("approve", "--revision", self.state()["Revision"])

    def test_approval_resume_and_accepted_stages_are_not_rerun(self):
        self.characterise()
        self.assertEqual("awaiting-approval", self.state()["Status"])
        self.cli("resume")
        self.assertEqual(["characterise"], (self.workspace / "calls").read_text().splitlines())
        self.cli("approve", "--revision", "wrong", code=1)
        self.approve()
        self.cli("resume")
        self.cli("resume")
        self.assertEqual("completed", self.state()["Status"])
        self.assertEqual(["characterise", "convert", "refactor"], (self.workspace / "calls").read_text().splitlines())
        self.cli("status")

    def test_each_reviewed_input_change_requires_new_approval(self):
        self.characterise()
        attempts = self.workspace / "characterise" / "attempts"
        retained = {}
        for number, changed in enumerate(("source", "target", "behaviour.md", "scenarios.json", "reference/check.py"), start=2):
            with self.subTest(changed=changed):
                retained.update({path.relative_to(attempts): path.read_bytes()
                                 for path in attempts.rglob("*") if path.is_file()})
                self.approve()
                path = self.source if changed == "source" else self.target if changed == "target" else self.workspace / "characterise" / changed
                path.write_text(path.read_text() + "\nchanged")
                self.cli("resume")
                self.assertEqual("awaiting-approval", self.state()["Status"])
                self.assertIsNone(self.state()["ApprovedRevision"])
                self.assertNotIn("convert", (self.workspace / "calls").read_text())
                self.assertEqual(number, self.state()["Stages"][0]["Attempts"])
                self.assertEqual([f"{i:04d}" for i in range(1, number + 1)],
                                 sorted(path.name for path in attempts.iterdir()))
                self.assertTrue((attempts / f"{number:04d}" / "request.json").is_file())
                current_files = {path.relative_to(attempts) for path in attempts.rglob("*") if path.is_file()}
                self.assertTrue(set(retained).issubset(current_files))
                for relative, contents in retained.items():
                    self.assertEqual(contents, (attempts / relative).read_bytes(), str(relative))

    def test_malformed_and_incomplete_results_fail_with_retained_evidence(self):
        results = [
            '{"passed":1}',
            '{"passed":1,"failed":0}',
            '{"passed":1,"skipped":0}',
            '{"failed":0,"skipped":0}',
            '{}', 'null', '[]', '{broken',
            '{"passed":1,"failed":null,"skipped":0}',
            '{"passed":1,"failed":"0","skipped":0}',
            '{"passed":1,"failed":0,"skipped":0.5}',
        ]
        self.mode("custom-result")
        for number, result_text in enumerate(results, start=1):
            with self.subTest(result=result_text):
                (self.workspace / "custom-result.json").write_text(result_text)
                if number == 1:
                    self.characterise(code=1)
                else:
                    self.cli("resume", code=1)
                self.assertEqual("failed", self.state()["Status"])
                self.assertIsNone(self.state()["ApprovedRevision"])
                evidence = self.workspace / "characterise" / "attempts" / f"{number:04d}"
                self.assertEqual(result_text, (evidence / "results-0.json").read_text())
                self.assertTrue((evidence / "failure.txt").read_text())
                self.cli("approve", "--revision", "anything", code=1)
        self.mode("ok")
        self.cli("resume")
        self.assertEqual("awaiting-approval", self.state()["Status"])

    def test_blocking_gap_prevents_approval(self):
        self.mode("gap")
        self.characterise()
        self.cli("approve", "--revision", self.state()["Revision"], code=1)
        self.assertIsNone(self.state()["ApprovedRevision"])

    def test_empty_skipped_failed_missing_and_stale_checks_fail(self):
        for mode in ("empty", "skipped", "failed-check", "missing-check", "stale"):
            with self.subTest(mode=mode):
                self.mode(mode)
                if (self.workspace / "state.json").exists():
                    self.cli("resume", code=1)
                else:
                    self.characterise(code=1)
                self.assertEqual("failed", self.state()["Status"])
                self.assertTrue(list(self.workspace.glob("characterise/attempts/*/failure.txt")))

    def test_repairs_are_bounded_and_resume_recovers(self):
        self.mode("agent-fails")
        self.characterise(code=1, repairs=2)
        self.assertEqual(3, self.state()["Stages"][0]["Attempts"])
        self.assertEqual(3, len(list(self.workspace.glob("characterise/attempts/*/agent.stderr.txt"))))
        self.mode("ok")
        self.cli("resume")
        self.approve()
        self.mode("convert-fails")
        self.cli("resume", code=1)
        self.assertEqual("accepted", self.state()["Stages"][0]["Status"])
        self.mode("ok")
        self.cli("resume")
        calls = (self.workspace / "calls").read_text().splitlines()
        self.assertEqual(4, calls.count("characterise"))
        self.assertEqual(1, calls.count("refactor"))
        self.assertEqual("completed", self.state()["Status"])

    def test_downstream_gates_retain_failures_and_resume_only_failed_stage(self):
        self.characterise()
        self.approve()
        approved = self.state()["ApprovedRevision"]
        retained = {}
        for attempt, gate in enumerate(("build", "style", "parity", "stale"), start=1):
            with self.subTest(gate=gate):
                self.mode("gate-" + gate)
                self.cli("resume", code=1)
                state = self.state()
                self.assertEqual("failed", state["Status"])
                self.assertEqual(approved, state["ApprovedRevision"])
                self.assertEqual(["accepted", "accepted", "failed"],
                                 [stage["Status"] for stage in state["Stages"]])
                evidence = self.workspace / "refactor/attempts" / f"{attempt:04d}"
                failure = (evidence / "failure.txt").read_text()
                self.assertTrue(failure)
                index = {"build": 0, "style": 1, "parity": 2, "stale": 2}[gate]
                self.assertTrue((evidence / f"check-{index}.command.json").exists())
                self.assertIn("executed", (evidence / f"check-{index}.stdout.txt").read_text())
                if gate in ("build", "style"):
                    self.assertIn("exited 9", failure)
                    self.assertIn("deliberate gate failure", (evidence / f"check-{index}.stderr.txt").read_text())
                elif gate == "parity":
                    self.assertEqual(1, json.loads((evidence / "results-2.json").read_text())["failed"])
                    report = json.loads((self.workspace / "refactor/parity-report.json").read_text())
                    self.assertEqual("synthetic-mismatch", report["id"])
                    self.assertFalse(report["matches"])
                else:
                    self.assertFalse((self.workspace / "refactor/parity-results.json").exists())
                if attempt > 1:
                    request = json.loads((evidence / "request.json").read_text())
                    self.assertEqual(previous_diagnostic, request["PreviousDiagnostic"])
                previous_diagnostic = state["Stages"][-1]["Diagnostic"]
                for path in self.workspace.glob("*/attempts/**/*"):
                    if path.is_file():
                        relative = path.relative_to(self.workspace)
                        if relative in retained:
                            self.assertEqual(retained[relative], path.read_bytes(), str(relative))
                        else:
                            retained[relative] = path.read_bytes()
        self.mode("gate-ok")
        self.cli("resume")
        self.assertEqual("completed", self.state()["Status"])
        self.assertEqual(approved, self.state()["ApprovedRevision"])
        self.assertEqual(["characterise", "convert"] + ["refactor"] * 5,
                         (self.workspace / "calls").read_text().splitlines())
        request = json.loads((self.workspace / "refactor/attempts/0005/request.json").read_text())
        self.assertEqual(previous_diagnostic, request["PreviousDiagnostic"])
        for relative, contents in retained.items():
            self.assertEqual(contents, (self.workspace / relative).read_bytes(), str(relative))

    def test_workspace_cannot_be_overwritten(self):
        self.characterise()
        self.characterise(code=1)
        self.assertEqual("awaiting-approval", self.state()["Status"])


if __name__ == "__main__":
    unittest.main()
