---
name: git-latest-code-check
description: Check whether a Git worktree contains the latest selected remote branch before planning or modifying code, and perform only an explicitly approved fast-forward update; skip non-Git work and ref-pinned read-only analysis.
---

# Git Latest Code Check

Use once per task before substantive code planning, creation, or modification in each Git worktree. This check establishes the task baseline; it does not promise that the remote will remain unchanged during the task.

## Check Before Work

Run the read-only command before relying on repository code:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" check --repo "<repository>"
```

Use `--remote <name> --branch <name>` together only when the task or user explicitly identifies the intended remote branch and the current branch has no usable upstream. Never infer and persist an upstream.

- Continue when the status is `CURRENT` or `AHEAD`
- Stop before finalizing a code plan or editing when the command reports `REMOTE_DIFFERS`, `BEHIND`, `DIVERGED`, `NO_UPSTREAM`, `DETACHED`, or any error
- Tell the user the repository, current branch, intended remote branch, local/remote commits when available, dirty state, and why work stopped
- Do not rerun during the same task unless the repository or branch changes, the user requests it, or an approved update succeeds

Skip this workflow for non-Git directories, ordinary explanatory questions, and read-only analysis explicitly pinned to a commit, PR, tag, or immutable ref.

## Update Only After Approval

An instruction to plan or change code does not authorize a repository update. Run `update` only after the user explicitly approves updating the reported repository and remote branch in the current conversation:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" update --repo "<repository>"
```

The update command must reject tracked, staged, or untracked changes, detached HEAD, missing upstream, divergence, remote rewrites, and remote movement during the attempt. It may fetch the selected branch and perform only a fast-forward merge. Never stash, rebase, reset, force, create a merge commit, discard changes, set upstream, or select another branch automatically.

In a mode that prohibits mutation, do not run `update` even after approval. Explain that the freshness check failed and defer updating until work can run in a writable mode.

After a successful update, discard conclusions based on the previous checkout, reread the relevant repository instructions and source, then restart planning or implementation. If the update is blocked or fails, stop after that single attempt.

## Script Contract

Read [README.md](README.md) only when exact statuses, exit codes, installation, troubleshooting, or direct CLI use are needed. The script uses `git ls-remote` in `check` mode and does not fetch or modify repository state. Exit `0` means the selected remote tip is present in local history or an update succeeded, `1` means user action is required, and `2` means input, Git, network, or environment failure.
