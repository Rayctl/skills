from __future__ import annotations

import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = SKILL_ROOT / "scripts" / "git_latest_code.py"
SPEC = importlib.util.spec_from_file_location("git_latest_code", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
git_latest_code = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = git_latest_code
SPEC.loader.exec_module(git_latest_code)


class GitLatestCodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repository fixture with spaces"
        self.root.mkdir()
        self.remote = self.root / "remote.git"
        self.publisher = self.root / "publisher"
        self.worktree = self.root / "worktree with spaces"

        self.git(self.root, "init", "--bare", str(self.remote))
        self.git(self.root, "init", str(self.publisher))
        self.configure_identity(self.publisher)
        (self.publisher / "tracked.txt").write_text("initial\n", encoding="utf-8")
        self.git(self.publisher, "add", "tracked.txt")
        self.git(self.publisher, "commit", "-m", "initial")
        self.git(self.publisher, "branch", "-M", "main")
        self.git(self.publisher, "remote", "add", "origin", str(self.remote))
        self.git(self.publisher, "push", "-u", "origin", "main")
        self.git(
            self.root,
            "clone",
            "--branch",
            "main",
            str(self.remote),
            str(self.worktree),
        )
        self.configure_identity(self.worktree)

    def git(
        self,
        repository: Path,
        *arguments: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *arguments],
            cwd=repository,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=check,
        )

    def configure_identity(self, repository: Path) -> None:
        self.git(repository, "config", "user.name", "Skill Test")
        self.git(repository, "config", "user.email", "skill-test@example.com")

    def test_run_git_disables_optional_writes_and_lazy_fetches(self) -> None:
        completed = mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.object(
            git_latest_code.subprocess,
            "run",
            return_value=completed,
        ) as run:
            git_latest_code.run_git(self.worktree, ["status"])

        environment = run.call_args.kwargs["env"]
        self.assertEqual("0", environment["GIT_OPTIONAL_LOCKS"])
        self.assertEqual("1", environment["GIT_NO_LAZY_FETCH"])

    def test_run_git_preserves_lazy_fetch_policy_for_approved_write(self) -> None:
        completed = mock.Mock(returncode=0, stdout="", stderr="")

        with mock.patch.dict(
            git_latest_code.os.environ,
            {"GIT_NO_LAZY_FETCH": "caller-policy"},
            clear=True,
        ), mock.patch.object(
            git_latest_code.subprocess,
            "run",
            return_value=completed,
        ) as run:
            git_latest_code.run_git(
                self.worktree,
                ["merge", "--ff-only", "refs/remotes/origin/main"],
                allow_lazy_fetch=True,
            )

        environment = run.call_args.kwargs["env"]
        self.assertEqual("caller-policy", environment["GIT_NO_LAZY_FETCH"])

    def run_tool(
        self,
        command: str,
        repository: Path | None = None,
        *arguments: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT_PATH),
                command,
                "--repo",
                str(repository or self.worktree),
                *arguments,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )

    def publish_change(self, content: str) -> str:
        (self.publisher / "tracked.txt").write_text(content, encoding="utf-8")
        self.git(self.publisher, "add", "tracked.txt")
        self.git(self.publisher, "commit", "-m", content.strip())
        self.git(self.publisher, "push", "origin", "main")
        return self.git(self.publisher, "rev-parse", "HEAD").stdout.strip()

    def commit_local_change(self, content: str) -> str:
        (self.worktree / "local.txt").write_text(content, encoding="utf-8")
        self.git(self.worktree, "add", "local.txt")
        self.git(self.worktree, "commit", "-m", content.strip())
        return self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()

    def git_metadata_snapshot(self) -> dict[str, bytes | None]:
        git_directory = self.worktree / ".git"
        paths = [
            git_directory / "index",
            git_directory / "FETCH_HEAD",
            git_directory / "packed-refs",
        ]
        paths.extend(path for path in git_directory.rglob("*") if path.is_file())
        for folder in (git_directory / "refs", git_directory / "logs" / "refs"):
            if folder.exists():
                paths.extend(path for path in folder.rglob("*") if path.is_file())
        return {
            str(path.relative_to(git_directory)): path.read_bytes() if path.exists() else None
            for path in sorted(set(paths))
        }

    def readonly_snapshot(self) -> tuple[dict, dict]:
        return self.git_metadata_snapshot(), {
            str(path.relative_to(self.worktree)): path.read_bytes()
            for path in self.worktree.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(self.worktree).parts
        }

    def assert_readonly(self, command: str, status: str, code: int, *args: str) -> None:
        before = self.readonly_snapshot()
        result = self.run_tool(command, None, *args)
        self.assertEqual(code, result.returncode, result.stdout + result.stderr)
        self.assertIn(f"STATUS {status}", result.stdout)
        self.assertEqual(before, self.readonly_snapshot())

    def push_check(self, status: str, code: int, branch: str = "main") -> None:
        self.assert_readonly("verify-push", status, code, "--remote", "origin", "--branch", branch)

    def test_check_current_is_read_only_and_supports_spaces(self) -> None:
        before = self.git_metadata_snapshot()

        result = self.run_tool("check")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STATUS CURRENT", result.stdout)
        self.assertIn(str(self.worktree), result.stdout)
        self.assertEqual(before, self.git_metadata_snapshot())
        self.assertEqual("", self.git(self.worktree, "status", "--porcelain").stdout)

    def test_check_allows_local_branch_ahead_of_remote(self) -> None:
        self.commit_local_change("local ahead\n")

        result = self.run_tool("check")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STATUS AHEAD", result.stdout)

    def test_check_reports_remote_difference_without_fetching(self) -> None:
        self.publish_change("remote ahead\n")
        before = self.git_metadata_snapshot()

        result = self.run_tool("check")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS REMOTE_DIFFERS", result.stdout)
        self.assertEqual(before, self.git_metadata_snapshot())

    def test_check_reports_behind_when_remote_commit_is_available(self) -> None:
        initial_sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        self.publish_change("known remote ahead\n")
        self.git(self.worktree, "fetch", "origin", "main")
        self.git(self.worktree, "checkout", "-b", "local-behind", initial_sha)
        self.git(self.worktree, "branch", "--set-upstream-to=origin/main")

        result = self.run_tool("check")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS BEHIND", result.stdout)

    def test_check_allows_dirty_worktree_when_remote_is_current(self) -> None:
        (self.worktree / "tracked.txt").write_text("local work\n", encoding="utf-8")

        result = self.run_tool("check")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STATUS CURRENT", result.stdout)
        self.assertIn("dirty: true", result.stdout)

    def test_update_fast_forwards_clean_branch(self) -> None:
        remote_sha = self.publish_change("fast forward\n")
        upstream_before = self.git(
            self.worktree,
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
        ).stdout.strip()
        stash_before = self.git(self.worktree, "stash", "list").stdout

        result = self.run_tool("update")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("STATUS UPDATED", result.stdout)
        self.assertEqual(remote_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())
        parent_line = self.git(
            self.worktree,
            "rev-list",
            "--parents",
            "-n",
            "1",
            "HEAD",
        ).stdout.split()
        self.assertEqual(2, len(parent_line))
        self.assertEqual(stash_before, self.git(self.worktree, "stash", "list").stdout)
        self.assertEqual(
            upstream_before,
            self.git(
                self.worktree,
                "rev-parse",
                "--abbrev-ref",
                "--symbolic-full-name",
                "@{upstream}",
            ).stdout.strip(),
        )

    def test_update_rejects_tracked_changes_before_fetch(self) -> None:
        self.publish_change("remote update\n")
        tracking_before = self.git(self.worktree, "rev-parse", "origin/main").stdout.strip()
        (self.worktree / "tracked.txt").write_text("dirty\n", encoding="utf-8")

        result = self.run_tool("update")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS DIRTY", result.stdout)
        self.assertEqual(
            tracking_before,
            self.git(self.worktree, "rev-parse", "origin/main").stdout.strip(),
        )

    def test_update_rejects_untracked_changes(self) -> None:
        (self.worktree / "untracked.txt").write_text("untracked\n", encoding="utf-8")

        result = self.run_tool("update")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS DIRTY", result.stdout)

    def test_update_rejects_staged_changes(self) -> None:
        (self.worktree / "tracked.txt").write_text("staged\n", encoding="utf-8")
        self.git(self.worktree, "add", "tracked.txt")

        result = self.run_tool("update")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS DIRTY", result.stdout)

    def test_check_requires_upstream_or_explicit_target(self) -> None:
        self.git(self.worktree, "branch", "--unset-upstream")

        missing = self.run_tool("check")
        explicit = self.run_tool("check", None, "--remote", "origin", "--branch", "main")

        self.assertEqual(1, missing.returncode)
        self.assertIn("STATUS NO_UPSTREAM", missing.stdout)
        self.assertEqual(0, explicit.returncode, explicit.stderr)
        self.assertIn("STATUS CURRENT", explicit.stdout)

    def test_explicit_update_does_not_set_upstream(self) -> None:
        self.git(self.worktree, "branch", "--unset-upstream")
        remote_sha = self.publish_change("explicit fast forward\n")

        result = self.run_tool(
            "update",
            None,
            "--remote",
            "origin",
            "--branch",
            "main",
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(remote_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())
        upstream = self.git(
            self.worktree,
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{upstream}",
            check=False,
        )
        self.assertNotEqual(0, upstream.returncode)

    def test_update_rejects_diverged_branch_without_merge_commit(self) -> None:
        local_sha = self.commit_local_change("local branch\n")
        self.publish_change("remote branch\n")

        result = self.run_tool("update")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS DIVERGED", result.stdout)
        self.assertEqual(local_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_rejects_remote_history_rewrite(self) -> None:
        self.git(self.publisher, "checkout", "--orphan", "replacement")
        self.git(self.publisher, "rm", "-f", "tracked.txt")
        (self.publisher / "replacement.txt").write_text("replacement\n", encoding="utf-8")
        self.git(self.publisher, "add", "replacement.txt")
        self.git(self.publisher, "commit", "-m", "replacement history")
        self.git(self.publisher, "push", "--force", "origin", "HEAD:main")
        local_sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()

        result = self.run_tool("update")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS FETCH_BLOCKED", result.stdout)
        self.assertEqual(local_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_stops_when_worktree_changes_during_fetch(self) -> None:
        self.publish_change("remote before concurrent work\n")
        repository = git_latest_code.find_repository(str(self.worktree))
        actual_fetch = git_latest_code.fetch_selected_branch

        def fetch_and_modify(root: Path, target: object) -> object:
            result = actual_fetch(root, target)
            (root / "concurrent.txt").write_text("concurrent\n", encoding="utf-8")
            return result

        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code,
            "fetch_selected_branch",
            side_effect=fetch_and_modify,
        ):
            result = git_latest_code.update_repository(repository, None, None)

        self.assertEqual(1, result)
        self.assertIn("STATUS WORKTREE_CHANGED", output.getvalue())
        self.assertNotEqual(
            self.git(self.publisher, "rev-parse", "HEAD").stdout.strip(),
            self.git(self.worktree, "rev-parse", "HEAD").stdout.strip(),
        )

    def test_update_stops_when_branch_detaches_during_fetch(self) -> None:
        self.publish_change("remote before branch change\n")
        local_sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual_fetch = git_latest_code.fetch_selected_branch

        def fetch_and_detach(root: Path, target: object) -> object:
            result = actual_fetch(root, target)
            self.git(root, "checkout", "--detach")
            return result

        repository = git_latest_code.find_repository(str(self.worktree))
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code,
            "fetch_selected_branch",
            side_effect=fetch_and_detach,
        ):
            result = git_latest_code.update_repository(repository, None, None)

        self.assertEqual(1, result)
        self.assertIn("STATUS WORKTREE_CHANGED", output.getvalue())
        self.assertIn("branch: (detached)", output.getvalue())
        self.assertEqual(local_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_stops_when_remote_moves_before_fetch(self) -> None:
        first_remote_sha = self.publish_change("first remote update\n")
        local_sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual_fetch = git_latest_code.fetch_selected_branch
        fetch_count = 0

        def move_remote_then_fetch(root: Path, target: object) -> object:
            nonlocal fetch_count
            fetch_count += 1
            self.publish_change("competing remote update\n")
            return actual_fetch(root, target)

        repository = git_latest_code.find_repository(str(self.worktree))
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code,
            "fetch_selected_branch",
            side_effect=move_remote_then_fetch,
        ):
            result = git_latest_code.update_repository(repository, None, None)

        self.assertEqual(1, result)
        self.assertEqual(1, fetch_count)
        self.assertIn("STATUS REMOTE_MOVED", output.getvalue())
        self.assertIn(first_remote_sha, output.getvalue())
        self.assertEqual(local_sha, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_check_rejects_detached_head(self) -> None:
        self.git(self.worktree, "checkout", "--detach")

        result = self.run_tool("check")

        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS DETACHED", result.stdout)
        self.assertIn("branch: (detached)", result.stdout)
        self.assertIn("local:", result.stdout)

    def test_remote_failure_is_environment_error(self) -> None:
        self.git(self.worktree, "remote", "set-url", "origin", str(self.root / "missing.git"))

        result = self.run_tool("check")

        self.assertEqual(2, result.returncode)
        self.assertIn("STATUS REMOTE_UNAVAILABLE", result.stdout)
        self.assertIn("cannot read remote branch", result.stdout)

    def test_non_git_directory_is_input_error(self) -> None:
        directory = self.root / "not a repository"
        directory.mkdir()

        result = self.run_tool("check", directory)

        self.assertEqual(2, result.returncode)
        self.assertIn("not a Git worktree", result.stderr)

    def test_remote_and_branch_must_be_provided_together(self) -> None:
        result = self.run_tool("check", None, "--remote", "origin")

        self.assertEqual(2, result.returncode)
        self.assertIn("must be provided together", result.stderr)

    def test_update_reports_remote_movement_without_retry(self) -> None:
        self.publish_change("moving remote\n")
        repository = git_latest_code.find_repository(str(self.worktree))
        actual_reader = git_latest_code.read_remote_sha
        call_count = 0

        def moved_remote(root: Path, target: object) -> str:
            nonlocal call_count
            call_count += 1
            actual_sha = actual_reader(root, target)
            return "f" * 40 if call_count == 2 else actual_sha

        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code,
            "read_remote_sha",
            side_effect=moved_remote,
        ):
            result = git_latest_code.update_repository(repository, None, None)

        self.assertEqual(1, result)
        self.assertEqual(2, call_count)
        self.assertIn("STATUS REMOTE_MOVED", output.getvalue())

    def test_missing_branch_with_stale_and_pruned_tracking_clean_and_dirty(self) -> None:
        self.git(self.remote, "update-ref", "-d", "refs/heads/main")
        for pruned in (False, True):
            if pruned:
                self.git(self.worktree, "fetch", "--prune", "origin")
            for dirty in (False, True):
                path = self.worktree / "dirty.txt"
                if dirty:
                    path.write_text("existing work\n", encoding="utf-8")
                for command in ("check", "update"):
                    with self.subTest(pruned=pruned, dirty=dirty, command=command):
                        self.assert_readonly(command, "REMOTE_BRANCH_MISSING", 1)
                self.push_check("REMOTE_BRANCH_MISSING", 1)
                if dirty:
                    path.unlink()

    def test_no_target_blocks_even_dirty_and_explicit_existing_target_works(self) -> None:
        self.git(self.worktree, "branch", "--unset-upstream")
        for dirty in (False, True):
            if dirty:
                (self.worktree / "dirty.txt").write_text("work\n", encoding="utf-8")
            for command in ("check", "update"):
                self.assert_readonly(command, "NO_UPSTREAM", 1)
            self.assert_readonly("check", "CURRENT", 0, "--remote", "origin", "--branch", "main")

    def test_custom_fetch_mapping_survives_absent_tracking_ref(self) -> None:
        self.git(self.worktree, "config", "remote.origin.fetch", "+refs/heads/*:refs/custom/*")
        self.assert_readonly("check", "CURRENT", 0)
        sha = self.publish_change("custom mapping update\n")
        result = self.run_tool("update")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual(sha, self.git(self.worktree, "rev-parse", "refs/custom/main").stdout.strip())
        self.git(self.remote, "update-ref", "-d", "refs/heads/main")
        self.git(self.worktree, "update-ref", "-d", "refs/custom/main")
        self.assert_readonly("check", "REMOTE_BRANCH_MISSING", 1)

    def test_operation_markers_block_all_commands_before_dirty_or_detached(self) -> None:
        sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        self.git(self.worktree, "checkout", "--detach")
        (self.worktree / "dirty.txt").write_text("work\n", encoding="utf-8")
        for marker in ("MERGE_HEAD", "CHERRY_PICK_HEAD", "REVERT_HEAD", "rebase-merge", "rebase-apply", "sequencer"):
            path = self.worktree / self.git(self.worktree, "rev-parse", "--git-path", marker).stdout.strip()
            if marker.endswith("HEAD"):
                path.write_text(sha + "\n", encoding="utf-8")
            else:
                path.mkdir()
            for command in ("check", "update", "verify-push"):
                args = ("--remote", "origin", "--branch", "main") if command == "verify-push" else ()
                with self.subTest(marker=marker, command=command):
                    self.assert_readonly(command, "GIT_OPERATION_IN_PROGRESS", 1, *args)
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()

    def test_linked_worktree_operation_detection(self) -> None:
        linked = self.root / "linked"
        self.git(self.worktree, "worktree", "add", "-b", "linked", str(linked))
        marker = linked / self.git(linked, "rev-parse", "--git-path", "sequencer").stdout.strip()
        marker.mkdir()
        result = self.run_tool("check", linked, "--remote", "origin", "--branch", "main")
        self.assertEqual(1, result.returncode)
        self.assertIn("STATUS GIT_OPERATION_IN_PROGRESS", result.stdout)
        self.assertTrue(marker.exists())

    def run_update_hook(self, name: str, hook: object) -> tuple[int, str]:
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(git_latest_code, name, side_effect=hook):
            code = git_latest_code.update_repository(self.worktree, None, None)
        return code, output.getvalue()

    def test_update_remote_deleted_before_fetch(self) -> None:
        self.publish_change("delete before fetch\n")
        before = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual = git_latest_code.fetch_selected_branch
        def hook(root, target):
            self.git(self.remote, "update-ref", "-d", "refs/heads/main")
            return actual(root, target)
        code, output = self.run_update_hook("fetch_selected_branch", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS REMOTE_BRANCH_MISSING", output)
        self.assertIn(before, output)
        self.assertEqual(before, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_remote_deleted_after_fetch_stops_before_merge(self) -> None:
        self.publish_change("delete after fetch\n")
        before = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual = git_latest_code.fetch_selected_branch
        def hook(root, target):
            result = actual(root, target)
            self.git(self.remote, "update-ref", "-d", "refs/heads/main")
            return result
        code, output = self.run_update_hook("fetch_selected_branch", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS REMOTE_BRANCH_MISSING", output)
        self.assertEqual(before, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_operation_appears_during_fetch(self) -> None:
        self.publish_change("operation during fetch\n")
        before = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual = git_latest_code.fetch_selected_branch
        def hook(root, target):
            result = actual(root, target)
            (root / ".git" / "sequencer").mkdir()
            return result
        code, output = self.run_update_hook("fetch_selected_branch", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS GIT_OPERATION_IN_PROGRESS", output)
        self.assertEqual(before, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_post_merge_deleted_reports_actual_head(self) -> None:
        expected = self.publish_change("post merge deletion\n")
        actual = git_latest_code.run_git
        def hook(root, args, **kwargs):
            result = actual(root, args, **kwargs)
            if args[0] == "merge":
                self.git(self.remote, "update-ref", "-d", "refs/heads/main")
            return result
        code, output = self.run_update_hook("run_git", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS REMOTE_BRANCH_MISSING", output)
        self.assertIn(f"local: {expected}", output)
        self.assertEqual(expected, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_post_merge_operation_stops_verification(self) -> None:
        expected = self.publish_change("post merge operation\n")
        actual = git_latest_code.run_git
        def hook(root, args, **kwargs):
            result = actual(root, args, **kwargs)
            if args[0] == "merge":
                (root / ".git" / "sequencer").mkdir()
            return result
        code, output = self.run_update_hook("run_git", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS GIT_OPERATION_IN_PROGRESS", output)
        self.assertIn(f"local: {expected}", output)

    def test_update_fetch_failure_diagnoses_unavailable_without_retry(self) -> None:
        actual = git_latest_code.fetch_selected_branch
        calls = []
        def hook(root, target):
            calls.append(target)
            self.git(root, "remote", "set-url", "origin", str(self.root / "absent.git"))
            return actual(root, target)
        code, output = self.run_update_hook("fetch_selected_branch", hook)
        self.assertEqual(2, code)
        self.assertEqual(1, len(calls))
        self.assertIn("STATUS REMOTE_UNAVAILABLE", output)

    def test_verify_push_current_ahead_and_dirty(self) -> None:
        self.push_check("CURRENT", 0)
        self.commit_local_change("ahead\n")
        (self.worktree / "dirty.txt").write_text("uncommitted\n", encoding="utf-8")
        self.push_check("AHEAD", 0)

    def test_verify_push_unknown_behind_and_diverged(self) -> None:
        self.publish_change("remote commit\n")
        self.push_check("REMOTE_DIFFERS", 1)
        self.git(self.worktree, "fetch", "origin")
        self.push_check("BEHIND", 1)
        self.commit_local_change("diverged\n")
        self.push_check("DIVERGED", 1)

    def test_verify_push_uses_push_address_and_destination_not_upstream(self) -> None:
        push_remote = self.root / "push.git"
        self.git(self.root, "clone", "--bare", str(self.remote), str(push_remote))
        self.git(push_remote, "update-ref", "refs/heads/destination", "refs/heads/main")
        self.git(self.worktree, "remote", "set-url", "--push", "origin", str(push_remote))
        self.publish_change("fetch address now ahead\n")
        self.push_check("CURRENT", 0, "destination")
        self.git(push_remote, "update-ref", "-d", "refs/heads/destination")
        self.push_check("REMOTE_BRANCH_MISSING", 1, "destination")

    def test_verify_push_multiple_addresses_and_invalid_inputs(self) -> None:
        missing = self.run_tool("verify-push")
        self.assertEqual(2, missing.returncode)
        self.git(self.worktree, "config", "--add", "remote.origin.pushurl", str(self.remote))
        self.git(self.worktree, "config", "--add", "remote.origin.pushurl", str(self.root / "other.git"))
        self.push_check("ERROR", 2)
        self.assert_readonly("verify-push", "ERROR", 2, "--remote", "unknown", "--branch", "main")

    def test_verify_push_unavailable_is_not_missing(self) -> None:
        self.git(self.worktree, "remote", "set-url", "--push", "origin", str(self.root / "absent.git"))
        self.push_check("REMOTE_UNAVAILABLE", 2)

    def test_clean_operation_blocks_all_commands(self) -> None:
        sha = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        (self.worktree / ".git" / "MERGE_HEAD").write_text(sha + "\n", encoding="utf-8")
        for command in ("check", "update"):
            self.assert_readonly(command, "GIT_OPERATION_IN_PROGRESS", 1)
        self.push_check("GIT_OPERATION_IN_PROGRESS", 1)

    def test_update_operation_appears_during_initial_remote_query(self) -> None:
        self.publish_change("operation before fetch\n")
        before = self.git(self.worktree, "rev-parse", "HEAD").stdout.strip()
        actual = git_latest_code.read_remote_sha
        def hook(root, target):
            result = actual(root, target)
            (root / ".git" / "sequencer").mkdir()
            return result
        with mock.patch.object(git_latest_code, "fetch_selected_branch") as fetch:
            code, output = self.run_update_hook("read_remote_sha", hook)
        fetch.assert_not_called()
        self.assertEqual(1, code)
        self.assertIn("STATUS GIT_OPERATION_IN_PROGRESS", output)
        self.assertEqual(before, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_head_changes_during_fetch_stops_before_merge(self) -> None:
        self.publish_change("head change during fetch\n")
        actual = git_latest_code.fetch_selected_branch
        expected = []
        def hook(root, target):
            result = actual(root, target)
            expected.append(self.commit_local_change("concurrent commit\n"))
            return result
        code, output = self.run_update_hook("fetch_selected_branch", hook)
        self.assertEqual(1, code)
        self.assertIn("STATUS WORKTREE_CHANGED", output)
        self.assertIn(f"local: {expected[0]}", output)
        self.assertEqual(expected[0], self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_update_post_merge_unavailable_reports_actual_head(self) -> None:
        expected = self.publish_change("post merge access failure\n")
        actual = git_latest_code.run_git
        def hook(root, args, **kwargs):
            result = actual(root, args, **kwargs)
            if args[0] == "merge":
                self.git(root, "remote", "set-url", "origin", str(self.root / "absent.git"))
            return result
        code, output = self.run_update_hook("run_git", hook)
        self.assertEqual(2, code)
        self.assertIn("STATUS REMOTE_UNAVAILABLE", output)
        self.assertIn(f"local: {expected}", output)

    def test_verify_push_comparison_failure_is_action_required(self) -> None:
        self.commit_local_change("comparison failure\n")
        output = io.StringIO()
        before = self.readonly_snapshot()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code, "is_ancestor", side_effect=git_latest_code.GitError("missing parent")
        ):
            code = git_latest_code.verify_push(self.worktree, "origin", "main")
        self.assertEqual(1, code)
        self.assertIn("STATUS REMOTE_DIFFERS", output.getvalue())
        self.assertIn("further verification", output.getvalue())
        self.assertEqual(before, self.readonly_snapshot())

    def test_verify_push_stops_if_head_changes_during_remote_query(self) -> None:
        actual = git_latest_code.read_remote_sha
        expected = []
        def hook(root, target, endpoint=None):
            sha = actual(root, target, endpoint)
            expected.append(self.commit_local_change("concurrent push head\n"))
            return sha
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(git_latest_code, "read_remote_sha", side_effect=hook):
            code = git_latest_code.verify_push(self.worktree, "origin", "main")
        self.assertEqual(1, code)
        self.assertIn("STATUS WORKTREE_CHANGED", output.getvalue())
        self.assertIn(f"local: {expected[0]}", output.getvalue())

    def test_verify_push_stops_if_operation_appears_during_remote_query(self) -> None:
        actual = git_latest_code.read_remote_sha
        def hook(root, target, endpoint=None):
            sha = actual(root, target, endpoint)
            (root / ".git" / "sequencer").mkdir()
            return sha
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(git_latest_code, "read_remote_sha", side_effect=hook):
            code = git_latest_code.verify_push(self.worktree, "origin", "main")
        self.assertEqual(1, code)
        self.assertIn("STATUS GIT_OPERATION_IN_PROGRESS", output.getvalue())
        self.assertTrue((self.worktree / ".git" / "sequencer").exists())

    def test_check_local_comparison_error_keeps_target_and_commits(self) -> None:
        local_sha = self.commit_local_change("local compare error\n")
        remote_sha = self.git(self.remote, "rev-parse", "refs/heads/main").stdout.strip()
        before = self.readonly_snapshot()
        output = io.StringIO()
        with redirect_stdout(output), mock.patch.object(
            git_latest_code, "is_ancestor", side_effect=git_latest_code.GitError("local object error")
        ):
            code = git_latest_code.check_repository(self.worktree, None, None)
        self.assertEqual(2, code)
        for expected in ("STATUS ERROR", "target: origin/main", local_sha, remote_sha, "dirty: false"):
            self.assertIn(expected, output.getvalue())
        self.assertEqual(before, self.readonly_snapshot())

    def test_update_merge_timeout_after_moving_head_reports_actual_state(self) -> None:
        expected = self.publish_change("merge timeout\n")
        actual = git_latest_code.run_git
        def hook(root, args, **kwargs):
            result = actual(root, args, **kwargs)
            if args[0] == "merge":
                raise git_latest_code.GitError("git command timed out")
            return result
        code, output = self.run_update_hook("run_git", hook)
        self.assertEqual(2, code)
        for value in ("STATUS ERROR", f"local: {expected}", f"remote: {expected}", "target: origin/main", "dirty: false"):
            self.assertIn(value, output)
        self.assertEqual(expected, self.git(self.worktree, "rev-parse", "HEAD").stdout.strip())

    def test_malformed_and_timeout_remote_results_are_unavailable(self) -> None:
        for result in (git_latest_code.GitResult(0, "malformed refs/heads/main", ""),
                       git_latest_code.GitResult(128, "", "authentication failed")):
            actual = git_latest_code.run_git
            def hook(root, args, **kwargs):
                return result if args[0] == "ls-remote" else actual(root, args, **kwargs)
            output = io.StringIO()
            with redirect_stdout(output), mock.patch.object(git_latest_code, "run_git", side_effect=hook):
                code = git_latest_code.check_repository(self.worktree, None, None)
            self.assertEqual(2, code)
            self.assertIn("STATUS REMOTE_UNAVAILABLE", output.getvalue())
        with mock.patch.object(git_latest_code.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 30)):
            with self.assertRaises(git_latest_code.GitError):
                git_latest_code.run_git(self.worktree, ["ls-remote"])


if __name__ == "__main__":
    unittest.main()
