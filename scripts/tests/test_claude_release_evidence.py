"""The skill delegates to the canonical verifier, including publisher checks."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import unittest

import test_release_scripts as release


class ClaudeReleaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = release.ReleaseScriptsTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.script = self.fixture.root / ".claude/skills/release-evidence/verify-artifact.sh"
        self.script.parent.mkdir(parents=True)
        shutil.copy2(release.REPO / ".claude/skills/release-evidence/verify-artifact.sh", self.script)
        self.image = self.fixture.stage_artifact()
        self.env = self.fixture.env | {
            "FAKE_MOUNT_SOURCE": str(self.fixture.stage_mount()),
            "NAV_CENTER_EXPECTED_SHA256": hashlib.sha256(self.image.read_bytes()).hexdigest(),
        }

    def run_check(self):
        return subprocess.run(["bash", str(self.script), str(self.image)],
                              env=self.env, capture_output=True, text=True, timeout=15)

    def test_canonical_checks_run_and_mount_read_only(self):
        result = self.run_check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS codesign --verify --deep --strict", result.stdout)
        self.assertIn("Clean-machine and release acceptance remain separate", result.stdout)
        calls = self.fixture.events()
        self.assertTrue(any("-readonly" in call["args"] for call in calls))

    def test_wrong_team_rejected(self):
        self.env["FAKE_SIGNING_TEAM"] = "EVILTEAM01"
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_wrong_bundle_rejected(self):
        self.env["FAKE_BUNDLE_ID"] = "com.attacker.lookalike"
        self.assertNotEqual(self.run_check().returncode, 0)

    def test_matching_sidecars_cannot_replace_trusted_digest(self):
        self.env["NAV_CENTER_EXPECTED_SHA256"] = "0" * 64
        self.assertNotEqual(self.run_check().returncode, 0)


if __name__ == "__main__":
    unittest.main()
