# Local Project Guidance

Read this reference only for a Java implementation task that touches logging, dependencies or utilities, remote calls, exception handling, formatting, or build verification. The optional `.codex/project-guidance.md` file is a local reference for stable project hints. It reduces repeated discovery but never replaces current repository evidence.

## Authority And Scope

Use this order of evidence:

1. user decisions, repository instructions, and published project contracts
2. current build files, configuration, source, tests, and reproducible behavior
3. version-matched official external documentation
4. local project guidance
5. generic Skill recommendations

Every guidance entry is advisory and cannot create a `P2` or `P3` finding by itself. Formatting and naming preferences remain suggestions unless a stronger source makes them required. Store only durable preferences and starting points, such as the preferred logger, approved utility families, expected remote wrapper, or verification commands. Do not store class lists, call graphs, field meanings, dependency versions, module layouts, or other code facts that change with implementation. Put enforceable rules in `AGENTS.md` or formal project documentation.

A named utility, logger, or wrapper is a permitted lookup hint, not a cached API contract. Do not store method signatures, accepted values, behavior descriptions, or concrete API invocation recipes. Before using the hint, check the current receiver and relevant implementation or dependency API.

In `Build And Verification`, distinguish the normal build or test entry point from environment-dependent options. Offline mode requires the necessary artifacts to be cached and no dependency refresh to be needed; do not make it the default merely because one run succeeded offline. Record cache assumptions or skipped build/test steps with their applicability conditions, and report resulting verification limits.

## Discover Or Offer The File

Look only for `<repository>/.codex/project-guidance.md`.

- If it exists, read frontmatter and level-two headings first, then read only sections relevant to the task
- A missing, empty, or unverified relevant section is not confirmed by the file's existence or another section's baseline. Perform targeted discovery for that area; if stable hints would help, ask once whether to add or refresh that section, unless the task already has the necessary approval. If declined, continue using current evidence without repeating the offer
- If it is absent, ask once when the task touches one of the sections below and the user is implementing Java code. This also applies when the trigger appears after implementation has started: pause before editing the newly affected area and re-evaluate the relevant sections
- If the user declines, continue with normal targeted discovery and do not ask again during the task
- Do not ask in review mode, explanatory questions, ordinary local style changes, or tasks without a confirmed Git worktree
- Never create or refresh the file without explicit approval

Relevant sections are `Logging`, `Dependencies And Utilities`, `Remote Calls`, `Exception Handling`, `Formatting And Naming`, and `Build And Verification`. A simple rename, comment-only change, local branch adjustment, or ordinary CRUD change does not by itself require initialization.

When initialization is approved, first confirm which relevant sections and stable hints should be recorded. For `Logging`, this may include the logger entry point, log ownership, payload policy, or a masking/redaction convention only when repository evidence or the user confirms one. Do not add a masking requirement merely because the file is being created. Use this shape and omit empty sections only when the user prefers:

```markdown
---
schema_version: 2
verified_commits:
  Logging: <full SHA>
  Dependencies And Utilities: <full SHA>
  Remote Calls: <full SHA>
  Exception Handling: <full SHA>
  Formatting And Naming: <full SHA>
  Build And Verification: <full SHA>
---

# Project Guidance

Local reference hints only. Current repository evidence and formal instructions take precedence.

## Logging

## Dependencies And Utilities

## Remote Calls

## Exception Handling

## Formatting And Naming

## Build And Verification
```

Register the path in the Git local exclude file without changing `.gitignore`:

```text
git rev-parse --git-path info/exclude
git check-ignore -v --no-index .codex/project-guidance.md
git ls-files --error-unmatch -- .codex/project-guidance.md
```

The first command identifies the correct exclude file, including linked worktrees. The second proves that the path matches an exclude rule. The third must fail with an untracked path before the file can be treated as local-only. A successful `git ls-files` means the file is tracked; stop and tell the user instead of silently relying on it as private guidance.

## Version And Baseline Handling

`schema_version: 2` uses an independent `verified_commits` entry for each section. Refresh only sections that were rechecked and approved; refreshing Logging must not mark Dependencies And Utilities as current. A missing or unknown version is unverified: read headings and safe human context only, then verify current evidence before relying on any section.

Version 1 files with one `verified_commit` are legacy input. The commit may guide a focused migration check, but it must not be copied automatically to every section's v2 baseline. Ask before rewriting the metadata.

Reuse the full `local` commit from `$git-latest-code-check`; do not rerun the remote check. `CURRENT`, `AHEAD`, or `UPDATED` confirms remote freshness and may coexist with `dirty=true`. Read status, freshness, and dirty state separately: a warning with `remoteFreshness=unconfirmed`, a remote error, or missing upstream may provide a local reading SHA but cannot advance any guidance baseline. Unrelated ordinary business edits do not by themselves block an approved refresh of a reverified section at the confirmed task `local`.

A section baseline is valid only if its recorded SHA resolves to a local commit and is an ancestor of the task `local`. Check with `git cat-file -e "<sha>^{commit}"` and `git merge-base --is-ancestor "<sha>" "<local>"`. A missing, malformed, unresolvable, or non-ancestor SHA makes that section unverified. Verify the relevant current infrastructure directly; an unavailable or empty diff is not proof of freshness. Do not fetch merely to validate an old hint's SHA. `validate_project_guidance.py` checks metadata shape only: its `VALID` result does not establish commit existence, ancestry, or current applicability.

For a section with a valid baseline, inspect committed paths changed after that section's SHA through the task baseline, plus staged, unstaged, and untracked paths. Changes to any-layer `pom.xml`, `.mvn/**`, `build.gradle*`, `settings.gradle*`, `gradle.properties`, `gradle/**`, lockfiles, logging configuration, shared clients, wrappers, serializers, or error infrastructure invalidate the related sections. Changes committed by others after the section baseline also invalidate it; current task changes invalidate it even when the build files are unchanged.

Invalidation means targeted verification, not a full repository scan. Read the changed descriptor or infrastructure and a representative current use. After verification, explain which sections are confirmed or outdated and ask before refreshing their commit entries. Do not advance a section while its relevant configuration or infrastructure is uncommitted, even when remote freshness is confirmed. Refresh only the reverified and authorized section; preserve other sections' commits.

## Load Only Relevant Sections

- logger or diagnostic changes: `Logging`
- library, utility, or dependency changes: `Dependencies And Utilities`
- HTTP, RPC, Feign, or SDK changes: `Remote Calls`, plus `Logging` or `Exception Handling` when applicable
- caller-visible failures or error mapping: `Exception Handling`
- genuine style ambiguity: `Formatting And Naming`
- build, test, lint, or run commands: `Build And Verification`

Read the affected receiver, import, configuration, or version declaration to confirm that a hint applies. Do not load every section because the file exists.
