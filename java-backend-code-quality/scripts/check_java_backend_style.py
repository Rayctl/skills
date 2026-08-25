#!/usr/bin/env python3
"""Check deterministic Java backend style rules without modifying sources."""

import argparse
import bisect
import os
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path


CONTROL_WORDS = {
    "assert",
    "catch",
    "for",
    "if",
    "synchronized",
    "switch",
    "try",
    "while",
}

CLASS_PATTERN = re.compile(r"\b(class|interface|enum|record)\b")
IDENTIFIER_PATTERN = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*\s*$")
ANNOTATION_TOKEN_PATTERN = re.compile(r"@(?:[A-Za-z_$][A-Za-z0-9_$.]*)")
CATCH_PATTERN = re.compile(r"\bcatch\s*\(")
BEHAVIOR_PATTERN = re.compile(r"\b(?:return|break|continue)\b|\bthrow\s+new\b")
CONTROL_FLOW_PATTERN = re.compile(r"\b(?:if|for|while|do|switch|catch)\b")
IF_PATTERN = re.compile(r"\bif\b")
TERMINATION_PATTERN = re.compile(r"\b(?:throw|return|break|continue)\b")
LOCAL_EXTRACTION_PATTERN = re.compile(
    r"^(?:final\s+)?(?:var|[A-Za-z_$][A-Za-z0-9_$\.\[\]]*"
    r"(?:\s*<[^;=]+>)?(?:\s*\[\])?)\s+"
    r"[A-Za-z_$][A-Za-z0-9_$]*\s*=",
    re.DOTALL,
)
LINE_RANGE_PATTERN = re.compile(r"^(.*):([1-9][0-9]*)-([1-9][0-9]*)$")
DIFF_HUNK_PATTERN = re.compile(
    r"^@@ -[0-9]+(?:,[0-9]+)? \+([0-9]+)(?:,([0-9]+))? @@"
)

Finding = namedtuple(
    "Finding",
    ("line", "rule", "message", "content", "evidence_start", "evidence_end"),
)
Scope = namedtuple("Scope", ("kind", "start", "end"))


class InputError(ValueError):
    """Raised when a requested scan scope cannot be resolved safely."""


def line_starts(source):
    starts = [0]
    for index, character in enumerate(source):
        if character == "\n":
            starts.append(index + 1)
    return starts


def line_number(starts, index):
    return bisect.bisect_right(starts, index)


def source_line(source_lines, number):
    if 1 <= number <= len(source_lines):
        return source_lines[number - 1]
    return ""


