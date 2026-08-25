import io
import importlib.util
import subprocess
import sys
import tempfile
import textwrap
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "check_java_backend_style.py"


def load_checker():
    spec = importlib.util.spec_from_file_location("check_java_backend_style", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckerTestCase(unittest.TestCase):
    def run_checker(self, *args, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def write(self, root, relative, content):
        path = Path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip("\n"), encoding="utf-8")
        return path

    def git(self, repo, *args):
        return subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout.strip()

    def make_repo(self):
        temporary = tempfile.TemporaryDirectory()
        repo = Path(temporary.name).resolve()
        self.git(repo, "init")
        self.git(repo, "config", "user.email", "checker@example.test")
        self.git(repo, "config", "user.name", "Checker Tests")
        return temporary, repo


class FullFileRuleTests(CheckerTestCase):
    def test_comment_full_stops_fail_but_periods_in_code_and_strings_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Comments.java", r'''
                class Comments {
                    // English period.
                    String english = "value.";
                    // Chinese period。
                    String chinese = "。";
                    int decimal = 1.5 > 1 ? 1 : 0;
                }
            ''')

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(2, result.stdout.count("STYLE-COMMENT-001"), result.stdout)
            self.assertNotIn("String english", result.stdout)
            self.assertNotIn("int decimal", result.stdout)

    def test_method_spacing_requires_exactly_one_blank_line(self):
        cases = {
            "zero": ("    }\n    void second()", 1),
            "one": ("    }\n\n    void second()", 0),
            "multiple": ("    }\n\n\n    void second()", 1),
        }
        for name, (boundary, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = "class Methods {\n    void first() {\n" + boundary + " {\n    }\n}\n"
                path = self.write(temporary, "Methods.java", source)

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(expected_code, result.stdout.count("STYLE-METHOD-001"))

    def test_wrapped_method_declarations_use_first_declaration_line(self):
        declarations = {
            "public": "    public\n    void second()",
            "modifiers": "    public static\n    void second()",
            "generic": "    <T>\n    T second()",
            "return_type": "    String\n    second()",
        }
        gaps = {
            "zero": ("\n", 1),
            "one": ("\n\n", 0),
            "multiple": ("\n\n\n", 1),
        }
        for declaration_name, declaration in declarations.items():
            for gap_name, (gap, expected_code) in gaps.items():
                with self.subTest(
                        declaration=declaration_name, gap=gap_name
                ), tempfile.TemporaryDirectory() as temporary:
                    source = (
                        "class WrappedMethods {\n"
                        "    void first() {\n"
                        "    }"
                        + gap
                        + declaration
                        + " {\n    }\n}\n"
                    )
                    path = self.write(temporary, "WrappedMethods.java", source)

                    result = self.run_checker(path)

                    self.assertEqual(expected_code, result.returncode, result)
                    self.assertEqual(
                        expected_code, result.stdout.count("STYLE-METHOD-001")
                    )
                    if expected_code:
                        self.assertIn(declaration.splitlines()[0].strip(), result.stdout)

    def test_output_contains_absolute_path_line_rule_and_offending_content(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Output.java", "class Output {\n    // Bad.\n}\n").resolve()

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn(str(path), result.stdout)
            self.assertRegex(result.stdout, r":2: STYLE-COMMENT-001:")
            self.assertIn("// Bad.", result.stdout)

    def test_methods_inside_anonymous_class_are_not_enclosing_class_methods(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "AnonymousMethods.java", """
                class AnonymousMethods {
                    void outerFirst() {
                    }
                    Runnable task = new Runnable() {
                        @Override
                        public void run() {
                        }
                    };
                    void outerSecond() {
                    }
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_anonymous_class_method_spacing_requires_exactly_one_blank_line(self):
        cases = {
            "zero": ("        }\n        void second()", 1),
            "one": ("        }\n\n        void second()", 0),
            "multiple": ("        }\n\n\n        void second()", 1),
        }
        for name, (boundary, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = (
                    "class AnonymousSpacing {\n"
                    "    Runnable task = new Runnable() {\n"
                    "        void first() {\n"
                    + boundary
                    + " {\n        }\n    };\n}\n"
                )
                path = self.write(temporary, "AnonymousSpacing.java", source)

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(expected_code, result.stdout.count("STYLE-METHOD-001"))

    def test_methods_separated_by_a_field_are_not_adjacent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "FieldSeparated.java", """
                class FieldSeparated {
                    void first() {
                    }
                    int value;
                    void second() {
                    }
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_same_line_annotated_field_prevents_method_adjacency(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "AnnotatedField.java", """
                class AnnotatedField {
                    void first() {
                    }
                    @Deprecated int value;
                    void second() {
                    }
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_same_line_adjacent_methods_still_fail_without_inverted_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "SameLineMethods.java",
                "class SameLineMethods { void first() {} void second() {} }\n",
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-METHOD-001", result.stdout)

    def test_multiline_annotation_method_spacing_uses_annotation_start(self):
        cases = {
            "zero": ("    }\n    @SuppressWarnings", 1),
            "one": ("    }\n\n    @SuppressWarnings", 0),
            "multiple": ("    }\n\n\n    @SuppressWarnings", 1),
        }
        for name, (boundary, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = (
                    "class AnnotatedMethods {\n"
                    "    void first() {\n"
                    + boundary
                    + "({\n        \"unchecked\",\n        \"rawtypes\"\n    })\n"
                    "    void second() {\n    }\n}\n"
                )
                path = self.write(temporary, "AnnotatedMethods.java", source)

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(expected_code, result.stdout.count("STYLE-METHOD-001"))

    def test_field_before_multiline_annotation_prevents_method_adjacency(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "AnnotatedFieldSeparated.java", """
                class AnnotatedFieldSeparated {
                    void first() {
                    }
                    int value;
                    @SuppressWarnings({
                        "unchecked",
                        "rawtypes"
                    })
                    void second() {
                    }
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_interface_bodyless_method_spacing_requires_exactly_one_blank_line(self):
        cases = {
            "zero": ("    void first();\n    @Deprecated", 1),
            "one": ("    void first();\n\n    @Deprecated", 0),
            "multiple": ("    void first();\n\n\n    @Deprecated", 1),
        }
        for name, (boundary, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = (
                    "interface BodylessContract {\n"
                    + boundary
                    + "\n    String second() throws java.io.IOException;\n}\n"
                )
                path = self.write(temporary, "BodylessContract.java", source)

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(expected_code, result.stdout.count("STYLE-METHOD-001"))

    def test_named_annotation_arguments_do_not_hide_bodyless_methods(self):
        cases = {
            "zero": ("    void first();\n    @SuppressWarnings(value = \"x\")", 1),
            "one": ("    void first();\n\n    @SuppressWarnings(value = \"x\")", 0),
            "multiple": (
                "    void first();\n\n\n    @SuppressWarnings(value = \"x\")",
                1,
            ),
        }
        for name, (boundary, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                source = (
                    "interface AnnotatedContract {\n"
                    + boundary
                    + "\n    String second();\n}\n"
                )
                path = self.write(temporary, "AnnotatedContract.java", source)

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(expected_code, result.stdout.count("STYLE-METHOD-001"))

    def test_array_annotation_argument_does_not_hide_bodyless_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "ArrayAnnotatedContract.java", '''
                interface ArrayAnnotatedContract {
                    void first();
                    @SuppressWarnings(value = {"unchecked", "rawtypes"})
                    String second();
                }
            ''')

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-METHOD-001"), result.stdout)

    def test_inline_annotation_placements_preserve_bodyless_spacing(self):
        declarations = {
            "modifier": 'public @A(value = "x") String second();',
            "type": 'java.util.@A(value = {"x", "y"}) List<String> second();',
        }
        gaps = {
            "zero": ("\n", 1),
            "one": ("\n\n", 0),
            "multiple": ("\n\n\n", 1),
        }
        for placement, declaration in declarations.items():
            for gap_name, (gap, expected_code) in gaps.items():
                with self.subTest(
                        placement=placement, gap=gap_name
                ), tempfile.TemporaryDirectory() as temporary:
                    source = (
                        "interface InlineAnnotatedContract {\n"
                        "    void first();"
                        + gap
                        + "    "
                        + declaration
                        + "\n}\n"
                    )
                    path = self.write(temporary, "InlineAnnotatedContract.java", source)

                    result = self.run_checker(path)

                    self.assertEqual(expected_code, result.returncode, result)
                    self.assertEqual(
                        expected_code, result.stdout.count("STYLE-METHOD-001")
                    )

    def test_throws_annotation_array_does_not_end_bodyless_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "ThrowsAnnotatedContract.java", '''
                interface ThrowsAnnotatedContract {
                    void first();

                    String second() throws @A(value = {"x", "y"}) Exception;
                    void third();
                }
            ''')

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-METHOD-001"), result.stdout)
            self.assertIn("void third();", result.stdout)

    def test_abstract_body_and_native_declarations_share_spacing_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "AbstractNative.java", """
                abstract class AbstractNative {
                    abstract void first();
                    void second() {
                    }
                    native void third();
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(2, result.stdout.count("STYLE-METHOD-001"), result.stdout)

    def test_annotation_members_are_bodyless_method_declarations(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Settings.java", """
                @interface Settings {
                    String name();
                    int[] values() default {1, 2};
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-METHOD-001"), result.stdout)

    def test_body_statements_initializer_and_field_calls_are_not_bodyless_methods(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "InitializerCalls.java", """
                class InitializerCalls {
                    void run() {
                        assert first();
                        assert second();
                        firstLabel: first();
                        secondLabel: second();
                        Util.<String>first();
                        Util.<String>second();
                    }
                    {
                        initialize();
                        cleanup();
                    }
                    Object firstValue = build();
                    Object secondValue = build();
                }
            """)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_escaped_text_block_delimiter_keeps_comment_shaped_text_masked(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = "\n".join([
                "class TextBlockSource {",
                '    String value = """',
                r'        escaped delimiter \"""',
                "        // Text block content is not a Java comment.",
                '        """;',
                "}",
                "",
            ])
            path = self.write(temporary, "TextBlockSource.java", source)

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class CatchRuleTests(CheckerTestCase):
    def catch_source(self, behavior, prefix=""):
        return f"""
            class Catcher {{
                Object run() {{
                    // Try-leading intent does not describe the catch branch
                    try {{
                        return work();
                    }} catch (RuntimeException exception) {{
                        {prefix}
                        {behavior}
                    }}
                }}

                Object work() {{
                    return new Object();
                }}
            }}
        """

    def test_fallback_return_requires_catch_local_comment(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "ReturnCatch.java", self.catch_source("return null;"))

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-CATCH-001", result.stdout)
            self.assertIn("return null;", result.stdout)

    def test_catch_local_intent_comment_before_behavior_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "CommentedCatch.java",
                self.catch_source("return null;", "// Remote lookup failed; preserve availability with an empty result"),
            )

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_adjacent_block_comment_before_behavior_passes(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "BlockCommentCatch.java",
                self.catch_source("/* Remote lookup failed; preserve empty fallback */return null;"),
            )

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_log_text_does_not_replace_a_comment(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "LoggedCatch.java",
                self.catch_source('return null;', 'log.warn("fallback because lookup failed");'),
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-CATCH-001", result.stdout)
            self.assertIn("return null;", result.stdout)

    def test_comment_after_behavior_is_too_late(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "LateCommentCatch.java",
                self.catch_source("return null; // Fallback intent is documented too late"),
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-CATCH-001", result.stdout)

    def test_comment_then_statement_does_not_cover_later_behavior(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "InterveningStatementCatch.java",
                self.catch_source(
                    "return null;",
                    "// Lookup failed; record the fallback metric\nrecordFallbackMetric();",
                ),
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-CATCH-001", result.stdout)
            self.assertIn("return null;", result.stdout)

    def test_comment_before_first_return_does_not_cover_second_return(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "MultipleReturnCatch.java",
                self.catch_source("""
                    if (usePrimary()) {
                        // Primary lookup failed; preserve its fallback result
                        return work();
                    }
                    return null;
                """),
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-CATCH-001"), result.stdout)
            self.assertIn("return null;", result.stdout)
            self.assertNotIn("return work();", result.stdout)

    def test_transparent_direct_rethrow_is_exempt(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "RethrowCatch.java", self.catch_source("throw exception;"))

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_all_deterministic_behavior_triggers_are_covered(self):
        cases = {
            "return": "return null;",
            "break": "while (true) { break; }",
            "continue": "while (true) { continue; }",
            "throw-new": "throw new IllegalStateException(exception);",
        }
        for name, behavior in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                path = self.write(temporary, "Trigger.java", self.catch_source(behavior))

                result = self.run_checker(path)

                self.assertEqual(1, result.returncode, result)
                self.assertIn("STYLE-CATCH-001", result.stdout)
                self.assertIn(behavior.split("{")[-1].strip(), result.stdout)

    def test_return_inside_lambda_does_not_trigger_catch_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "LambdaCatch.java",
                self.catch_source("throw exception;", "Runnable task = () -> { return; };"),
            )

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)


class IntentAndGuardRuleTests(CheckerTestCase):
    def generalized_url_builder_source(self):
        return """
            class RequestUrlBuilder {
                String build(Config config, Request request) {
                    if (config == null) {
                        throw new IllegalArgumentException("config");
                    }
                    if (request == null) {
                        throw new IllegalArgumentException("request");
                    }
                    String baseUrl = config.baseUrl();
                    if (baseUrl == null) {
                        throw new IllegalStateException("baseUrl");
                    }
                    if (config.path() == null) {
                        throw new IllegalStateException("path");
                    }
                    java.util.Set<String> placeholders = config.placeholders();
                    java.util.Map<String, Object> mappedPath = request.pathValues();
                    if (!placeholders.equals(mappedPath.keySet())) {
                        throw new IllegalArgumentException("path values");
                    }
                    java.util.Map<String, Object> pathValues = new java.util.LinkedHashMap<>();
                    for (java.util.Map.Entry<String, Object> entry : mappedPath.entrySet()) {
                        if (entry.getValue() == null) {
                            throw new IllegalArgumentException("path value");
                        }
                        pathValues.put(entry.getKey(), entry.getValue());
                    }
                    try {
                        String endpoint = expand(baseUrl, config.path(), pathValues);
                        String query = buildEncodedQuery(request.queryValues());
                        if (query == null) {
                            return endpoint;
                        }
                        return endpoint + "?" + query;
                    } catch (IllegalArgumentException exception) {
                        // Invalid expansion prevents sending an ambiguous request
                        throw new IllegalStateException("invalid URL", exception);
                    }
                }

                String buildEncodedQuery(java.util.Map<String, Object> values) {
                    if (values == null || values.isEmpty()) {
                        return null;
                    }
                    StringBuilder query = new StringBuilder();
                    for (java.util.Map.Entry<String, Object> entry : values.entrySet()) {
                        if (entry.getKey() == null || entry.getValue() == null) {
                            continue;
                        }
                        if (entry.getValue() instanceof java.util.Collection) {
                            for (Object item : (java.util.Collection<?>) entry.getValue()) {
                                if (item != null) {
                                    query.append(entry.getKey()).append(stringifyQueryValue(item));
                                }
                            }
                        } else {
                            query.append(entry.getKey()).append(stringifyQueryValue(entry.getValue()));
                        }
                    }
                    return query.toString();
                }

                String stringifyQueryValue(Object value) {
                    if (value instanceof String) {
                        return (String) value;
                    }
                    if (value instanceof Number || value instanceof Boolean) {
                        return String.valueOf(value);
                    }
                    try {
                        return serialize(value);
                    } catch (RuntimeException exception) {
                        // Serialization failure preserves the legacy string fallback
                        return String.valueOf(value);
                    }
                }
            }
        """

    def complex_method_source(self, top_level_comment=""):
        return f"""
            class Selector {{
                /**
                 * Selects the first usable candidate
                 */
                Object select(java.util.List<Object> values) {{
                    Object selected = null;
                    {top_level_comment}
                    try {{
                        for (Object value : values) {{
                            if (isPrimary(value)) {{
                                // Nested branch comments only describe their branch
                                selected = value;
                            }} else if (isCompatible(value)) {{
                                selected = adapt(value);
                            }}
                        }}
                    }} catch (RuntimeException exception) {{
                        // Candidate inspection failure returns the stable empty fallback
                        return null;
                    }}
                    log.info("candidate selection completed");
                    while (selected != null && !isReady(selected)) {{
                        selected = next(selected);
                    }}
                    return selected;
                }}
            }}
        """

    def guard_source(self, guards, comment="", extraction_after=None):
        statements = []
        for index in range(guards):
            statements.extend([
                f"if (input.value{index}() == null) {{",
                f"    throw new IllegalArgumentException(\"value{index}\");",
                "}",
            ])
            if extraction_after == index:
                statements.append("String selected = input.selected();")
        if extraction_after is None:
            statements.append("String selected = input.selected();")
        statements.append("return selected;")
        body = "\n".join("                    " + line for line in statements)
        return f"""
            class GuardedBuilder {{
                String build(Input input) {{
                    {comment}
{body}
                }}
            }}
        """

    def test_generalized_url_builder_reports_guard_and_stage_omissions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary, "RequestUrlBuilder.java", self.generalized_url_builder_source()
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-GUARD-001"), result.stdout)
            self.assertEqual(2, result.stdout.count("STYLE-INTENT-001"), result.stdout)
            self.assertIn("String build(Config config, Request request)", result.stdout)
            self.assertIn("String buildEncodedQuery", result.stdout)
            self.assertNotIn("String stringifyQueryValue", result.stdout)

    def test_two_entry_guards_do_not_trigger_guard_rule(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "TwoGuards.java", self.guard_source(2))

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_three_entry_guards_require_one_leading_comment(self):
        cases = {
            "missing": ("", 1),
            "present": ("// Separate missing inputs before selecting the usable value", 0),
        }
        for name, (comment, expected_code) in cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                path = self.write(
                    temporary, "ThreeGuards.java", self.guard_source(3, comment)
                )

                result = self.run_checker(path)

                self.assertEqual(expected_code, result.returncode, result)
                self.assertEqual(
                    expected_code, result.stdout.count("STYLE-GUARD-001"), result.stdout
                )

    def test_local_extraction_between_entry_guards_keeps_the_cluster(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "ExtractedGuards.java",
                self.guard_source(3, extraction_after=1),
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-GUARD-001", result.stdout)

    def test_javadoc_log_catch_and_nested_comments_do_not_replace_stage_intent(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary, "Selector.java", self.complex_method_source()
            )

            result = self.run_checker(path)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-INTENT-001"), result.stdout)
            self.assertNotIn("STYLE-CATCH-001", result.stdout)

    def test_top_level_stage_comment_satisfies_the_automatic_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "CommentedSelector.java",
                self.complex_method_source(
                    "// Compare candidates before advancing the selected value"
                ),
            )

            result = self.run_checker(path)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_line_range_requires_an_intersection_with_the_complex_method(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = textwrap.dedent(self.complex_method_source()).lstrip("\n")
            source = source.replace("class Selector {", "class Selector {\n    int marker;")
            path = self.write(temporary, "ScopedSelector.java", source).resolve()
            method_line = next(
                index for index, line in enumerate(source.splitlines(), 1)
                if "Object select(" in line
            )

            outside = self.run_checker("--line-range", f"{path}:2-2")
            inside = self.run_checker(
                "--line-range", f"{path}:{method_line}-{method_line}"
            )

            self.assertEqual(0, outside.returncode, outside.stdout + outside.stderr)
            self.assertNotIn("STYLE-INTENT-001", outside.stdout)
            self.assertEqual(1, inside.returncode, inside)
            self.assertIn("STYLE-INTENT-001", inside.stdout)


class LineRangeTests(CheckerTestCase):
    def test_line_range_only_reports_intersecting_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(
                temporary,
                "Ranges.java",
                "class Ranges {\n    // First.\n    int value;\n    // Second.\n}\n",
            ).resolve()

            result = self.run_checker("--line-range", f"{path}:2-2")

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-COMMENT-001"), result.stdout)
            self.assertIn(":2:", result.stdout)
            self.assertNotIn(":4:", result.stdout)

    def test_windows_drive_colon_is_parsed_from_final_range_suffix(self):
        checker = load_checker()

        path, start, end = checker.parse_line_range(r"C:\work\Example.java:12-18")

        self.assertEqual(r"C:\work\Example.java", path)
        self.assertEqual((12, 18), (start, end))

    def test_line_ranges_cannot_be_combined_with_positional_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Ranges.java", "class Ranges {}\n").resolve()

            result = self.run_checker("--line-range", f"{path}:1-1", path)

            self.assertEqual(2, result.returncode, result)
            self.assertIn("cannot be combined", result.stderr)

    def test_invalid_or_out_of_bounds_ranges_are_input_errors(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Ranges.java", "class Ranges {}\n").resolve()
            for value in (f"{path}:0-1", f"{path}:2-1", f"{path}:1-2", "not-a-range"):
                with self.subTest(value=value):
                    result = self.run_checker("--line-range", value)
                    self.assertEqual(2, result.returncode, result)


class ExclusionTests(CheckerTestCase):
    def test_full_path_excludes_directory_and_single_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            keep = self.write(root, "src/Keep.java", "class Keep {\n    // Keep.\n}\n")
            generated = self.write(
                root, "generated/Generated.java", "class Generated {\n    // Generated.\n}\n"
            )
            skipped = self.write(root, "src/Skip.java", "class Skip {\n    // Skip.\n}\n")

            result = self.run_checker(
                "--exclude",
                "generated",
                "--exclude",
                skipped,
                root,
                cwd=root,
            )

            self.assertEqual(1, result.returncode, result)
            self.assertIn(str(keep.resolve()), result.stdout)
            self.assertNotIn(str(generated.resolve()), result.stdout)
            self.assertNotIn(str(skipped.resolve()), result.stdout)
            self.assertEqual(1, result.stdout.count("STYLE-COMMENT-001"), result.stdout)

    def test_full_path_all_excluded_is_clean(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.write(root, "generated/Only.java", "class Only {\n    // Excluded.\n}\n")

            result = self.run_checker("--exclude", "generated", root, cwd=root)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("No Java files remain after exclusions", result.stdout)

    def test_exclude_glob_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.write(root, "Only.java", "class Only {}\n")

            result = self.run_checker("--exclude", "*.java", root, cwd=root)

            self.assertEqual(2, result.returncode, result)
            self.assertIn("exclude paths do not support globs", result.stderr)


class ChangedScopeTests(CheckerTestCase):
    def commit_all(self, repo, message):
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-m", message)

    def create_file_symlink_or_skip(self, link, target):
        try:
            link.symlink_to(target)
        except OSError as error:
            self.skipTest("file symlink creation denied by OS: %s" % error)

    def test_changed_mode_ignores_unchanged_historical_violation(self):
        temporary, repo = self.make_repo()
        with temporary:
            path = self.write(repo, "Historical.java", "class Historical {\n    // Historical.\n}\n")
            self.commit_all(repo, "base")
            path.write_text("class Historical {\n    // Historical.\n    int current;\n}\n", encoding="utf-8")

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("STYLE-COMMENT-001", result.stdout)

    def test_changed_mode_ignores_historical_complex_method_without_intent(self):
        temporary, repo = self.make_repo()
        with temporary:
            self.write(repo, "Legacy.java", """
                class Legacy {
                    int calculate(int value) {
                        int result = value;
                        for (int index = 0; index < 3; index++) {
                            if (result < index) {
                                result += index;
                            } else if (result > index) {
                                result -= index;
                            }
                        }
                        while (result < 10) {
                            result++;
                        }
                        if (result > 20) {
                            result = 20;
                        }
                        return result;
                    }
                }
            """)
            self.commit_all(repo, "base")
            self.write(repo, "Current.java", "class Current {\n    int value;\n}\n")

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("STYLE-INTENT-001", result.stdout)

    def test_changed_mode_detects_staged_unstaged_and_untracked_java(self):
        temporary, repo = self.make_repo()
        with temporary:
            staged = self.write(repo, "Staged.java", "class Staged {}\n")
            unstaged = self.write(repo, "Unstaged.java", "class Unstaged {}\n")
            self.commit_all(repo, "base")
            staged.write_text("class Staged {\n    // Staged.\n}\n", encoding="utf-8")
            self.git(repo, "add", "Staged.java")
            unstaged.write_text("class Unstaged {\n    // Unstaged.\n}\n", encoding="utf-8")
            self.write(repo, "Untracked.java", "class Untracked {\n    // Untracked.\n}\n")
            status_before = self.git(repo, "status", "--porcelain=v1")

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(status_before, self.git(repo, "status", "--porcelain=v1"))
            self.assertEqual(3, result.stdout.count("STYLE-COMMENT-001"), result.stdout)
            for name in ("Staged.java", "Unstaged.java", "Untracked.java"):
                self.assertIn(str((repo / name).resolve()), result.stdout)

            filtered = self.run_checker("--changed", "--repo", repo, staged)
            self.assertEqual(1, filtered.returncode, filtered)
            self.assertEqual(1, filtered.stdout.count("STYLE-COMMENT-001"), filtered.stdout)
            self.assertIn(str(staged.resolve()), filtered.stdout)
            self.assertNotIn(str(unstaged.resolve()), filtered.stdout)

    def test_changed_excludes_directory_after_inclusion(self):
        temporary, repo = self.make_repo()
        with temporary:
            keep = self.write(repo, "src/Keep.java", "class Keep {}\n")
            generated = self.write(repo, "generated/Tracked.java", "class Tracked {}\n")
            self.commit_all(repo, "base")
            keep.write_text("class Keep {\n    // Keep.\n}\n", encoding="utf-8")
            generated.write_text("class Tracked {\n    // Tracked.\n}\n", encoding="utf-8")
            untracked = self.write(
                repo, "generated/Untracked.java", "class Untracked {\n    // Untracked.\n}\n"
            )

            result = self.run_checker(
                "--changed",
                "--repo",
                repo,
                "--exclude",
                "generated",
                repo,
            )

            self.assertEqual(1, result.returncode, result)
            self.assertIn(str(keep.resolve()), result.stdout)
            self.assertNotIn(str(generated.resolve()), result.stdout)
            self.assertNotIn(str(untracked.resolve()), result.stdout)
            self.assertEqual(1, result.stdout.count("STYLE-COMMENT-001"), result.stdout)

    def test_changed_excludes_file_and_accepts_absent_path(self):
        temporary, repo = self.make_repo()
        with temporary:
            keep = self.write(repo, "Keep.java", "class Keep {}\n")
            skipped = self.write(repo, "Skip.java", "class Skip {}\n")
            self.commit_all(repo, "base")
            keep.write_text("class Keep {\n    // Keep.\n}\n", encoding="utf-8")
            skipped.write_text("class Skip {\n    // Skip.\n}\n", encoding="utf-8")

            result = self.run_checker(
                "--changed",
                "--repo",
                repo,
                "--exclude",
                skipped,
                "--exclude",
                "not-created",
            )

            self.assertEqual(1, result.returncode, result)
            self.assertIn(str(keep.resolve()), result.stdout)
            self.assertNotIn(str(skipped.resolve()), result.stdout)
            self.assertEqual(1, result.stdout.count("STYLE-COMMENT-001"), result.stdout)

    def test_changed_all_excluded_is_clean(self):
        temporary, repo = self.make_repo()
        with temporary:
            generated = self.write(repo, "generated/Only.java", "class Only {}\n")
            self.commit_all(repo, "base")
            generated.write_text(
                "class Only {\n    // Excluded.\n}\n", encoding="utf-8"
            )

            result = self.run_checker(
                "--changed", "--repo", repo, "--exclude", "generated"
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("remain after inclusions and exclusions", result.stdout)

    def test_changed_exclude_outside_repo_is_input_error(self):
        temporary, repo = self.make_repo()
        with temporary, tempfile.TemporaryDirectory() as outside:
            self.write(repo, "Base.java", "class Base {}\n")
            self.commit_all(repo, "base")

            result = self.run_checker(
                "--changed", "--repo", repo, "--exclude", Path(outside).resolve()
            )

            self.assertEqual(2, result.returncode, result)
            self.assertIn("exclude path is outside repository", result.stderr)

    def test_base_branch_and_commit_use_merge_base_against_worktree(self):
        temporary, repo = self.make_repo()
        with temporary:
            path = self.write(repo, "Base.java", "class Base {}\n")
            self.commit_all(repo, "base")
            base_commit = self.git(repo, "rev-parse", "HEAD")
            self.git(repo, "branch", "baseline", base_commit)
            path.write_text("class Base {\n    // Added.\n}\n", encoding="utf-8")
            self.commit_all(repo, "violation")

            current = self.run_checker("--changed", "--repo", repo)
            by_branch = self.run_checker("--changed", "--repo", repo, "--base", "baseline")
            by_commit = self.run_checker("--changed", "--repo", repo, "--base", base_commit)

            self.assertEqual(0, current.returncode, current.stdout + current.stderr)
            self.assertIn("No changed Java lines", current.stdout)
            self.assertEqual(1, by_branch.returncode, by_branch)
            self.assertIn("STYLE-COMMENT-001", by_branch.stdout)
            self.assertEqual(1, by_commit.returncode, by_commit)
            self.assertIn("STYLE-COMMENT-001", by_commit.stdout)

    def test_blank_line_only_change_intersects_full_method_boundary(self):
        temporary, repo = self.make_repo()
        with temporary:
            path = self.write(
                repo,
                "Methods.java",
                "class Methods {\n    void first() {\n    }\n\n    void second() {\n    }\n}\n",
            )
            self.commit_all(repo, "base")
            path.write_text(
                "class Methods {\n    void first() {\n    }\n\n\n    void second() {\n    }\n}\n",
                encoding="utf-8",
            )

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-METHOD-001", result.stdout)

    def test_deleting_only_method_separator_reports_method_spacing(self):
        temporary, repo = self.make_repo()
        with temporary:
            path = self.write(
                repo,
                "DeletedSeparator.java",
                "class DeletedSeparator {\n    void first() {\n    }\n\n    void second() {\n    }\n}\n",
            )
            self.commit_all(repo, "base")
            path.write_text(
                "class DeletedSeparator {\n    void first() {\n    }\n    void second() {\n    }\n}\n",
                encoding="utf-8",
            )

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(1, result.returncode, result)
            self.assertIn("STYLE-METHOD-001", result.stdout)

    def test_deletion_point_does_not_select_unrelated_comment_or_catch(self):
        temporary, repo = self.make_repo()
        with temporary:
            path = self.write(repo, "DeletedLine.java", """
                class DeletedLine {
                    // Historical.
                    int removed;
                    Object run() {
                        try {
                            return new Object();
                        } catch (RuntimeException exception) {
                            return null;
                        }
                    }
                }
            """)
            self.commit_all(repo, "base")
            path.write_text(path.read_text(encoding="utf-8").replace("    int removed;\n", ""), encoding="utf-8")

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertNotIn("STYLE-COMMENT-001", result.stdout)
            self.assertNotIn("STYLE-CATCH-001", result.stdout)

    def test_pure_rename_has_no_changed_lines_and_uses_destination_filter(self):
        temporary, repo = self.make_repo()
        with temporary:
            source = "class HistoricalRename {\n    // Historical.\n" + "".join(
                "    int value%d;\n" % index for index in range(10)
            ) + "}\n"
            self.write(repo, "OldName.java", source)
            self.commit_all(repo, "base")
            self.git(repo, "mv", "OldName.java", "NewName.java")
            destination = (repo / "NewName.java").resolve()

            result = self.run_checker("--changed", "--repo", repo, destination)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("No changed Java lines", result.stdout)
            self.assertNotIn("STYLE-COMMENT-001", result.stdout)

    def test_rename_plus_edit_scans_only_edited_destination_lines(self):
        temporary, repo = self.make_repo()
        with temporary:
            source = "class EditedRename {\n    // Historical.\n" + "".join(
                "    int value%d;\n" % index for index in range(10)
            ) + "    // Clean comment\n}\n"
            self.write(repo, "OldName.java", source)
            self.commit_all(repo, "base")
            self.git(repo, "mv", "OldName.java", "NewName.java")
            destination = repo / "NewName.java"
            destination.write_text(
                source.replace("// Clean comment", "// New violation."),
                encoding="utf-8",
            )

            result = self.run_checker("--changed", "--repo", repo, destination)

            self.assertEqual(1, result.returncode, result)
            self.assertEqual(1, result.stdout.count("STYLE-COMMENT-001"), result.stdout)
            self.assertIn("// New violation.", result.stdout)
            self.assertNotIn("// Historical.", result.stdout)

    def test_changed_filename_with_pathspec_metacharacters_is_literal(self):
        temporary, repo = self.make_repo()
        with temporary:
            literal = self.write(repo, "Flow[1].java", "class LiteralFlow {\n    int value;\n}\n")
            sibling = self.write(repo, "Flow1.java", "class SiblingFlow {\n    // Historical.\n}\n")
            self.commit_all(repo, "base")
            literal.write_text(
                "class LiteralFlow {\n    int value;\n    // New violation.\n}\n",
                encoding="utf-8",
            )

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(1, result.returncode, result)
            self.assertIn(str(literal.resolve()), result.stdout)
            self.assertIn("// New violation.", result.stdout)
            self.assertNotIn(str(sibling.resolve()), result.stdout)
            self.assertNotIn("// Historical.", result.stdout)

    def test_invalid_repo_ref_and_filter_path_exit_two(self):
        with tempfile.TemporaryDirectory() as non_repo:
            invalid_repo = self.run_checker("--changed", "--repo", non_repo)
            self.assertEqual(2, invalid_repo.returncode, invalid_repo)

        temporary, repo = self.make_repo()
        with temporary:
            self.write(repo, "Base.java", "class Base {}\n")
            self.commit_all(repo, "base")
            invalid_ref = self.run_checker("--changed", "--repo", repo, "--base", "missing-ref")
            invalid_path = self.run_checker("--changed", "--repo", repo, "missing-path")
            self.assertEqual(2, invalid_ref.returncode, invalid_ref)
            self.assertEqual(2, invalid_path.returncode, invalid_path)

    def test_no_java_changes_is_clean_with_clear_message(self):
        temporary, repo = self.make_repo()
        with temporary:
            self.write(repo, "README.txt", "base\n")
            self.commit_all(repo, "base")
            self.write(repo, "README.txt", "changed\n")

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("No changed Java lines", result.stdout)

    def test_changed_tracked_symlink_outside_repo_is_input_error(self):
        temporary, repo = self.make_repo()
        with temporary, tempfile.TemporaryDirectory() as outside_temporary:
            outside = Path(outside_temporary).resolve()
            first_target = self.write(outside, "First.java", "class First {}\n")
            second_target = self.write(outside, "Second.java", "class Second {}\n")
            link = repo / "Linked.java"
            self.create_file_symlink_or_skip(link, first_target)
            self.commit_all(repo, "base")
            link.unlink()
            self.create_file_symlink_or_skip(link, second_target)

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(2, result.returncode, result)
            self.assertIn("outside repository", result.stderr)

    def test_changed_untracked_symlink_outside_repo_is_input_error(self):
        temporary, repo = self.make_repo()
        with temporary, tempfile.TemporaryDirectory() as outside_temporary:
            outside = Path(outside_temporary).resolve()
            target = self.write(outside, "External.java", "class External {}\n")
            self.write(repo, "README.txt", "base\n")
            self.commit_all(repo, "base")
            self.create_file_symlink_or_skip(repo / "Linked.java", target)

            result = self.run_checker("--changed", "--repo", repo)

            self.assertEqual(2, result.returncode, result)
            self.assertIn("outside repository", result.stderr)


class CliValidationTests(CheckerTestCase):
    def test_no_scope_is_an_input_error(self):
        result = self.run_checker()

        self.assertEqual(2, result.returncode, result)

    def test_help_documents_line_range_combination_contract(self):
        result = self.run_checker("--help")

        self.assertEqual(0, result.returncode, result)
        self.assertIn("cannot be combined with positional paths", result.stdout)

    def test_line_range_cannot_be_combined_with_exclude(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = self.write(temporary, "Range.java", "class Range {}\n").resolve()

            result = self.run_checker(
                "--line-range", f"{path}:1-1", "--exclude", path
            )

            self.assertEqual(2, result.returncode, result)
            self.assertIn("cannot be combined with --exclude", result.stderr)

    def test_git_launch_failure_is_an_environment_error(self):
        checker = load_checker()
        stderr = io.StringIO()

        with patch.object(checker.subprocess, "run", side_effect=OSError("git unavailable")):
            with redirect_stderr(stderr):
                code = checker.main(["--changed", "--repo", str(Path.cwd())])

        self.assertEqual(2, code)
        self.assertIn("cannot launch Git", stderr.getvalue())

    def test_changed_diff_disables_textconv_and_external_diff(self):
        checker = load_checker()

        with patch.object(checker, "run_git", return_value="") as run_git_mock:
            checker.changed_hunk_ranges(
                Path("repo"), "baseline", [Path("Old.java"), Path("New.java")]
            )

        arguments = run_git_mock.call_args.args[1]
        self.assertIn("--no-textconv", arguments)
        self.assertIn("--no-ext-diff", arguments)

    def test_changed_diff_uses_literal_pathspecs_after_separator(self):
        checker = load_checker()

        with patch.object(checker, "run_git", return_value="") as run_git_mock:
            checker.changed_hunk_ranges(
                Path("repo"), "baseline", [Path("Flow[1].java")]
            )

        arguments = run_git_mock.call_args.args[1]
        separator = arguments.index("--")
        self.assertEqual([":(literal)Flow[1].java"], arguments[separator + 1:])

    def test_changed_name_status_disables_textconv_and_external_diff(self):
        checker = load_checker()

        with patch.object(checker, "resolve_baseline", return_value="baseline"):
            with patch.object(checker, "run_git", side_effect=[[], []]) as run_git_mock:
                checker.changed_line_scopes(Path("repo"), None, [])

        arguments = run_git_mock.call_args_list[0].args[1]
        self.assertIn("--no-textconv", arguments)
        self.assertIn("--no-ext-diff", arguments)


if __name__ == "__main__":
    unittest.main()
