#!/usr/bin/env python3
"""Compare a skill source and installation without modifying either directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


IGNORED_DIRECTORIES = {".git", "__pycache__"}
IGNORED_FILENAMES = {".DS_Store"}
IGNORED_SUFFIXES = {".pyc", ".pyd", ".pyo"}


class InstallationInputError(ValueError):
    """A source or installation directory cannot be compared safely."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


def is_reparse_point(entry_stat: os.stat_result) -> bool:
    flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(getattr(entry_stat, "st_file_attributes", 0) & flag)


def validate_root(path: Path, label: str) -> Path:
    try:
        entry_stat = path.lstat()
    except OSError as exception:
        raise InstallationInputError(f"{label}_unreadable") from exception
    if not stat.S_ISDIR(entry_stat.st_mode) or path.is_symlink() or is_reparse_point(entry_stat):
        raise InstallationInputError(f"{label}_not_plain_directory")
    if not (path / "SKILL.md").is_file():
        raise InstallationInputError(f"{label}_missing_skill_entrypoint")
    return path.resolve()


def should_ignore_file(path: Path) -> bool:
    return path.name in IGNORED_FILENAMES or path.suffix.lower() in IGNORED_SUFFIXES


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for current, directory_names, file_names in os.walk(root, followlinks=False):
        current_path = Path(current)
        kept_directories: list[str] = []
        for name in sorted(directory_names):
            if name in IGNORED_DIRECTORIES:
                continue
            directory = current_path / name
            try:
                entry_stat = directory.lstat()
            except OSError as exception:
                raise InstallationInputError("unreadable_directory") from exception
            if directory.is_symlink() or is_reparse_point(entry_stat):
                raise InstallationInputError("linked_directory_not_supported")
            kept_directories.append(name)
        directory_names[:] = kept_directories

        for name in sorted(file_names):
            path = current_path / name
            if should_ignore_file(path):
                continue
            try:
                entry_stat = path.lstat()
            except OSError as exception:
                raise InstallationInputError("unreadable_file") from exception
            if not stat.S_ISREG(entry_stat.st_mode) or path.is_symlink() or is_reparse_point(entry_stat):
                raise InstallationInputError("non_regular_file_not_supported")
            relative = path.relative_to(root).as_posix()
            try:
                files[relative] = hash_file(path)
            except OSError as exception:
                raise InstallationInputError("unreadable_file") from exception
    return files


def compare_installation(source: Path, target: Path) -> dict[str, object]:
    source_root = validate_root(source, "source")
    target_root = validate_root(target, "target")
    source_files = collect_files(source_root)
    target_files = collect_files(target_root)

    source_paths = set(source_files)
    target_paths = set(target_files)
    missing = sorted(source_paths - target_paths)
    extra = sorted(target_paths - source_paths)
    changed = sorted(
        path
        for path in source_paths & target_paths
        if source_files[path] != target_files[path]
    )
    status = "MATCH" if not (missing or extra or changed) else "DIFF"
    return {
        "status": status,
        "source_files": len(source_files),
        "target_files": len(target_files),
        "missing": missing,
        "extra": extra,
        "changed": changed,
    }


def print_payload(payload: dict[str, object]) -> None:
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify that an installed skill matches its source directory."
    )
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--target", required=True, type=Path)
    args = parser.parse_args(arguments)

    try:
        result = compare_installation(args.source, args.target)
    except InstallationInputError as exception:
        print_payload({"status": "ERROR", "reason": exception.reason})
        return 2

    print_payload(result)
    return 0 if result["status"] == "MATCH" else 1


if __name__ == "__main__":
    sys.exit(main())
