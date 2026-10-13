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

    def test_unknown_or_missing_version_does_not_parse_foreign_mappings(self):
        for version, reason in (
            ("schema_version: 9\n", "unsupported_schema_version"),
            ("", "missing_schema_version"),
        ):
            content = f"---\n{version}future_metadata:\n  nested:\n    commit: {SHA}\n---\n"
            code, payload = self.run_validator(content)
            self.assertEqual(0, code)
            self.assertEqual({"status": "UNVERIFIED", "reason": reason}, payload)

    def test_body_examples_cannot_supply_or_override_metadata(self):
        example = f"# Project Guidance\n```yaml\nverified_commits:\n  Logging: {SHA}\n```\n"
        for prefix, status in (
            ("---\nschema_version: 2\n---\n", "UNVERIFIED"),
            (f"---\nschema_version: 2\nverified_commits:\n  Logging: {SHA}\n---\n", "VALID"),
            ("---\nschema_version: 2\nverified_commits:\n  Logging: invalid\n---\n", "UNVERIFIED"),
        ):
            with self.subTest(prefix=prefix):
                code, payload = self.run_validator(prefix + example)
                self.assertEqual(0, code)
                self.assertEqual(status, payload["status"])

    def test_duplicate_metadata_and_section_commits_are_invalid(self):
        for content, reason in (
            (f"schema_version: 1\nschema_version: 2\nverified_commit: {SHA}", "duplicate_metadata_key"),
            (f"schema_version: 2\nverified_commits:\n  Logging: {SHA}\n  Logging: {SHA}", "duplicate_section_commit"),
            (f"schema_version: 2\nverified_commits:\n  Logging: {SHA}\nverified_commits:\n  Exception Handling: {SHA}", "duplicate_metadata_key"),
        ):
            with self.subTest(reason=reason, content=content):
                code, payload = self.run_validator(f"---\n{content}\n---\n")
                self.assertEqual(1, code)
                self.assertEqual({"status": "INVALID", "reason": reason}, payload)

    def test_malformed_mapping_cannot_be_reported_valid(self):
        for mapping in (
            f"verified_commits: {{Logging: {SHA}}}",
            f"verified_commits:\n Logging: {SHA}",
            f"verified_commits:\n  Logging:\n    nested: {SHA}",
            f"verified_commits:\n\tLogging: {SHA}",
            f"verified_commits:\n  Logging: \"{SHA}",
        ):
            with self.subTest(mapping=mapping):
                code, payload = self.run_validator(f"---\nschema_version: 2\n{mapping}\n---\n")
                self.assertEqual(1, code)
                self.assertEqual("INVALID", payload["status"])

    def test_angle_brackets_are_not_stripped_from_commit_placeholders(self):
        code, payload = self.run_validator(
            f"---\nschema_version: 2\nverified_commits:\n  Logging: <{SHA}>\n---\n"
        )
        self.assertEqual(0, code)
        self.assertEqual("UNVERIFIED", payload["status"])

    def test_quoted_values_and_comments_are_valid(self):
        code, payload = self.run_validator(
            f"---\n# reference only\nschema_version: '2'\nverified_commits: # per-section\n"
            f"  'Logging': \"{SHA}\"\n  Exception Handling: {SHA} # checked\n---\n"
        )
        self.assertEqual(0, code)
        self.assertEqual({"status": "VALID"}, payload)


if __name__ == "__main__":
    unittest.main()