def is_escaped(source, index):
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and source[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def text_block_end(source, start):
    cursor = start + 3
    while True:
        delimiter = source.find('"""', cursor)
        if delimiter == -1:
            return len(source)
        if not is_escaped(source, delimiter):
            return delimiter + 3
        cursor = delimiter + 1


def mask_source(source):
    """Return source with strings and comments blanked while preserving lines."""
    masked = list(source)
    comments = []
    length = len(source)
    index = 0

    def blank(start, end):
        for position in range(start, end):
            if source[position] != "\n":
                masked[position] = " "

    while index < length:
        if source.startswith("//", index):
            end = source.find("\n", index)
            if end == -1:
                end = length
            comments.append(("line", index, end))
            blank(index, end)
            index = end
            continue

        if source.startswith("/*", index):
            end = source.find("*/", index + 2)
            if end == -1:
                end = length
            else:
                end += 2
            comments.append(("block", index, end))
            blank(index, end)
            index = end
            continue

        if source.startswith('"""', index):
            end = text_block_end(source, index)
            blank(index, end)
            index = end
            continue

        if source[index] in ('"', "'"):
            quote = source[index]
            position = index + 1
            while position < length:
                if source[position] == "\\":
                    position += 2
                    continue
                if source[position] == quote:
                    position += 1
                    break
                position += 1
            blank(index, min(position, length))
            index = position
            continue

        index += 1

    return "".join(masked), comments


def matching_pairs(masked, opening, closing):
    stack = []
    pairs = {}
    for index, character in enumerate(masked):
        if character == opening:
            stack.append(index)
        elif character == closing and stack:
            pairs[stack.pop()] = index
    return pairs


def brace_depths(masked):
    depths = [0] * (len(masked) + 1)
    depth = 0
    for index, character in enumerate(masked):
        depths[index] = depth
        if character == "{":
            depth += 1
        elif character == "}":
            depth = max(0, depth - 1)
    depths[len(masked)] = depth
    return depths


def class_ranges(masked, brace_pairs):
    ranges = []
    for match in CLASS_PATTERN.finditer(masked):
        if match.start() > 0 and masked[match.start() - 1] == ".":
            continue
        opening = masked.find("{", match.end())
        semicolon = masked.find(";", match.end())
        if opening == -1 or (semicolon != -1 and semicolon < opening):
            continue
        closing = brace_pairs.get(opening)
        if closing is not None:
            ranges.append((opening, closing))
    return ranges


def annotation_ranges(masked, paren_pairs):
    ranges = []
    for match in ANNOTATION_TOKEN_PATTERN.finditer(masked):
        cursor = match.end()
        while cursor < len(masked) and masked[cursor].isspace():
            cursor += 1
        end = match.end()
        if cursor < len(masked) and masked[cursor] == "(":
            closing = paren_pairs.get(cursor)
            if closing is not None:
                end = closing + 1
        ranges.append((match.start(), end))
    return ranges


def mask_ranges(masked, ranges):
    result = list(masked)
    for start, end in ranges:
        for index in range(start, end):
            if result[index] != "\n":
                result[index] = " "
    return "".join(result)


def method_candidates(masked, paren_pairs, brace_pairs, depths, classes, starts):
    methods = []
    annotations = annotation_ranges(masked, paren_pairs)
    delimiter_source = mask_ranges(masked, annotations)
    for opening, closing in sorted(paren_pairs.items()):
        after = closing + 1
        while after < len(delimiter_source) and delimiter_source[after].isspace():
            after += 1

        body_opening = None
        if re.match(r"throws\b", delimiter_source[after:]):
            body_opening = delimiter_source.find("{", after)
            semicolon = delimiter_source.find(";", after)
            terminators = [
                position for position in (body_opening, semicolon) if position != -1
            ]
            if not terminators:
                continue
            terminator = min(terminators)
            if terminator != body_opening:
                body_opening = None
        elif re.match(r"default\b", delimiter_source[after:]):
            terminator = delimiter_source.find(";", after)
            if terminator == -1:
                continue
        elif after < len(delimiter_source) and delimiter_source[after] == "{":
            body_opening = after
            terminator = after
        elif after < len(delimiter_source) and delimiter_source[after] == ";":
            terminator = after
        else:
            continue

        before = masked[:opening]
        name_match = IDENTIFIER_PATTERN.search(before)
        if name_match is None:
            continue
        method_name = name_match.group(0).strip()
        if method_name in CONTROL_WORDS:
            continue

        declaration_start = max(
            delimiter_source.rfind(";", 0, opening),
            delimiter_source.rfind("{", 0, opening),
            delimiter_source.rfind("}", 0, opening),
        ) + 1
        declaration_prefix = delimiter_source[declaration_start:name_match.start()]
        if re.search(r"\bnew\b", declaration_prefix) or "->" in declaration_prefix:
            continue

        if body_opening is None:
            if (
                    not declaration_prefix.strip()
                    or "=" in declaration_prefix
                    or declaration_prefix.rstrip().endswith(".")
                    or re.search(r"\b(?:return|throw)\b", declaration_prefix)
            ):
                continue
            member_end = terminator
        else:
            member_end = brace_pairs.get(body_opening)
            if member_end is None:
                continue

        containing_classes = [
            (class_opening, class_closing)
            for class_opening, class_closing in classes
            if class_opening < terminator < class_closing
        ]
        if not containing_classes:
            continue

        member_start = declaration_start
        if body_opening is None:
            owner_range = max(containing_classes, key=lambda item: item[0])
            if (
                    not owner_range[0] < member_start <= member_end < owner_range[1]
                    or depths[terminator] != depths[owner_range[0]] + 1
            ):
                continue
        else:
            owner_depth = depths[terminator] - 1
            owners = [
                (owner_opening, owner_closing)
                for owner_opening, owner_closing in brace_pairs.items()
                if owner_opening < member_start <= terminator <= member_end < owner_closing
                and depths[owner_opening] == owner_depth
            ]
            if not owners:
                continue
            owner_range = max(owners, key=lambda item: item[0])
        declaration_token = member_start
        while declaration_token < len(masked) and masked[declaration_token].isspace():
            declaration_token += 1
        methods.append({
            "member_start": member_start,
            "member_end": member_end,
            "owner_range": owner_range,
            "declaration_line": line_number(starts, declaration_token),
            "body_opening": body_opening,
        })

    unique = {}
    for method in methods:
        unique[(method["member_start"], method["member_end"])] = method
    return sorted(unique.values(), key=lambda method: method["member_start"])


def comment_line_numbers(comments, starts):
    lines = set()
    for _, start, end in comments:
        first = line_number(starts, start)
        last = line_number(starts, max(start, end - 1))
        lines.update(range(first, last + 1))
    return lines


def annotation_line_spans(masked, paren_pairs, starts):
    spans_by_end_line = {}
    for match in ANNOTATION_TOKEN_PATTERN.finditer(masked):
        cursor = match.end()
        while cursor < len(masked) and masked[cursor].isspace():
            cursor += 1
        end = match.end() - 1
        if cursor < len(masked) and masked[cursor] == "(":
            end = paren_pairs.get(cursor, end)
        line_end = masked.find("\n", end + 1)
        if line_end == -1:
            line_end = len(masked)
        if masked[end + 1:line_end].strip():
            continue
        start_line = line_number(starts, match.start())
        end_line = line_number(starts, end)
        spans_by_end_line.setdefault(end_line, []).append(start_line)
    return spans_by_end_line


def leading_method_line(method_line, source_lines, comment_lines, annotation_spans):
    start = method_line
    cursor = method_line - 1
    while cursor >= 1:
        content = source_lines[cursor - 1].strip()
        if not content:
            break
        if cursor in comment_lines:
            start = cursor
            cursor -= 1
            continue
        if cursor in annotation_spans:
            start = min(annotation_spans[cursor])
            cursor = start - 1
            continue
        break
    return start


def check_comment_terminators(source, comments, starts, source_lines):
    findings = []
    for kind, start, end in comments:
        raw = source[start:end]
        if kind == "line":
            content = raw[2:]
            if content.rstrip().endswith((".", "。")):
                number = line_number(starts, start)
                findings.append(Finding(
                    number,
                    "STYLE-COMMENT-001",
                    "comment must not end with '.' or '。'",
                    source_line(source_lines, number),
                    number,
                    number,
                ))
            continue

        raw_lines = raw.splitlines()
        for offset, content in enumerate(raw_lines):
            if offset == 0:
                content = content.split("/*", 1)[1]
            if offset == len(raw_lines) - 1:
                content = content.rsplit("*/", 1)[0]
            content = re.sub(r"^\s*\*\s?", "", content)
            if content.rstrip().endswith((".", "。")):
                number = line_number(starts, start) + offset
                findings.append(Finding(
                    number,
                    "STYLE-COMMENT-001",
                    "comment must not end with '.' or '。'",
                    source_line(source_lines, number),
                    number,
                    number,
                ))
    return findings


def check_method_spacing(masked, comments, methods, starts, source_lines, paren_pairs):
    findings = []
    comment_lines = comment_line_numbers(comments, starts)
    annotation_spans = annotation_line_spans(masked, paren_pairs, starts)
    grouped = {}
    for method in methods:
        grouped.setdefault(method["owner_range"], []).append(method)

    for class_methods in grouped.values():
        class_methods.sort(key=lambda method: method["member_start"])
        for previous, current in zip(class_methods, class_methods[1:]):
            previous_line = line_number(starts, previous["member_end"])
            current_line = leading_method_line(
                current["declaration_line"],
                source_lines,
                comment_lines,
                annotation_spans,
            )
            if current_line < previous_line:
                continue
            gap_end = (
                starts[current_line - 1]
                if current_line > previous_line
                else current["member_start"]
            )
            member_gap = masked[previous["member_end"] + 1:gap_end]
            if member_gap.strip():
                continue
            blank_count = sum(
                not source_lines[line - 1].strip()
                for line in range(previous_line + 1, current_line)
            )
            if blank_count != 1:
                findings.append(Finding(
                    current_line,
                    "STYLE-METHOD-001",
                    "adjacent methods must have exactly one blank line",
                    source_line(source_lines, current_line),
                    previous_line,
                    current_line,
                ))
    return findings


def catch_ranges(masked, paren_pairs, brace_pairs):
    catches = []
    for match in CATCH_PATTERN.finditer(masked):
        opening_paren = masked.find("(", match.start(), match.end())
        closing_paren = paren_pairs.get(opening_paren)
        if closing_paren is None:
            continue
        body_opening = closing_paren + 1
        while body_opening < len(masked) and masked[body_opening].isspace():
            body_opening += 1
        if body_opening >= len(masked) or masked[body_opening] != "{":
            continue
        body_closing = brace_pairs.get(body_opening)
        if body_closing is not None:
            catches.append((match.start(), body_opening, body_closing))
    return catches


def nested_behavior_exclusions(masked, brace_pairs, classes, catches, body_opening, body_closing):
    exclusions = [
        item for item in classes
        if body_opening < item[0] < item[1] < body_closing
    ]
    exclusions.extend(
        (nested_opening, nested_closing)
        for _, nested_opening, nested_closing in catches
        if body_opening < nested_opening < nested_closing < body_closing
    )

    body = masked[body_opening + 1:body_closing]
    for match in re.finditer(r"->\s*\{", body):
        opening = body_opening + 1 + body.find("{", match.start(), match.end())
        closing = brace_pairs.get(opening)
        if closing is not None and closing < body_closing:
            exclusions.append((opening, closing))

    # Anonymous class bodies do not contain a class keyword but can contain returns.
    anonymous_pattern = re.compile(r"\bnew\b[^;{}]*?\([^;{}]*\)\s*\{")
    for match in anonymous_pattern.finditer(body):
        opening = body_opening + 1 + body.find("{", match.start(), match.end())
        closing = brace_pairs.get(opening)
        if closing is not None and closing < body_closing:
            exclusions.append((opening, closing))
    return exclusions


def inside_any(index, ranges):
    return any(start < index < end for start, end in ranges)


def standalone_top_level_comments(method, masked, comments, starts, depths):
    body_opening = method["body_opening"]
    if body_opening is None:
        return []
    body_depth = depths[body_opening] + 1
    result = []
    for _, start, end in comments:
        if not body_opening < start < end <= method["member_end"]:
            continue
        if depths[start] != body_depth:
            continue
        comment_line = line_number(starts, start)
        if masked[starts[comment_line - 1]:start].strip():
            continue
        result.append((start, end))
    return result


def effective_code_line_count(masked, body_opening, body_closing):
    return sum(
        bool(line.strip())
        for line in masked[body_opening + 1:body_closing].splitlines()
    )


def check_intent_comments(masked, comments, methods, starts, source_lines, depths):
    findings = []
    for method in methods:
        body_opening = method["body_opening"]
        if body_opening is None:
            continue
        body_closing = method["member_end"]
        if effective_code_line_count(masked, body_opening, body_closing) < 15:
            continue
        if len(CONTROL_FLOW_PATTERN.findall(masked, body_opening + 1, body_closing)) < 3:
            continue
        if standalone_top_level_comments(method, masked, comments, starts, depths):
            continue

        declaration_line = method["declaration_line"]
        findings.append(Finding(
            declaration_line,
            "STYLE-INTENT-001",
            "complex method requires at least one top-level stage intent comment",
            source_line(source_lines, declaration_line),
            declaration_line,
            line_number(starts, body_closing),
        ))
    return findings


def statement_semicolon(masked, start, limit, depths, expected_depth):
    cursor = masked.find(";", start, limit)
    while cursor != -1:
        if depths[cursor] == expected_depth:
            return cursor
        cursor = masked.find(";", cursor + 1, limit)
    return None


def terminating_guard_end(masked, if_start, method_end, paren_pairs,
                          brace_pairs, depths):
    opening_paren = if_start + 2
    while opening_paren < method_end and masked[opening_paren].isspace():
        opening_paren += 1
    if opening_paren >= method_end or masked[opening_paren] != "(":
        return None
    closing_paren = paren_pairs.get(opening_paren)
    if closing_paren is None or closing_paren >= method_end:
        return None

    statement_start = closing_paren + 1
    while statement_start < method_end and masked[statement_start].isspace():
        statement_start += 1
    if statement_start >= method_end:
        return None

    if masked[statement_start] == "{":
        statement_end = brace_pairs.get(statement_start)
        if statement_end is None or statement_end >= method_end:
            return None
        after = statement_end + 1
        while after < method_end and masked[after].isspace():
            after += 1
        if re.match(r"else\b", masked[after:method_end]):
            return None

        body_depth = depths[statement_start] + 1
        terminations = [
            match for match in TERMINATION_PATTERN.finditer(
                masked, statement_start + 1, statement_end
            )
            if depths[match.start()] == body_depth
        ]
        if not terminations:
            return None
        termination = terminations[-1]
        semicolon = statement_semicolon(
            masked, termination.start(), statement_end, depths, body_depth
        )
        if semicolon is None or masked[semicolon + 1:statement_end].strip():
            return None
        return statement_end + 1

    termination = TERMINATION_PATTERN.match(masked, statement_start, method_end)
    if termination is None:
        return None
    statement_depth = depths[statement_start]
    semicolon = statement_semicolon(
        masked, termination.start(), method_end, depths, statement_depth
    )
    return None if semicolon is None else semicolon + 1


def only_local_extractions(segment):
    remaining = segment.strip()
    while remaining:
        semicolon = remaining.find(";")
        if semicolon == -1:
            return False
        statement = remaining[:semicolon + 1].strip()
        if not LOCAL_EXTRACTION_PATTERN.match(statement):
            return False
        if any(character in statement for character in "{}"):
            return False
        remaining = remaining[semicolon + 1:].strip()
    return True


def entry_guard_cluster(method, masked, paren_pairs, brace_pairs, depths):
    body_opening = method["body_opening"]
    if body_opening is None:
        return None
    body_closing = method["member_end"]
    body_depth = depths[body_opening] + 1
    direct_ifs = [
        match.start() for match in IF_PATTERN.finditer(
            masked, body_opening + 1, body_closing
        )
        if depths[match.start()] == body_depth
    ]

    cursor = body_opening + 1
    guards = []
    for if_start in direct_ifs:
        if if_start < cursor:
            continue
        if not only_local_extractions(masked[cursor:if_start]):
            break
        guard_end = terminating_guard_end(
            masked, if_start, body_closing, paren_pairs, brace_pairs, depths
        )
        if guard_end is None:
            break
        guards.append((if_start, guard_end))
        cursor = guard_end
    return guards if len(guards) >= 3 else None


def check_guard_comments(masked, comments, methods, starts, source_lines,
                         paren_pairs, brace_pairs, depths):
    findings = []
    for method in methods:
        guards = entry_guard_cluster(
            method, masked, paren_pairs, brace_pairs, depths
        )
        if guards is None:
            continue
        first_guard = guards[0][0]
        has_leading_comment = any(
            end <= first_guard
            for start, end in standalone_top_level_comments(
                method, masked, comments, starts, depths
            )
            if start < first_guard
        )
        if has_leading_comment:
            continue

        guard_line = line_number(starts, first_guard)
        findings.append(Finding(
            guard_line,
            "STYLE-GUARD-001",
            "entry guard cluster requires one leading intent comment",
            source_line(source_lines, guard_line),
            method["declaration_line"],
            line_number(starts, method["member_end"]),
        ))
    return findings


def check_catch_comments(masked, comments, starts, source_lines, paren_pairs,
                         brace_pairs, classes):
    findings = []
    catches = catch_ranges(masked, paren_pairs, brace_pairs)
    for _, body_opening, body_closing in catches:
        exclusions = nested_behavior_exclusions(
            masked, brace_pairs, classes, catches, body_opening, body_closing
        )
        behaviors = (
            match for match in BEHAVIOR_PATTERN.finditer(
                masked, body_opening + 1, body_closing
            )
            if not inside_any(match.start(), exclusions)
        )
        for behavior in behaviors:
            has_local_comment = any(
                body_opening < start and end <= behavior.start()
                and not inside_any(start, exclusions)
                and not masked[end:behavior.start()].strip()
                for _, start, end in comments
            )
            if has_local_comment:
                continue

            behavior_line = line_number(starts, behavior.start())
            cursor = behavior.start() - 1
            while cursor > body_opening and masked[cursor].isspace():
                cursor -= 1
            evidence_start = line_number(starts, max(cursor, body_opening))
            findings.append(Finding(
                behavior_line,
                "STYLE-CATCH-001",
                "behavior-changing catch path requires a directly preceding catch-local intent comment",
                source_line(source_lines, behavior_line),
                evidence_start,
                behavior_line,
            ))
    return findings


def analyze_source(source):
    starts = line_starts(source)
    source_lines = source.splitlines()
    masked, comments = mask_source(source)
    brace_pairs = matching_pairs(masked, "{", "}")
    paren_pairs = matching_pairs(masked, "(", ")")
    depths = brace_depths(masked)
    classes = class_ranges(masked, brace_pairs)
    methods = method_candidates(masked, paren_pairs, brace_pairs, depths, classes, starts)

    findings = []
    findings.extend(check_comment_terminators(source, comments, starts, source_lines))
    findings.extend(check_method_spacing(
        masked, comments, methods, starts, source_lines, paren_pairs
    ))
    findings.extend(check_catch_comments(
        masked, comments, starts, source_lines, paren_pairs, brace_pairs, classes
    ))
    findings.extend(check_guard_comments(
        masked, comments, methods, starts, source_lines,
        paren_pairs, brace_pairs, depths
    ))
    findings.extend(check_intent_comments(
        masked, comments, methods, starts, source_lines, depths
    ))
    return sorted(findings, key=lambda finding: (finding.line, finding.rule))


def read_java_source(path):
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        raise InputError("cannot read Java source %s: %s" % (path, error)) from error


def check_file(path):
    return analyze_source(read_java_source(path))


def java_files(inputs):
    files = set()
    for raw_path in inputs:
        path = Path(raw_path).resolve()
        if not path.exists():
            raise InputError("path does not exist: %s" % path)
        if path.is_file():
            if path.suffix.lower() == ".java":
                files.add(path)
            continue
        files.update(item.resolve() for item in path.rglob("*.java") if item.is_file())
    return sorted(files, key=lambda path: os.path.normcase(str(path)))


def parse_line_range(value):
    """Parse the final :start-end suffix so a Windows drive colon stays in the path."""
    match = LINE_RANGE_PATTERN.match(value)
    if match is None or not match.group(1):
        raise InputError("invalid line range: %s" % value)
    start = int(match.group(2))
    end = int(match.group(3))
    if start > end:
        raise InputError("line range start must not exceed end: %s" % value)
    return match.group(1), start, end


def merge_ranges(ranges):
    merged = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def line_scopes(ranges):
    return [Scope("lines", start, end) for start, end in merge_ranges(ranges)]


def merge_scopes(scopes):
    lines = line_scopes(
        (scope.start, scope.end) for scope in scopes if scope.kind == "lines"
    )
    boundaries = sorted({
        scope.start for scope in scopes if scope.kind == "boundary"
    })
    return lines + [Scope("boundary", point, point) for point in boundaries]


def exact_line_scopes(values):
    scopes = {}
    line_counts = {}
    for value in values:
        raw_path, start, end = parse_line_range(value)
        path = Path(raw_path).resolve()
        if not path.exists() or not path.is_file():
            raise InputError("line-range path is not a file: %s" % path)
        if path.suffix.lower() != ".java":
            raise InputError("line-range path is not a Java file: %s" % path)
        if path not in line_counts:
            line_counts[path] = len(read_java_source(path).splitlines())
        if end > line_counts[path]:
            raise InputError(
                "line range %d-%d exceeds %s (%d line(s))"
                % (start, end, path, line_counts[path])
            )
        scopes.setdefault(path, []).append((start, end))
    return {
        path: line_scopes(ranges)
        for path, ranges in sorted(
            scopes.items(), key=lambda item: os.path.normcase(str(item[0]))
        )
    }


def run_git(repo, arguments, description, nul_output=False):
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as error:
        raise InputError("cannot launch Git: %s" % error) from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise InputError("%s%s" % (description, ": " + detail if detail else ""))
    if nul_output:
        return [
            item.decode("utf-8", errors="surrogateescape")
            for item in result.stdout.split(b"\0")
            if item
        ]
    return result.stdout.decode("utf-8", errors="replace").strip()


def resolve_repo(raw_repo):
    candidate = Path(raw_repo).resolve()
    if not candidate.exists() or not candidate.is_dir():
        raise InputError("repository path is not a directory: %s" % candidate)
    top_level = run_git(
        candidate,
        ["rev-parse", "--show-toplevel"],
        "path is not a Git worktree: %s" % candidate,
    )
    repo = Path(top_level).resolve()
    inside = run_git(repo, ["rev-parse", "--is-inside-work-tree"], "invalid Git worktree")
    if inside != "true":
        raise InputError("path is not a Git worktree: %s" % candidate)
    return repo


def resolve_baseline(repo, base):
    head = run_git(
        repo,
        ["rev-parse", "--verify", "HEAD^{commit}"],
        "repository HEAD does not resolve to a commit",
    )
    if base is None:
        return head
    base_commit = run_git(
        repo,
        ["rev-parse", "--verify", "%s^{commit}" % base],
        "base ref does not resolve to a commit: %s" % base,
    )
    return run_git(
        repo,
        ["merge-base", base_commit, head],
        "cannot find merge-base between %s and HEAD" % base,
    )


def path_is_within(path, parent):
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def resolve_exclusions(raw_paths, base, required_parent=None):
    exclusions = []
    for raw_path in raw_paths:
        if "*" in str(raw_path) or "?" in str(raw_path):
            raise InputError("exclude paths do not support globs: %s" % raw_path)
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = base / candidate
        candidate = candidate.resolve()
        if required_parent is not None and not path_is_within(candidate, required_parent):
            raise InputError("exclude path is outside repository: %s" % candidate)
        exclusions.append(candidate)
    return exclusions


def is_excluded(path, exclusions):
    return any(path == item or path_is_within(path, item) for item in exclusions)


def resolve_changed_filters(repo, raw_paths):
    filters = []
    for raw_path in raw_paths:
        candidate = Path(raw_path)
        if not candidate.is_absolute():
            candidate = repo / candidate
        candidate = candidate.resolve()
        if not candidate.exists():
            raise InputError("filter path does not exist: %s" % candidate)
        if not path_is_within(candidate, repo):
            raise InputError("filter path is outside repository: %s" % candidate)
        filters.append(candidate)
    return filters


def matches_filters(path, filters):
    if not filters:
        return True
    return any(path == item or (item.is_dir() and path_is_within(path, item)) for item in filters)


def resolve_changed_path(repo, name):
    requested_path = repo / name
    resolved_path = requested_path.resolve()
    if not path_is_within(resolved_path, repo):
        raise InputError(
            "changed path resolves outside repository: %s" % requested_path
        )
    return resolved_path


def changed_hunk_ranges(repo, baseline, relative_paths):
    pathspecs = [":(literal)" + path.as_posix() for path in relative_paths]
    diff = run_git(
        repo,
        [
            "diff",
            "--unified=0",
            "--no-color",
            "--no-ext-diff",
            "--no-textconv",
            "--find-renames",
            baseline,
            "--",
            *pathspecs,
        ],
        "cannot inspect changes for %s" % ", ".join(pathspecs),
    )
    scopes = []
    for line in diff.splitlines():
        match = DIFF_HUNK_PATTERN.match(line)
        if match is None:
            continue
        start = int(match.group(1))
        count = int(match.group(2) or "1")
        if count > 0:
            scopes.append(Scope("lines", start, start + count - 1))
        else:
            scopes.append(Scope("boundary", start, start))
    return merge_scopes(scopes)


def changed_path_pairs(tokens):
    pairs = []
    index = 0
    while index < len(tokens):
        status = tokens[index]
        index += 1
        if not status:
            raise InputError("Git returned an empty change status")
        if status[0] in {"R", "C"}:
            if index + 1 >= len(tokens):
                raise InputError("Git returned an incomplete rename/copy record")
            old_name = tokens[index]
            new_name = tokens[index + 1]
            index += 2
        else:
            if index >= len(tokens):
                raise InputError("Git returned an incomplete change record")
            old_name = tokens[index]
            new_name = tokens[index]
            index += 1
        pairs.append((status, old_name, new_name))
    return pairs


def changed_line_scopes(repo, base, raw_paths, exclusions=None):
    baseline = resolve_baseline(repo, base)
    filters = resolve_changed_filters(repo, raw_paths)
    exclusions = exclusions or []
    tracked_status = run_git(
        repo,
        [
            "diff",
            "--name-status",
            "-z",
            "--find-renames",
            "--no-ext-diff",
            "--no-textconv",
            "--diff-filter=ACMRTUXB",
            baseline,
            "--",
        ],
        "cannot list tracked worktree changes",
        nul_output=True,
    )
    untracked_names = run_git(
        repo,
        ["ls-files", "--others", "--exclude-standard", "-z"],
        "cannot list untracked files",
        nul_output=True,
    )

    scopes = {}
    for _, old_name, new_name in changed_path_pairs(tracked_status):
        path = resolve_changed_path(repo, new_name)
        if (
            path.suffix.lower() != ".java"
            or not path.is_file()
            or not matches_filters(path, filters)
            or is_excluded(path, exclusions)
        ):
            continue
        relative_paths = []
        for name in (old_name, new_name):
            relative_path = Path(name)
            if relative_path not in relative_paths:
                relative_paths.append(relative_path)
        changed_scopes = changed_hunk_ranges(repo, baseline, relative_paths)
        if changed_scopes:
            scopes[path] = changed_scopes

    for name in untracked_names:
        path = resolve_changed_path(repo, name)
        if (
            path.suffix.lower() != ".java"
            or not path.is_file()
            or not matches_filters(path, filters)
            or is_excluded(path, exclusions)
        ):
            continue
        line_count = len(read_java_source(path).splitlines())
        if line_count:
            scopes[path] = [Scope("lines", 1, line_count)]

    return {
        path: scopes[path]
        for path in sorted(scopes, key=lambda item: os.path.normcase(str(item)))
    }


def finding_intersects(finding, scopes):
    for scope in scopes:
        if scope.kind == "lines":
            if finding.evidence_start <= scope.end and scope.start <= finding.evidence_end:
                return True
        elif finding.evidence_start <= scope.start < finding.evidence_end:
            return True
    return False


def scan(scopes):
    findings = []
    for path, ranges in scopes.items():
        for finding in check_file(path):
            if ranges is None or finding_intersects(finding, ranges):
                findings.append((path, finding))
    return sorted(
        findings,
        key=lambda item: (
            os.path.normcase(str(item[0])), item[1].line, item[1].rule
        ),
    )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Check deterministic Java backend style rules in current sources.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Scope contract: --line-range is an exact-scope mode and cannot be "
            "combined with positional paths, --changed, or --exclude. In --changed mode, "
            "positional paths filter changed Java files; otherwise positional "
            "paths are scanned as complete files or directories. Repeatable --exclude "
            "paths remove files after inclusion and do not accept globs."
        ),
    )
    parser.add_argument(
        "--changed",
        action="store_true",
        help="inspect added/modified current-source lines relative to HEAD or --base",
    )
    parser.add_argument(
        "--base",
        help="base ref for --changed; its merge-base with HEAD is used",
    )
    parser.add_argument(
        "--repo",
        help="Git worktree for --changed (default: current directory)",
    )
    parser.add_argument(
        "--line-range",
        action="append",
        default=[],
        metavar="FILE:START-END",
        help=(
            "inspect an exact inclusive current-source range; repeatable and "
            "parsed from the final :digits-digits suffix"
        ),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "exclude a file or directory tree after inclusion; repeatable, relative to "
            "--repo in --changed mode and otherwise to the current directory"
        ),
    )
    parser.add_argument(
        "paths",
        nargs="*",
        help="Java files/directories, or path filters when --changed is used",
    )
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.changed and args.line_range:
        parser.error("--changed and --line-range cannot be combined")
    if args.line_range and args.paths:
        parser.error("--line-range cannot be combined with positional paths")
    if args.line_range and args.exclude:
        parser.error("--line-range cannot be combined with --exclude")
    if not args.changed and args.base is not None:
        parser.error("--base requires --changed")
    if not args.changed and args.repo is not None:
        parser.error("--repo requires --changed")
    if not args.changed and not args.line_range and not args.paths:
        parser.error("provide paths, --changed, or at least one --line-range")

    try:
        if args.changed:
            repo = resolve_repo(args.repo or ".")
            exclusions = resolve_exclusions(args.exclude, repo, repo)
            scopes = changed_line_scopes(repo, args.base, args.paths, exclusions)
            if not scopes:
                if args.exclude:
                    print("No changed Java lines remain after inclusions and exclusions")
                else:
                    print("No changed Java lines found")
                return 0
        elif args.line_range:
            scopes = exact_line_scopes(args.line_range)
        else:
            requested_files = java_files(args.paths)
            if not requested_files:
                raise InputError("no Java files found in requested paths")
            exclusions = resolve_exclusions(args.exclude, Path.cwd().resolve())
            files = [path for path in requested_files if not is_excluded(path, exclusions)]
            if not files:
                print("No Java files remain after exclusions")
                return 0
            scopes = {path: None for path in files}

        findings = scan(scopes)
    except InputError as error:
        print("ERROR: %s" % error, file=sys.stderr)
        return 2

    for path, finding in findings:
        print(
            "%s:%d: %s: %s | %s"
            % (
                path.resolve(),
                finding.line,
                finding.rule,
                finding.message,
                finding.content,
            )
        )

    if findings:
        print("Found %d style violation(s)" % len(findings), file=sys.stderr)
        return 1
    print("No deterministic style violations found in %d Java file(s)" % len(scopes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
