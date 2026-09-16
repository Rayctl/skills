import importlib.util
import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]


def load_script(name):
    path = SKILL_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SemanticEvaluationValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_script("validate_semantic_evals.py")

    def valid_payload(self):
        return {
            "schema_version": 1,
            "cases": [
                {
                    "id": "example-case",
                    "title": "Example",
                    "mode": "review",
                    "triggers": ["method-design"],
                    "fixture": "A small Java fixture",
                    "expected_decisions": ["Make the required decision"],
                    "disallowed_decisions": ["Do not make the wrong decision"],
                }
            ],
        }

    def run_main(self, path):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.validator.main([str(path)])
        return code, json.loads(stdout.getvalue())

    def write_payload(self, directory, payload):
        path = Path(directory) / "cases.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_repository_catalog_is_structurally_valid(self):
        path = SKILL_ROOT / "evals" / "semantic-cases.json"

        code, result = self.run_main(path)

        self.assertEqual(0, code)
        self.assertEqual("VALID", result["status"])
        self.assertGreaterEqual(result["case_count"], 10)

    def test_duplicate_case_id_is_invalid(self):
        payload = self.valid_payload()
        payload["cases"].append(dict(payload["cases"][0]))
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_payload(temporary, payload)

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual("duplicate_case_id", result["reason"])
        self.assertEqual(2, result["case_index"])

    def test_missing_case_field_is_invalid(self):
        payload = self.valid_payload()
        del payload["cases"][0]["fixture"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_payload(temporary, payload)

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual("case_fields_do_not_match_schema", result["reason"])

    def test_empty_expected_decisions_are_invalid(self):
        payload = self.valid_payload()
        payload["cases"][0]["expected_decisions"] = []
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_payload(temporary, payload)

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual("expected_decisions_must_be_non_empty_list", result["reason"])

    def test_unknown_reference_trigger_is_invalid(self):
        payload = self.valid_payload()
        payload["cases"][0]["triggers"] = ["missing-reference"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_payload(temporary, payload)

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual("unknown_trigger", result["reason"])

    def test_non_string_mode_is_invalid_without_traceback(self):
        payload = self.valid_payload()
        payload["cases"][0]["mode"] = ["review"]
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write_payload(temporary, payload)

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual("invalid_mode", result["reason"])

    def test_invalid_json_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            path.write_text("{", encoding="utf-8")

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual({"status": "INVALID", "reason": "invalid_json"}, result)

    def test_invalid_utf8_is_reported_without_traceback(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "cases.json"
            path.write_bytes(b"\xff")

            code, result = self.run_main(path)

        self.assertEqual(1, code)
        self.assertEqual({"status": "INVALID", "reason": "invalid_utf8"}, result)


class InstallationVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = load_script("verify_skill_installation.py")

    def create_skill(self, root, files):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        if "SKILL.md" not in files:
            files = {"SKILL.md": "---\nname: example\n---\n", **files}
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return root

    def run_main(self, source, target):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = self.verifier.main(
                ["--source", str(source), "--target", str(target)]
            )
        return code, json.loads(stdout.getvalue())

    def tree_snapshot(self, root):
        return {
            path.relative_to(root).as_posix(): path.read_bytes()
            for path in Path(root).rglob("*")
            if path.is_file()
        }

    def test_matching_installation_passes_without_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create_skill(
                Path(temporary) / "source",
                {"references/rules.md": "rules\n"},
            )
            target = self.create_skill(
                Path(temporary) / "target",
                {"references/rules.md": "rules\n"},
            )
            before_source = self.tree_snapshot(source)
            before_target = self.tree_snapshot(target)

            code, result = self.run_main(source, target)

            self.assertEqual(0, code)
            self.assertEqual("MATCH", result["status"])
            self.assertEqual(before_source, self.tree_snapshot(source))
            self.assertEqual(before_target, self.tree_snapshot(target))

    def test_missing_extra_and_changed_files_are_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create_skill(
                Path(temporary) / "source",
                {"same.md": "source\n", "missing.md": "missing\n"},
            )
            target = self.create_skill(
                Path(temporary) / "target",
                {"same.md": "target\n", "extra.md": "extra\n"},
            )

            code, result = self.run_main(source, target)

        self.assertEqual(1, code)
        self.assertEqual("DIFF", result["status"])
        self.assertEqual(["missing.md"], result["missing"])
        self.assertEqual(["extra.md"], result["extra"])
        self.assertEqual(["same.md"], result["changed"])

    def test_runtime_cache_files_are_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = self.create_skill(Path(temporary) / "source", {})
            target = self.create_skill(Path(temporary) / "target", {})
            cache = target / "scripts" / "__pycache__" / "tool.pyc"
            cache.parent.mkdir(parents=True)
            cache.write_bytes(b"runtime cache")

            code, result = self.run_main(source, target)

        self.assertEqual(0, code)
        self.assertEqual("MATCH", result["status"])

    def test_missing_skill_entrypoint_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()
            target = self.create_skill(Path(temporary) / "target", {})

            code, result = self.run_main(source, target)

        self.assertEqual(2, code)
        self.assertEqual("source_missing_skill_entrypoint", result["reason"])


if __name__ == "__main__":
    unittest.main()
