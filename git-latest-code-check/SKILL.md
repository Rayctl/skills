---
name: git-latest-code-check
description: Check the development target of an already-confirmed Git worktree before substantive code work, safely fast-forward a clean branch when permitted, and verify an explicit existing destination before pushing. Do not discover repositories.
---

# Git Latest Code Check

Use the development check once per task before substantive code planning, creation, or modification in each already-confirmed Git worktree, and use push verification before every actual push. The caller must first verify the candidate with `git rev-parse --is-inside-work-tree`; this Skill does not discover repositories or search unrelated directories.

## Check Before Work

Run the read-only check:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" check --repo "<repository>"
```

Resolve the configured upstream from `branch.<name>.remote` and `branch.<name>.merge`, even if its cached tracking ref was pruned. The remote branch must exist. Without an upstream, ask the user to specify an existing remote target; never infer one or create/restore a branch.

Use `--remote` and `--branch` together for a user-specified target. Before invoking with an explicit target, read the configured upstream. If the two differ, visibly report both and ask which target to use, unless the user already explicitly confirmed that choice in this task. After confirmation, retain the explicit pair in subsequent checks and updates; never modify upstream configuration. The CLI accepts an explicit pair as the caller's confirmed selection; it does not perform an interactive choice.

- Always stop for `REMOTE_BRANCH_MISSING`, `NO_UPSTREAM`, `GIT_OPERATION_IN_PROGRESS`, `DETACHED`, invalid input/repository, and local Git failures, even when dirty. Report the reason and ask for the correct existing target or resolution of the unfinished operation. Do not switch branches, abort operations, or recreate deleted branches automatically.
- Clean worktree: continue for `CURRENT`; for `AHEAD`, report both commits and the additional local commits (`git log <remote-sha>..HEAD`) and confirm they belong to the task. A clean worktree alone does not establish commit ownership. For `BEHIND`, announce and automatically attempt one safe fast-forward update. Stop for `REMOTE_DIFFERS`, `DIVERGED`, or `REMOTE_UNAVAILABLE`.
- Dirty worktree: for `CURRENT` or `AHEAD`, confirm the task belongs with the existing changes and commits. Only `BEHIND`, `DIVERGED`, `REMOTE_DIFFERS`, and temporary `REMOTE_UNAVAILABLE` may become visible warnings; freshness remains unconfirmed, update is prohibited, and only existing related work may continue. Unknown targets and deleted branches never qualify for this exception.
- Do not rerun development checks in the same task unless the repository/branch/selected target changes, the user requests it, or an update succeeds. Push verification is separate and runs before every actual push.

`BEHIND` is established only when the observed remote commit exists locally and local `HEAD` is its ancestor. If that object is absent, `check` returns `REMOTE_DIFFERS`; do not fetch during a read-only check or label this as `BEHIND`. Request approval for a single safe update attempt on a clean worktree.

The full `local` value is the task's observed local baseline. After a successful update, replace the old baseline with the result's full `local` value. The handoff also has a logical `remoteFreshness` value:

- `confirmed` for `CURRENT`, `AHEAD`, or successful `UPDATED`
- `unconfirmed` for permitted dirty freshness warnings or unavailable remote; blocking results cannot hand off permission to continue

Codex should carry this handoff to downstream Skills without rerunning the remote check. A local SHA with `remoteFreshness: unconfirmed` is usable for permitted related work but cannot refresh metadata such as Java `.codex/project-guidance.md` baselines. Push verification does not replace this development baseline.

Skip this workflow for ordinary explanations, immutable commit/PR/tag analysis, no repository, or a candidate that is not a Git worktree. Do not mention the Skill when it is skipped.

## Report Every Result

Before every update invocation, visibly announce the repository, branch, remote target, actual observed status, available local and remote short commits, the clean-worktree precondition, and that only one safe update attempt will run: fetch the selected branch, then use `git merge --ff-only` if fast-forward is possible. Use `BEHIND` only when observed; an approved `REMOTE_DIFFERS` attempt must say the relationship needs verification.

After every `check`, `update`, or `verify-push`, visibly report the result before continuing or stopping. Tool output is not user-visible notification; successful execution does not mean the user has been informed.

- For `CURRENT`, `AHEAD`, or `UPDATED`, give a concise repository/branch/target/status/short-commit summary; mention dirty state when present. For `AHEAD`, include both local and remote commits, explain that local history contains additional commits, and assess their task ownership.
- For every failure or command/tool exception, report status (`ERROR` if none), available target and commit information, dirty state (unknown if unavailable), reason, next action, and any required user choice. A missing branch must explicitly stop development and request the correct existing target; do not call it a temporary access failure.
- For permitted dirty freshness warnings, say freshness is unconfirmed, only existing related work may continue, and update is prohibited. Push failures never qualify for warning-only continuation.
- Update may fail after moving `HEAD`; report the latest known local commit and never claim the checkout is unchanged without evidence. After `UPDATED`, refresh the baseline and reread rules/source before continuing. After update failure, report recovery and stop without retry.

## Safe Fast-Forward Update

When `check` reports `BEHIND` with `dirty: false`, the user-approved policy authorizes exactly one automatic update for the reported repository and remote branch. Announce the update first, then run:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" update --repo "<repository>"
```

