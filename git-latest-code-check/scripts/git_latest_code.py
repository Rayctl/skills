#!/usr/bin/env python3
"""Check a Git worktree against its remote branch and fast-forward when approved."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


EXIT_OK = 0
EXIT_ACTION_REQUIRED = 1
EXIT_ERROR = 2
DEFAULT_TIMEOUT_SECONDS = 30


class InputError(Exception):
    """Raised when the command cannot identify a valid repository or target."""


class GitError(Exception):
    """Raised when Git or the selected remote cannot complete a required read."""


class ActionRequired(Exception):
    """Raised when repository state requires a user decision."""

    def __init__(
        self,
        status: str,
        detail: str,
        state: RepositoryState | None = None,
    ) -> None:
        super().__init__(detail)
        self.status = status
        self.detail = detail
        self.state = state


@dataclass(frozen=True)
class GitResult:
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class RemoteTarget:
    remote: str
    branch: str
    source_ref: str
    tracking_ref: str

    @property
    def display_name(self) -> str:
        return f"{self.remote}/{self.branch}"


@dataclass(frozen=True)
class RepositoryState:
    root: Path
    branch: str
    local_sha: str
    dirty_count: int


def last_output_line(result: GitResult) -> str:
    output = result.stderr or result.stdout
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def run_git(
    repository: Path,
    arguments: Sequence[str],
    *,
    check: bool = True,
) -> GitResult:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=repository,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=DEFAULT_TIMEOUT_SECONDS,
            env=environment,
            shell=False,
        )
    except FileNotFoundError as error:
        raise GitError("git executable was not found") from error
    except subprocess.TimeoutExpired as error:
        raise GitError(
            f"git command timed out after {DEFAULT_TIMEOUT_SECONDS} seconds"
        ) from error

    result = GitResult(
        returncode=completed.returncode,
        stdout=completed.stdout.strip(),
        stderr=completed.stderr.strip(),
    )
    if check and result.returncode != 0:
        detail = last_output_line(result) or "git command failed"
        raise GitError(f"git {' '.join(arguments[:2])} failed: {detail}")
    return result


def find_repository(raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser().resolve()
    if not candidate.is_dir():
        raise InputError(f"repository path is not a directory: {candidate}")
    result = run_git(candidate, ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0 or not result.stdout:
        raise InputError(f"path is not a Git worktree: {candidate}")
    return Path(result.stdout).resolve()


def read_repository_state(repository: Path) -> RepositoryState:
    local_sha = run_git(repository, ["rev-parse", "HEAD"]).stdout
    status = run_git(
        repository,
        ["status", "--porcelain=v1", "--untracked-files=all"],
    ).stdout
    dirty_count = len(status.splitlines()) if status else 0
    branch_result = run_git(
        repository,
        ["symbolic-ref", "--quiet", "--short", "HEAD"],
        check=False,
    )
    if branch_result.returncode != 0 or not branch_result.stdout:
        detached_state = RepositoryState(
            root=repository,
            branch="(detached)",
            local_sha=local_sha,
            dirty_count=dirty_count,
        )
        raise ActionRequired(
            "DETACHED",
            "HEAD is not attached to a local branch",
            detached_state,
        )
    return RepositoryState(
        root=repository,
        branch=branch_result.stdout,
        local_sha=local_sha,
        dirty_count=dirty_count,
    )


def read_config(repository: Path, key: str) -> str | None:
    result = run_git(repository, ["config", "--get", key], check=False)
    if result.returncode == 0 and result.stdout:
        return result.stdout
    return None


def validate_remote(repository: Path, remote: str) -> None:
    remote_list = run_git(repository, ["remote"]).stdout.splitlines()
    if remote not in remote_list:
        raise InputError(f"remote does not exist: {remote}")


def validate_branch(repository: Path, branch: str) -> None:
    result = run_git(
        repository,
        ["check-ref-format", "--branch", branch],
        check=False,
    )
    if result.returncode != 0:
        raise InputError(f"invalid remote branch name: {branch}")


def resolve_target(
    state: RepositoryState,
    explicit_remote: str | None,
    explicit_branch: str | None,
) -> RemoteTarget:
    if explicit_remote is not None and explicit_branch is not None:
        remote = explicit_remote
        branch = explicit_branch
        validate_remote(state.root, remote)
        validate_branch(state.root, branch)
        tracking_ref = f"refs/remotes/{remote}/{branch}"
    else:
        remote = read_config(state.root, f"branch.{state.branch}.remote")
        merge_ref = read_config(state.root, f"branch.{state.branch}.merge")
        if remote is None or merge_ref is None:
            raise ActionRequired(
                "NO_UPSTREAM",
                "current branch has no upstream; provide --remote and --branch",
            )
        if remote == ".":
            raise ActionRequired(
                "NO_UPSTREAM",
                "current branch tracks a local branch instead of a remote branch",
            )
        prefix = "refs/heads/"
        if not merge_ref.startswith(prefix) or len(merge_ref) == len(prefix):
            raise ActionRequired(
                "NO_UPSTREAM",
                f"unsupported upstream merge ref: {merge_ref}",
            )
        branch = merge_ref[len(prefix) :]
        validate_remote(state.root, remote)
        validate_branch(state.root, branch)
        tracking_result = run_git(
            state.root,
            ["rev-parse", "--symbolic-full-name", "@{upstream}"],
            check=False,
        )
        if tracking_result.returncode != 0 or not tracking_result.stdout:
            raise ActionRequired("NO_UPSTREAM", "upstream tracking ref is unavailable")
        tracking_ref = tracking_result.stdout

    tracking_check = run_git(
        state.root,
        ["check-ref-format", tracking_ref],
        check=False,
    )
    if tracking_check.returncode != 0:
        raise InputError(f"invalid remote tracking ref: {tracking_ref}")
    return RemoteTarget(
        remote=remote,
        branch=branch,
        source_ref=f"refs/heads/{branch}",
        tracking_ref=tracking_ref,
    )


def read_remote_sha(repository: Path, target: RemoteTarget) -> str:
    result = run_git(
        repository,
        ["ls-remote", "--exit-code", target.remote, target.source_ref],
        check=False,
    )
    if result.returncode != 0:
        detail = last_output_line(result)
        suffix = f": {detail}" if detail else ""
        raise GitError(f"cannot read remote branch {target.display_name}{suffix}")

    matching_sha_list = []
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == target.source_ref:
            matching_sha_list.append(parts[0])
    if len(matching_sha_list) != 1:
        raise GitError(f"remote branch was not resolved uniquely: {target.display_name}")
    return matching_sha_list[0]


def commit_exists(repository: Path, sha: str) -> bool:
    result = run_git(
        repository,
        ["cat-file", "-e", f"{sha}^{{commit}}"],
        check=False,
    )
    return result.returncode == 0


def is_ancestor(repository: Path, older_sha: str, newer_sha: str) -> bool:
    result = run_git(
        repository,
        ["merge-base", "--is-ancestor", older_sha, newer_sha],
        check=False,
    )
    if result.returncode not in (0, 1):
        detail = last_output_line(result) or "cannot compare commits"
        raise GitError(detail)
    return result.returncode == 0


def classify_relation(repository: Path, local_sha: str, remote_sha: str) -> str:
    if local_sha == remote_sha:
        return "CURRENT"
    if not commit_exists(repository, remote_sha):
        return "REMOTE_DIFFERS"
    if is_ancestor(repository, remote_sha, local_sha):
        return "AHEAD"
    if is_ancestor(repository, local_sha, remote_sha):
        return "BEHIND"
    return "DIVERGED"


def emit_status(
    status: str,
    state: RepositoryState | None,
    target: RemoteTarget | None,
    *,
    remote_sha: str | None = None,
    detail: str | None = None,
) -> None:
    print(f"STATUS {status}")
    if state is not None:
        print(f"repository: {state.root}")
        print(f"branch: {state.branch}")
        print(f"local: {state.local_sha}")
        print(f"dirty: {'true' if state.dirty_count else 'false'}")
        print(f"dirtyCount: {state.dirty_count}")
    if target is not None:
        print(f"target: {target.display_name}")
    if remote_sha is not None:
        print(f"remote: {remote_sha}")
    if detail:
        print(f"message: {detail}")


def check_repository(
    repository: Path,
    explicit_remote: str | None,
    explicit_branch: str | None,
) -> int:
    state: RepositoryState | None = None
    try:
        state = read_repository_state(repository)
        target = resolve_target(state, explicit_remote, explicit_branch)
        try:
            remote_sha = read_remote_sha(repository, target)
        except GitError as error:
            emit_status("REMOTE_UNAVAILABLE", state, target, detail=str(error))
            return EXIT_ERROR
        relation = classify_relation(repository, state.local_sha, remote_sha)
    except ActionRequired as error:
        state = error.state or state
        emit_status(error.status, state, None, detail=error.detail)
        return EXIT_ACTION_REQUIRED

    emit_status(relation, state, target, remote_sha=remote_sha)
    return EXIT_OK if relation in ("CURRENT", "AHEAD") else EXIT_ACTION_REQUIRED


def fetch_selected_branch(repository: Path, target: RemoteTarget) -> GitResult:
    refspec = f"{target.source_ref}:{target.tracking_ref}"
    return run_git(
        repository,
        ["fetch", "--no-tags", target.remote, refspec],
        check=False,
    )


def update_repository(
    repository: Path,
    explicit_remote: str | None,
    explicit_branch: str | None,
) -> int:
    state: RepositoryState | None = None
    try:
        state = read_repository_state(repository)
        target = resolve_target(state, explicit_remote, explicit_branch)
    except ActionRequired as error:
        state = error.state or state
        emit_status(error.status, state, None, detail=error.detail)
        return EXIT_ACTION_REQUIRED

    if state.dirty_count:
        emit_status(
            "DIRTY",
            state,
            target,
            detail="update requires no staged, tracked, or untracked changes",
        )
        return EXIT_ACTION_REQUIRED

    try:
        initial_remote_sha = read_remote_sha(repository, target)
    except GitError as error:
        emit_status("REMOTE_UNAVAILABLE", state, target, detail=str(error))
        return EXIT_ERROR

    fetch_result = fetch_selected_branch(repository, target)
    if fetch_result.returncode != 0:
        detail = last_output_line(fetch_result) or "selected branch could not be fetched"
        emit_status("FETCH_BLOCKED", state, target, detail=detail)
        return EXIT_ACTION_REQUIRED

    try:
        pre_merge_state = read_repository_state(repository)
    except ActionRequired as error:
        emit_status(
            "WORKTREE_CHANGED",
            error.state,
            target,
            detail="current branch changed while fetching; no merge was attempted",
        )
        return EXIT_ACTION_REQUIRED
    if (
        pre_merge_state.branch != state.branch
        or pre_merge_state.local_sha != state.local_sha
        or pre_merge_state.dirty_count
    ):
        emit_status(
            "WORKTREE_CHANGED",
            pre_merge_state,
            target,
            detail="worktree or current branch changed while fetching; no merge was attempted",
        )
        return EXIT_ACTION_REQUIRED

    fetched_sha = run_git(repository, ["rev-parse", target.tracking_ref]).stdout
    if fetched_sha != initial_remote_sha:
        emit_status(
            "REMOTE_MOVED",
            pre_merge_state,
            target,
            remote_sha=fetched_sha,
            detail=(
                "remote changed before the fast-forward attempt; "
                f"initial remote was {initial_remote_sha}; no retry was attempted"
            ),
        )
        return EXIT_ACTION_REQUIRED

    relation = classify_relation(repository, pre_merge_state.local_sha, fetched_sha)
    if relation == "DIVERGED":
        emit_status(
            "DIVERGED",
            state,
            target,
            remote_sha=fetched_sha,
            detail="fast-forward update is not possible",
        )
        return EXIT_ACTION_REQUIRED

    changed = False
    if relation == "BEHIND":
        merge_result = run_git(
            repository,
            ["merge", "--ff-only", target.tracking_ref],
            check=False,
        )
        if merge_result.returncode != 0:
            detail = last_output_line(merge_result) or "fast-forward merge failed"
            emit_status(
                "UPDATE_BLOCKED",
                state,
                target,
                remote_sha=fetched_sha,
                detail=detail,
            )
            return EXIT_ACTION_REQUIRED
        changed = True
    elif relation == "REMOTE_DIFFERS":
        emit_status(
            "UPDATE_BLOCKED",
            state,
            target,
            remote_sha=fetched_sha,
            detail="fetched remote commit is unavailable for comparison",
        )
        return EXIT_ACTION_REQUIRED

    try:
        final_state = read_repository_state(repository)
    except ActionRequired as error:
        emit_status(
            "WORKTREE_CHANGED",
            error.state,
            target,
            remote_sha=fetched_sha,
            detail="current branch changed during the update",
        )
        return EXIT_ACTION_REQUIRED
    if final_state.branch != state.branch or final_state.dirty_count:
        emit_status(
            "WORKTREE_CHANGED",
            final_state,
            target,
            remote_sha=fetched_sha,
            detail="worktree or current branch changed during the update",
        )
        return EXIT_ACTION_REQUIRED

    try:
        published_sha = read_remote_sha(repository, target)
    except GitError as error:
        emit_status(
            "REMOTE_UNAVAILABLE",
            final_state,
            target,
            remote_sha=fetched_sha,
            detail=str(error),
        )
        return EXIT_ERROR
    if published_sha != fetched_sha:
        emit_status(
            "REMOTE_MOVED",
            final_state,
            target,
            remote_sha=published_sha,
            detail="remote changed during the update; no retry was attempted",
        )
        return EXIT_ACTION_REQUIRED

    final_relation = classify_relation(repository, final_state.local_sha, published_sha)
    if final_relation not in ("CURRENT", "AHEAD"):
        emit_status(
            "UPDATE_BLOCKED",
            final_state,
            target,
            remote_sha=published_sha,
            detail=f"unexpected post-update relation: {final_relation}",
        )
        return EXIT_ACTION_REQUIRED

    emit_status(
        "UPDATED" if changed else final_relation,
        final_state,
        target,
        remote_sha=published_sha,
    )
    return EXIT_OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check remote Git state or perform an approved fast-forward update."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "update"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument(
            "--repo",
            default=".",
            help="Git worktree path; defaults to the current directory",
        )
        command_parser.add_argument(
            "--remote",
            help="Explicit remote name; must be used with --branch",
        )
        command_parser.add_argument(
            "--branch",
            help="Explicit remote branch; must be used with --remote",
        )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if (arguments.remote is None) != (arguments.branch is None):
        parser.error("--remote and --branch must be provided together")

    try:
        repository = find_repository(arguments.repo)
        if arguments.command == "check":
            return check_repository(repository, arguments.remote, arguments.branch)
        return update_repository(repository, arguments.remote, arguments.branch)
    except InputError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return EXIT_ERROR
    except GitError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
