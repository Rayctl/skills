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
        for folder in (git_directory / "refs", git_directory / "logs" / "refs"):
            if folder.exists():
                paths.extend(path for path in folder.rglob("*") if path.is_file())
        return {
            str(path.relative_to(git_directory)): path.read_bytes() if path.exists() else None
            for path in sorted(set(paths))
        }

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


if __name__ == "__main__":
    unittest.main()