Use exactly the same repository and target as the check. If it used explicit `--remote` and `--branch`, pass the same pair to `update`. Restart the check if repository, branch, or selected target changes.

Do not automatically update `REMOTE_DIFFERS`, `DIVERGED`, unknown/missing targets, unfinished operations, detached HEAD, or errors. For a direct update request outside the clean `BEHIND` path, require explicit approval for the reported repository and existing target and announce the action first. `REMOTE_DIFFERS` remains subject to approval.

Update rejects staged, tracked, or untracked changes, unfinished Git operations, detached HEAD, unresolved/missing targets, divergence, rewrites, and concurrent local or remote changes. A confirmed explicit existing target works without upstream. Remote deletion and access failure are distinguished before update, after fetch failure, and during final verification. No automatic retry. It may only fetch the selected branch and fast-forward. Never stash, rebase, reset, force, create a merge commit, discard changes, switch branches, or set upstream.

After `UPDATED`, discard old conclusions, reread repository instructions and relevant source, and restart planning or implementation. In a mode that prohibits mutation, defer the automatic update and report why. If update fails, stop after that attempt.

## Script Contract

Read [README.md](README.md) for statuses and installation. `check` and `verify-push` use `git ls-remote`; neither changes HEAD, index, refs, `FETCH_HEAD`, operation markers, configuration, or worktree. Optional locks and lazy fetch are disabled. Exit `0` means `CURRENT`/`AHEAD` or successful `UPDATED`; `1` requires action; `2` indicates input, Git, access, or environment errors. Interpret development `check` with the policy above.

## Verify Before Every Push

Before each actual push, identify the exact remote and destination and run:

```text
py -3 "<skill-directory>\scripts\git_latest_code.py" verify-push --repo "<repository>" --remote "<remote>" --branch "<destination>"
```

This supports current `HEAD` pushed to one existing branch only. Both target arguments are required. It reads `git remote get-url --push --all` and queries the actual push address, which may differ from the fetch address. Multiple addresses, complex refspecs, or multiple destinations require the user to choose a single target; do not silently choose or rewrite configuration. Explicit task authorization for a concrete destination already supplies that choice. The push destination may deliberately differ from upstream; report it and do not change upstream.

Only `CURRENT` and `AHEAD` permit the authorized push to proceed. Report the result in conversation before pushing. All failures stop the push, even with a dirty worktree. Dirty state alone does not prohibit pushing already committed content. If objects are missing, `REMOTE_DIFFERS` means comparison needs further verification; this command must not fetch. If the destination changes or an update finishes, verify again before pushing. Never create or restore a missing remote branch as an exception.

The command also rechecks local state after the remote query. Concurrent HEAD/branch changes return `WORKTREE_CHANGED`; newly started Git operations still block. Report the latest local state and verify again after the concurrent work is resolved.

This check neither authorizes an otherwise unauthorized push nor proves write permission or protected-branch acceptance. Follow repository PR rules and report the actual push result. It observes a moment in time; do not force push to override a later rejection.
