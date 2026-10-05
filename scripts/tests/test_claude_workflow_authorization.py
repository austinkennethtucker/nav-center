"""Execute the actual workflow authorization shell with synthetic permissions."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


class ClaudeWorkflowAuthorizationTests(unittest.TestCase):
    def run_gate(self, filename, original="write", rerun="write", failure=False):
        text = (REPO / ".github/workflows" / filename).read_text()
        gate = text.split("      - name: Authorize workflow caller\n", 1)[1]
        run = gate.split("        run: |\n", 1)[1].split("\n      - name:", 1)[0]
        run = "\n".join(line[10:] for line in run.splitlines())
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            gh = root / "gh"
            gh.write_text("#!/bin/bash\n" +
                          "[[ $FAILURE != 1 ]] || exit 1\n" +
                          "case $2 in */first/permission) printf '%s' \"$ORIGINAL_PERMISSION\" ;; " +
                          "*/rerun/permission) printf '%s' \"$RERUN_PERMISSION\" ;; *) exit 2 ;; esac\n")
            gh.chmod(0o700)
            output = root / "output"
            env = {"PATH": directory + ":/usr/bin:/bin", "REPOSITORY": "owner/repo",
                   "CALLER": "first", "ORIGINAL_CALLER": "rerun", "GITHUB_OUTPUT": str(output),
                   "ORIGINAL_PERMISSION": original, "RERUN_PERMISSION": rerun,
                   "FAILURE": "1" if failure else "0"}
            result = subprocess.run(["bash", "-c", run], env=env, capture_output=True, text=True)
            return result.returncode, output.read_text() if output.exists() else ""

    def test_only_write_capable_original_and_rerun_callers_reach_secrets(self):
        for workflow in ("claude.yml", "claude-code-review.yml"):
            for first, second, accepted in (("write", "admin", True), ("read", "write", False),
                                            ("write", "read", False), ("none", "admin", False)):
                with self.subTest(workflow=workflow, first=first, second=second):
                    code, output = self.run_gate(workflow, first, second)
                    self.assertEqual(code == 0, accepted)
                    self.assertEqual("trusted=true" in output, accepted)

    def test_permission_api_failure_is_closed(self):
        for workflow in ("claude.yml", "claude-code-review.yml"):
            code, output = self.run_gate(workflow, failure=True)
            self.assertNotEqual(code, 0)
            self.assertEqual(output, "")

    def test_secret_actions_use_gate_and_no_dynamic_marketplace(self):
        for workflow in ("claude.yml", "claude-code-review.yml"):
            text = (REPO / ".github/workflows" / workflow).read_text()
            action = text.split("      - name: Run Claude Code", 1)[1]
            self.assertIn("if: steps.authorize.outputs.trusted == 'true'", action)
            self.assertIn("github_token: ${{ github.token }}", action)
            self.assertNotIn("plugin_marketplaces:", text)
            self.assertNotIn("id-token: write", text)
