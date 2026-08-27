---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic; excludes formal code-reviewer and commit-gate workflows.
---

# Java Backend Code Quality

Use this skill whenever a task creates, modifies, or reviews Java backend code. Apply the core rules to every changed Java production and test source. Apply deeper contract and lifecycle checks only when the changed behavior needs them.

## Scope And Authority

Read repository instructions before acting. Explicit user and repository rules override this skill when they conflict.

Keep implementation and findings inside the current task surface. Prefer an explicit file, line, commit, or branch range; otherwise use the current worktree changes. If the worktree is clean, use an explicit baseline or a derivable upstream merge-base; if neither can be established, ask for a baseline instead of guessing. Include staged, unstaged, and untracked Java files when reviewing the worktree. Ignore unrelated historical code, generated sources, vendored code, and third-party code. Read unchanged callers and collaborators as context, but report unchanged code only when the current change directly activates or regresses it.

This skill does not perform a formal `code-reviewer` or commit-gate workflow and does not issue their approval markers.

## Apply The Skill

### Implementation mode

Before writing a non-trivial method, identify its stages, inputs, outputs, ownership, ordering, and failure consequences. Apply names, structure, JavaDoc, stage comments, exception handling, and tests while implementing. Re-read the changed ranges and check stage coverage before closing.

### Review mode

Report actionable findings without editing unless the user requests fixes. Lead with severity, file, line, evidence, impact, and the smallest correction. Do not report a preference without a concrete maintenance or behavioral cost.

### Complexity routing

Always inspect changed Java code for caller-visible correctness, names, comments, exception behavior, method design, formatting, and tests. Then load only the references needed by the change:

- Read [references/naming.md](references/naming.md) when classes, methods, fields, parameters, local variables, or enums are added or renamed, a generic action is under review, or the call site cannot reveal the complete responsibility
- Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) when behavior crosses stages, stores, transactions, remote calls, asynchronous work, retries, caches, compensation, locks, resource lifecycles, or a non-obvious caller-visible failure policy
- Read [references/checker.md](references/checker.md) before running the deterministic checker or when exact CLI, changed-scope, or rule-identifier behavior matters

Do not load any reference merely because it exists. Keep the task's code, tests, and relevant repository context ahead of optional guidance.

## Core Correctness And Design

- preserve caller-visible null, empty, absent, disabled, default, and exception semantics
- identify one owner for validation, state transitions, persistence, cleanup, and delayed work
- keep ordering that protects compatibility, idempotency, security, transaction boundaries, and failure isolation
- do not hide meaningful I/O, mutation, retry, fallback, or cleanup inside an apparently pure calculation or condition
- keep a method when it owns a stable stage or policy; split methods that mix orchestration, transformation, side effects, and cleanup into an opaque block
- inline wrappers that only rename delegation, add a routine null check, or construct a fixed exception without adding policy; avoid generic context, builder, coordinator, or helper abstractions created only to reduce line count
- use intermediate values and parameters that expose a real stage or contract, not generic carriers created only to reduce line count
- use deferred functions only when locking, retry, transaction, caching, or fallback genuinely requires deferred execution; verify they run only as intended and preserve exception semantics
- remove always-fixed booleans, use enums for stable states with distinct behavior, and group parameters only when they form a cohesive value
- before extracting, keep rejection conditions and meaningful local duplication visible when another jump would hide the rule; reuse alone is not sufficient

## Naming

Read the naming reference for detailed patterns and exemptions. At minimum, a caller reading only the receiver, method name, arguments, return type, and result use must understand the concrete subject, action, result, and caller-relevant side effects. Prefer familiar business vocabulary over translated abstractions or AI-sounding generalities.

Generic verbs such as `build`, `convert`, `find`, `validate`, `save`, `process`, and `handle` need a concrete product, subject, rule, or outcome. `Batch`, `List`, `Data`, `Info`, `Context`, `Item`, and `Result` describe shape only. A method name that hides persistence, remote I/O, transactions, compensation, fallback, or absence behavior is a finding even when its return type looks correct.

For enum lookups, follow the current repository convention and make both the result and lookup field visible, such as `getByCode` or `getDescByCode`. A bare `find` does not expose the key. Make the repository's `null`, `Optional`, or throwing-on-missing contract explicit; do not change that contract only to satisfy naming.

## Comments And Formatting

Treat class JavaDoc, method JavaDoc, top-level stage comments, and branch-local comments as separate scopes:

- class JavaDoc describes responsibility and collaboration boundaries; public methods and methods owning a caller-visible contract, lifecycle, or non-obvious behavior need JavaDoc describing meaningful inputs, outputs, failures, and lifecycle ownership; getters, setters, simple delegation, fixed exception construction, and self-evident private helpers may be exempt
- non-trivial methods need concise top-level intent comments for stages whose reason, precondition, result consumer, ordering, compatibility choice, or failure consequence is not clear from names and types
- always inspect independent-source comparisons, filtering or reshaping, compatibility paths, ordered steps, and calls with hidden policy or side effects
- treat adjacent calls as separate stages when they switch processor responsibility, pass an intermediate result to another operation, or have different ordering, side-effect, or failure boundaries; add one intent comment immediately before each such stage, even when the receiver is the same
- one comment may cover a cohesive sequence only when the calls share the same purpose, precondition, result consumer, and failure semantics; a comment for a preparation or mapping call cannot also stand for a later execution, persistence, or response call
- three or more terminating entry guards need one comment before the first guard explaining the validation boundary; do not repeat a comment on every `if`
- a smaller validation cluster still needs a comment when it crosses input, configuration, state, security, or error-classification boundaries
- comments must explain why, boundary, downstream use, or consequence; do not translate obvious syntax into prose
- do not add line comments for obvious assignments, pure predicates, getters, or direct calls whose complete action contract is visible
- JavaDoc, logs, catch-local comments, and nested comments do not substitute for a separate top-level stage comment
- update or remove comments when behavior or ownership moves, and do not call an operation atomic unless its actual primitive, lock, or compare-and-set contract provides that guarantee

Java comments, including JavaDoc and body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations. Report every changed-scope violation even when its severity is only `P3`.

## Exception Paths

Inspect every changed `try-catch-finally` as a behavioral boundary. Catch the intended exception, preserve unexpected failures, keep caller-relevant error categories distinct, remove catch-log-rethrow blocks that add no context or ownership, and prevent cleanup or recovery from masking the original failure.

When a `catch` changes behavior through fallback, degradation, retry, suppression, continuation, compensation, or exception conversion, add a local comment immediately before that behavior. State what failed, what happens next, and which guarantee is skipped or preserved. JavaDoc, a comment before `try`, a log message, or a vague helper name cannot replace it. A transparent direct rethrow is exempt, and no mechanical comment is required for an unchanged catch or every return.

## Verification And Findings

Map tests to changed input, output, absence, failure, and state semantics. Run the deterministic checker using [references/checker.md](references/checker.md) for the selected files or ranges. Never claim tests passed when compilation failed or tests did not start. Distinguish confirmed behavior, supplied configuration, inference, and unverified runtime assumptions; when no findings remain, state that explicitly and list residual risks or verification gaps.

Use `P0` for data loss, security exposure, or system-wide outage risk; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics likely to cause defects or unsafe maintenance; and `P3` for local clarity or deterministic style. Punctuation, method spacing, and wrapping findings are at most `P3`. Before closing, recheck scope, names, stage comments, guards, behavior-changing catches, applicable lifecycle rules, tests, and checker output.
