#!/usr/bin/env python3
"""Validate the structure of PRD business understanding semantic cases."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SCHEMA_VERSION = 1
CASE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ALLOWED_MODES = {"dialogue", "direct-planning", "implementation"}
KNOWN_TRIGGERS = {
    "entry-choice",
    "collaborative-clarification",
    "evidence-boundaries",
    "source-provenance",
    "claim-classification",
    "evidence-conflict",
    "compatibility",
    "document-lineage",
    "contract-boundaries",
    "implementation-explanation",
    "completion-mapping",
    "scope-preservation",
    "existing-contract",
    "path-coverage",
    "concurrency-semantics",
    "domain-terminology",
}
REQUIRED_CASE_FIELDS = {
    "id",
    "title",
    "mode",
    "triggers",
    "fixture",
    "expected_decisions",
    "disallowed_decisions",
    "prompt",
}


def non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_string_list(value: Any, field: str, case_index: int) -> None:
    if not isinstance(value, list) or not value:
        raise ValueError(f"case_{case_index}_{field}_must_be_non_empty_list")
    if any(not non_empty_string(item) for item in value):
        raise ValueError(f"case_{case_index}_{field}_contains_invalid_value")
    if len(value) != len(set(value)):
        raise ValueError(f"case_{case_index}_{field}_contains_duplicate")


def validate_catalog(payload: Any) -> int:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "cases"}:
        raise ValueError("root_fields_invalid")
    schema_version = payload["schema_version"]
    if (
        type(schema_version) is not int
        or schema_version != SCHEMA_VERSION
    ):
        raise ValueError("schema_version_unsupported")

    cases = payload["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("cases_must_be_non_empty_list")

    case_ids: set[str] = set()
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict) or set(case) != REQUIRED_CASE_FIELDS:
            raise ValueError(f"case_{index}_fields_invalid")

        case_id = case["id"]
        if not non_empty_string(case_id) or not CASE_ID_PATTERN.fullmatch(case_id):
            raise ValueError(f"case_{index}_id_invalid")
        if case_id in case_ids:
            raise ValueError(f"case_{index}_id_duplicate")
        case_ids.add(case_id)

        for field in ("title", "fixture", "prompt"):
            if not non_empty_string(case[field]):
                raise ValueError(f"case_{index}_{field}_invalid")
        if not isinstance(case["mode"], str) or case["mode"] not in ALLOWED_MODES:
            raise ValueError(f"case_{index}_mode_invalid")

        validate_string_list(case["triggers"], "triggers", index)
        if any(trigger not in KNOWN_TRIGGERS for trigger in case["triggers"]):
            raise ValueError(f"case_{index}_trigger_unknown")
        validate_string_list(case["expected_decisions"], "expected_decisions", index)
        validate_string_list(case["disallowed_decisions"], "disallowed_decisions", index)

    return len(cases)


def main(arguments: list[str] | None = None) -> int:
    default_catalog = Path(__file__).resolve().parents[1] / "evals" / "semantic-cases.json"
    parser = argparse.ArgumentParser(
        description="Validate the structure of the semantic evaluation catalog."
    )
    parser.add_argument("catalog", nargs="?", type=Path, default=default_catalog)
    args = parser.parse_args(arguments)

    try:
        payload = json.loads(args.catalog.read_text(encoding="utf-8"))
        case_count = validate_catalog(payload)
    except OSError:
        print(json.dumps({"status": "ERROR", "reason": "catalog_unreadable"}))
        return 2
    except UnicodeError:
        print(json.dumps({"status": "INVALID", "reason": "invalid_utf8"}))
        return 1
    except json.JSONDecodeError:
        print(json.dumps({"status": "INVALID", "reason": "invalid_json"}))
        return 1
    except ValueError as error:
        print(json.dumps({"status": "INVALID", "reason": str(error)}))
        return 1

    print(json.dumps({"status": "VALID", "case_count": case_count}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
