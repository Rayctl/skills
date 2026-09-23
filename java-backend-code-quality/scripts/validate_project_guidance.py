#!/usr/bin/env python3
"""Validate local project-guidance metadata without changing the repository."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


SECTIONS = {
    "Logging",
    "Dependencies And Utilities",
    "Remote Calls",
    "Exception Handling",
    "Formatting And Naming",
    "Build And Verification",
}
SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


def result(status: str, reason: str | None = None) -> int:
    payload: dict[str, Any] = {"status": status}
    if reason:
        payload["reason"] = reason
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))
    return 0 if status in {"VALID", "VALID_LEGACY", "UNVERIFIED"} else 1


def parse_frontmatter(text: str) -> dict[str, str] | None:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return None

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line or line.startswith((" ", "\t")):
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"\'')
    return metadata


def validate(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return result("ERROR", "guidance_unreadable")
    except UnicodeError:
        return result("ERROR", "invalid_utf8")

    metadata = parse_frontmatter(text)
    if metadata is None:
        return result("UNVERIFIED", "missing_frontmatter")

    raw_version = metadata.get("schema_version")
    if raw_version is None:
        return result("UNVERIFIED", "missing_schema_version")
    try:
        version = int(raw_version)
    except ValueError:
        return result("UNVERIFIED", "invalid_schema_version")

    if version == 1:
        if not SHA_PATTERN.fullmatch(metadata.get("verified_commit", "")):
            return result("UNVERIFIED", "legacy_commit_missing_or_invalid")
        return result("VALID_LEGACY")

    if version != 2:
        return result("UNVERIFIED", "unsupported_schema_version")

    section_lines = text.splitlines()
    in_commits = False
    commits: dict[str, str] = {}
    for line in section_lines:
        if line.strip() == "verified_commits:":
            in_commits = True
            continue
        if in_commits and line and not line[0].isspace():
            break
        if in_commits and ":" in line:
            key, value = line.strip().split(":", 1)
            commits[key.strip()] = value.strip().strip('"\'<>')

    if not commits:
        return result("UNVERIFIED", "section_commits_missing")
    unknown = set(commits) - SECTIONS
    if unknown:
        return result("INVALID", "unknown_guidance_section")
    if any(not SHA_PATTERN.fullmatch(value) for value in commits.values()):
        return result("UNVERIFIED", "section_commit_missing_or_invalid")
    return result("VALID")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate local project-guidance metadata")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(arguments)
    return validate(args.path)


if __name__ == "__main__":
    sys.exit(main())
