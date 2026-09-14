---
name: git-latest-code-check
description: Check whether an already-confirmed Git worktree contains the latest selected remote branch before substantive code planning or modification, and perform only an explicitly approved fast-forward update. Do not use this skill to discover whether a task has a repository.
---

# Git Latest Code Check

Use once per task before substantive code planning, creation, or modification in each Git worktree. The caller must already have confirmed the target with `git rev-parse --is-inside-work-tree` in the current working directory or an explicitly named repository path. Do not load or invoke this skill merely to discover whether a task has a repository, and do not search unrelated directories for one. This check establishes the task baseline; it does not promise that the remote will remain unchanged during the task.

## Check Before Work

Run the read-only command before relying on repository code:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" check --repo "<repository>"
```

Use `--remote <name> --branch <name>` together only when the task or user explicitly identifies the intended remote branch and the current branch has no usable upstream. Never infer and persist an upstream.

Always run the read-only check even when the worktree already has staged, tracked, or untracked changes. Interpret the result together with the emitted `dirty` field:

- When `dirty: false`, continue only for `CURRENT` or `AHEAD`. Stop before finalizing a code plan or editing for `REMOTE_DIFFERS`, `BEHIND`, `DIVERGED`, `NO_UPSTREAM`, `DETACHED`, `REMOTE_UNAVAILABLE`, or any command error, then explain the state and the required action.
- When `dirty: true`, continue for `CURRENT` or `AHEAD` and mention the dirty state. Treat `REMOTE_DIFFERS`, `BEHIND`, `DIVERGED`, `NO_UPSTREAM`, `REMOTE_UNAVAILABLE`, and remote-read errors as visible non-blocking warnings: do not request or run an update, and continue only work related to the changes already present in that worktree.
- `DETACHED`, invalid repository or target input, and local Git failures remain stopping conditions even when the worktree is dirty because the local work context cannot be established safely.
- Before continuing in a dirty worktree, confirm from the task and relevant local diff that the requested work belongs with the existing changes. If it is unrelated or cannot be separated safely, stop and require a clean worktree instead of mixing the work.
- Do not rerun during the same task unless the repository or branch changes, the user requests it, or an approved update succeeds.

Skip this workflow without mentioning the skill when the conversation has no associated Git repository, no repository path was explicitly provided, or the candidate directory is not a Git worktree. Also skip ordinary explanatory questions and read-only analysis explicitly pinned to a commit, PR, tag, or immutable ref.

## Report Every Result

After every `check` or `update` invocation, give the user a visible result before continuing or stopping. Command or tool output alone does not satisfy this requirement because the user may not see it. Use the user's language.

- For `CURRENT`, report the repository, current branch, remote target, `CURRENT`, and the first seven characters of the shared commit. Keep this to one concise sentence.
- For `AHEAD`, report the repository, current branch, remote target, `AHEAD`, and the first seven characters of both local and remote commits; explicitly say that the local branch contains the remote tip and has additional commits.
- For `UPDATED`, report the repository, current branch, remote target, `UPDATED`, and the first seven characters of the new local commit.
- For a successful status, mention the dirty worktree only when `dirty: true`.
- For every unsuccessful status or command error, report the emitted status, or `ERROR` when no status was emitted, plus the repository, branch, target, local and remote commits when available, dirty state when known, and the reason.
- For a dirty-worktree remote warning, explicitly say that remote freshness was not established, the existing related work may continue, and `update` is prohibited while the worktree is dirty. For all other failures, state the next required action and preserve the stop and approval boundary.

## Update Only After Approval

An instruction to plan or change code does not authorize a repository update. Never invoke `update` after a check reports `dirty: true`, even if the user approves; explain that local changes must first be handled by the user in a separate workflow. For a clean worktree, run `update` only after the user explicitly approves updating the reported repository and remote branch in the current conversation:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" update --repo "<repository>"
```

The update command must reject tracked, staged, or untracked changes, detached HEAD, missing upstream, divergence, remote rewrites, and remote movement during the attempt. It may fetch the selected branch and perform only a fast-forward merge. Never stash, rebase, reset, force, create a merge commit, discard changes, set upstream, or select another branch automatically.

In a mode that prohibits mutation, do not run `update` even after approval. Explain that the freshness check failed and defer updating until work can run in a writable mode.

After a successful update, discard conclusions based on the previous checkout, reread the relevant repository instructions and source, then restart planning or implementation. If the update is blocked or fails, stop after that single attempt.

## Script Contract

Read [README.md](README.md) only when exact statuses, exit codes, installation, troubleshooting, or direct CLI use are needed. The script uses `git ls-remote` in `check` mode and does not fetch or modify repository state. Exit `0` means the selected remote tip is present in local history or an update succeeded, `1` means the CLI found a state that normally requires action, and `2` means input, Git, network, or environment failure. For `check`, apply the dirty-worktree policy above instead of treating a nonzero exit code by itself as a mandatory stop.
