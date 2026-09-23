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

## Discover Or Offer The File

Look only for `<repository>/.codex/project-guidance.md`.

- If it exists, read frontmatter and level-two headings first, then read only sections relevant to the task
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

Reuse the full `local` commit from the successful `$git-latest-code-check` result. Do not rerun the remote check. `CURRENT`, `AHEAD`, or `UPDATED` means remote freshness is confirmed. A dirty-worktree warning, remote error, missing upstream, or any other unsuccessful check may still provide a local SHA for reading code, but its `remoteFreshness` is `unconfirmed` and it cannot advance any guidance baseline.

For a section with a valid baseline, inspect committed paths changed after that section's SHA through the task baseline, plus staged, unstaged, and untracked paths. Changes to any-layer `pom.xml`, `.mvn/**`, `build.gradle*`, `settings.gradle*`, `gradle.properties`, `gradle/**`, lockfiles, logging configuration, shared clients, wrappers, serializers, or error infrastructure invalidate the related sections. Changes committed by others after the section baseline also invalidate it; current task changes invalidate it even when the build files are unchanged.

Invalidation means targeted verification, not a full repository scan. Read the changed descriptor or infrastructure and a representative current use. After verification, explain which sections are confirmed or outdated and ask before refreshing their commit entries. Do not advance a section while its relevant configuration is uncommitted.

## Load Only Relevant Sections

- logger or diagnostic changes: `Logging`
- library, utility, or dependency changes: `Dependencies And Utilities`
- HTTP, RPC, Feign, or SDK changes: `Remote Calls`, plus `Logging` or `Exception Handling` when applicable
- caller-visible failures or error mapping: `Exception Handling`
- genuine style ambiguity: `Formatting And Naming`
- build, test, lint, or run commands: `Build And Verification`

Read the affected receiver, import, configuration, or version declaration to confirm that a hint applies. Do not load every section because the file exists.
