#!/usr/bin/env python3
"""Validate the structure of Java backend semantic evaluation cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_MODES = {"implementation", "review"}
KNOWN_TRIGGERS = {
    "checker",
    "comments-and-javadoc",
    "contracts-and-lifecycles",
    "control-flow",
    "evidence-and-verification",
    "exception-communication",
    "method-design",
    "naming",
    "project-guidance",
    "remote-calls",
    "structure-choice",
}
REQUIRED_CASE_FIELDS = {
    "id",
    "title",
    "mode",
    "triggers",
    "fixture",
    "expected_decisions",
    "disallowed_decisions",
}
OPTIONAL_CASE_FIELDS = {"assertions", "input_files", "prompt"}


class EvaluationValidationError(ValueError):
    """The evaluation catalog does not satisfy its structural contract."""

    def __init__(self, reason: str, *, case_index: int | None = None) -> None:
        self.reason = reason
        self.case_index = case_index
        super().__init__(reason)


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_string_list(
    value: Any,
    field: str,
    *,
    case_index: int,
) -> None:
    if not isinstance(value, list) or not value:
        raise EvaluationValidationError(
            f"{field}_must_be_non_empty_list", case_index=case_index
        )
    if any(not non_empty_string(item) for item in value):
        raise EvaluationValidationError(
            f"{field}_contains_invalid_value", case_index=case_index
        )
    if len(value) != len(set(value)):
        raise EvaluationValidationError(
            f"{field}_contains_duplicate", case_index=case_index
        )


def validate_catalog(payload: Any) -> int:
    if not isinstance(payload, dict):
        raise EvaluationValidationError("root_must_be_object")
    if set(payload) != {"schema_version", "cases"}:
        raise EvaluationValidationError("unexpected_root_fields")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise EvaluationValidationError("unsupported_schema_version")

    cases = payload["cases"]
    if not isinstance(cases, list) or not cases:
        raise EvaluationValidationError("cases_must_be_non_empty_list")

    case_ids: set[str] = set()
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise EvaluationValidationError("case_must_be_object", case_index=index)
        if not REQUIRED_CASE_FIELDS.issubset(case) or set(case) - REQUIRED_CASE_FIELDS - OPTIONAL_CASE_FIELDS:
            raise EvaluationValidationError(
                "case_fields_do_not_match_schema", case_index=index
            )

        case_id = case["id"]
        if not non_empty_string(case_id) or not CASE_ID_PATTERN.fullmatch(case_id):
            raise EvaluationValidationError("invalid_case_id", case_index=index)
        if case_id in case_ids:
            raise EvaluationValidationError("duplicate_case_id", case_index=index)
        case_ids.add(case_id)

        if not non_empty_string(case["title"]):
            raise EvaluationValidationError("invalid_title", case_index=index)
        if not isinstance(case["mode"], str) or case["mode"] not in ALLOWED_MODES:
            raise EvaluationValidationError("invalid_mode", case_index=index)
        if not non_empty_string(case["fixture"]):
            raise EvaluationValidationError("invalid_fixture", case_index=index)

        validate_string_list(case["triggers"], "triggers", case_index=index)
        if any(trigger not in KNOWN_TRIGGERS for trigger in case["triggers"]):
            raise EvaluationValidationError("unknown_trigger", case_index=index)
        validate_string_list(
            case["expected_decisions"], "expected_decisions", case_index=index
        )
        validate_string_list(
            case["disallowed_decisions"], "disallowed_decisions", case_index=index
        )
        for optional_field in OPTIONAL_CASE_FIELDS:
            if optional_field in case:
                if optional_field == "prompt":
                    if not non_empty_string(case[optional_field]):
                        raise EvaluationValidationError(
                            "prompt_must_be_non_empty_string", case_index=index
                        )
                else:
                    validate_string_list(case[optional_field], optional_field, case_index=index)

    return len(cases)


def print_payload(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def main(arguments: list[str] | None = None) -> int:
    default_catalog = Path(__file__).resolve().parents[1] / "evals" / "semantic-cases.json"
    parser = argparse.ArgumentParser(
        description="Validate the semantic evaluation catalog structure."
    )
    parser.add_argument("catalog", nargs="?", type=Path, default=default_catalog)
    args = parser.parse_args(arguments)

    try:
        text = args.catalog.read_text(encoding="utf-8")
    except OSError:
        print_payload({"status": "ERROR", "reason": "catalog_unreadable"})
        return 2
    except UnicodeError:
        print_payload({"status": "INVALID", "reason": "invalid_utf8"})
        return 1

    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        print_payload({"status": "INVALID", "reason": "invalid_json"})
        return 1

    try:
        case_count = validate_catalog(payload)
    except EvaluationValidationError as exception:
        result: dict[str, object] = {
            "status": "INVALID",
            "reason": exception.reason,
        }
        if exception.case_index is not None:
            result["case_index"] = exception.case_index
        print_payload(result)
        return 1

    print_payload({"status": "VALID", "case_count": case_count})
    return 0


if __name__ == "__main__":
    sys.exit(main())
