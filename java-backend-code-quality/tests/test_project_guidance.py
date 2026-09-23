import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "validate_project_guidance.py"
SHA = "0123456789abcdef0123456789abcdef01234567"


class ProjectGuidanceMetadataTests(unittest.TestCase):
    def run_validator(self, content: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "project-guidance.md"
            path.write_text(content, encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                capture_output=True,
                text=True,
                check=False,
            )
        return completed.returncode, json.loads(completed.stdout)

    def test_schema_v2_has_independent_section_commits(self):
        content = """---
schema_version: 2
verified_commits:
  Logging: 0123456789abcdef0123456789abcdef01234567
  Exception Handling: 0123456789abcdef0123456789abcdef01234567
---
# Project Guidance
"""
        code, payload = self.run_validator(content)
        self.assertEqual(0, code)
        self.assertEqual({"status": "VALID"}, payload)

    def test_schema_v1_is_legacy(self):
        code, payload = self.run_validator(
            f"---\nschema_version: 1\nverified_commit: {SHA}\n---\n"
        )
        self.assertEqual(0, code)
        self.assertEqual({"status": "VALID_LEGACY"}, payload)

    def test_missing_or_unknown_version_is_unverified(self):
        for content, reason in (
            ("---\nverified_commit: " + SHA + "\n---\n", "missing_schema_version"),
            ("---\nschema_version: 9\n---\n", "unsupported_schema_version"),
        ):
            code, payload = self.run_validator(content)
            self.assertEqual(0, code)
            self.assertEqual({"status": "UNVERIFIED", "reason": reason}, payload)

    def test_v2_does_not_accept_unknown_sections(self):
        content = f"---\nschema_version: 2\nverified_commits:\n  Current Classes: {SHA}\n---\n"
        code, payload = self.run_validator(content)
        self.assertEqual(1, code)
        self.assertEqual({"status": "INVALID", "reason": "unknown_guidance_section"}, payload)


if __name__ == "__main__":
    unittest.main()
