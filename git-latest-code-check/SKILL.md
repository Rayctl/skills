---
name: git-latest-code-check
description: Check whether an already-confirmed Git worktree contains the latest selected remote branch before substantive code planning or modification, and perform only an explicitly approved fast-forward update. Do not use this skill to discover whether a task has a repository.
---

# Git Latest Code Check

Use once per task before substantive code planning, creation, or modification in each already-confirmed Git worktree. The caller must first verify the candidate with `git rev-parse --is-inside-work-tree`; this Skill does not discover repositories or search unrelated directories.

## Check Before Work

Run the read-only check:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" check --repo "<repository>"
```

Use `--remote` and `--branch` together only when the user explicitly identifies the target and no usable upstream exists. Never persist an inferred target.

- Clean worktree: continue only for `CURRENT` or `AHEAD`; stop for remote differences, unknown target, detached HEAD, or command errors
- Dirty worktree: continue for `CURRENT` or `AHEAD` after confirming the task belongs with the existing changes; remote problems are visible warnings, update is prohibited, and continue only related work
- Detached HEAD, invalid repository, and local Git failures stop even when dirty
- Do not rerun in the same task unless the repository or branch changes, the user requests it, or an approved update succeeds

The full `local` value is the task's observed local baseline. The handoff also has a logical `remoteFreshness` value:

- `confirmed` for `CURRENT`, `AHEAD`, or successful `UPDATED`
- `unconfirmed` for dirty remote warnings, unavailable remote, missing upstream, or other unsuccessful freshness checks

The CLI keeps its existing output and exit codes. Codex should carry this handoff to downstream Skills without rerunning the remote check. A local SHA with `remoteFreshness: unconfirmed` is usable for reading local code but cannot refresh metadata such as Java `.codex/project-guidance.md` baselines.

Skip this workflow for ordinary explanations, immutable commit/PR/tag analysis, no repository, or a candidate that is not a Git worktree. Do not mention the Skill when it is skipped.

## Report Every Result

After every check or update, visibly report the repository, branch, remote target, status, short commit, dirty state when relevant, reason for failures, and next action. For dirty remote warnings, say that freshness is unconfirmed, related existing work may continue, and update is prohibited.

## Update Only After Approval

An implementation request does not authorize updating the repository. For a clean worktree, run update only after explicit approval for the reported repository and branch:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" update --repo "<repository>"
```

Update must reject staged, tracked, or untracked changes, detached HEAD, missing upstream, divergence, rewrites, and remote movement. It may only fetch the selected branch and fast-forward. Never stash, rebase, reset, force, create a merge commit, discard changes, switch branches, or set upstream.

After `UPDATED`, discard old conclusions, reread repository instructions and relevant source, and restart planning or implementation. In a mode that prohibits mutation, defer update even after approval. If update fails, stop after that attempt.

## Script Contract

Read [README.md](README.md) for exact CLI statuses and installation. `check` uses `git ls-remote` and does not modify refs, index, worktree, or `FETCH_HEAD`. Exit `0` means current, already contains remote, or update succeeded; `1` means action is needed; `2` means input, Git, network, or environment error. Interpret `check` together with its dirty field and the policy above.
