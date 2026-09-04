---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic; excludes formal code-reviewer and commit-gate workflows.
---

# Java Backend Code Quality

Use for Java backend creation, modification, or review. Apply core rules to every changed production and test source; add contract and lifecycle checks only when behavior requires them.

## Scope And Authority

Repository instructions and explicit user rules take precedence.

Limit work and findings to current-task changes. Prefer an explicit file, line, commit, or branch; otherwise use staged, unstaged, and untracked Java changes. For a clean worktree, use an explicit baseline or upstream merge-base; ask if neither exists. Ignore unrelated historical, generated, vendored, and third-party code. Read unchanged collaborators as context and report them only when the change activates or regresses behavior.

Do not perform formal `code-reviewer` or commit-gate workflows or issue their approval markers.

## Apply The Skill

### Implementation mode

Before non-trivial code, identify stages, inputs and outputs, ownership, ordering, and failure consequences. Apply names, structure, JavaDoc, stage comments, exception handling, and tests while coding; recheck changed ranges and stage coverage.

### Review mode

Unless fixes are requested, report without editing. Lead with severity, file, line, evidence, impact, and the smallest correction; tie preferences to concrete maintenance or behavioral cost.

### Complexity routing

Always inspect caller-visible correctness, names, comments, exceptions, method design, formatting, and tests. Load only references whose trigger applies:

- Read [references/naming.md](references/naming.md) for generic vocabulary, enum lookups, renames, or unclear call-site responsibility, not otherwise clear new identifiers
- Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) for multi-stage or cross-store behavior, transactions, remote or asynchronous work, retries, caches, compensation, locks, resources, or non-obvious failure policy
- Read [references/checker.md](references/checker.md) for `--base`, `--line-range`, `--exclude`, unclear scope, checker errors, or exact CLI and rule behavior; run ordinary worktree and explicit-path checks directly

## Core Correctness And Design

- preserve caller-visible null, empty, absent, disabled, default, and exception semantics
- identify one owner for validation, state transitions, persistence, cleanup, and delayed work
- keep ordering that protects compatibility, idempotency, security, transaction boundaries, and failure isolation
- do not hide meaningful I/O, mutation, retry, fallback, or cleanup inside an apparently pure calculation or condition
- compare extracted and inlined forms for every changed private helper; keep rejection rules and meaningful local duplication visible. Reuse, a second call site, a stable-policy label, or fewer lines do not justify extraction
- inline a helper with one or two explicit source call sites when its body is small and locally readable, even when this duplicates it: one guard plus a simple assignment or call, argument forwarding, a few linear statements, a routine null check, a fixed exception, or one persistence or remote call without owned policy
- retain a helper only when its call-site contract is clear and it isolates non-trivial branching or an algorithm, owns enforceable transaction demarcation, resource lifecycle, side-effect ordering, compensation, or failure policy, or needs separate identity for a framework, annotation, reflection, or serialization contract; verify implicit use and prefer local names plus stage comments for inlined behavior
- use intermediate values and parameters that expose a real stage or contract, not generic carriers created only to reduce line count
- use deferred functions only when locking, retry, transaction, caching, or fallback genuinely requires deferred execution; verify they run only as intended and preserve exception semantics
- remove always-fixed booleans, use enums for stable states with distinct behavior, and group parameters only when they form a cohesive value

## Naming

From only the receiver, method name, arguments, return type, and result use, a caller must understand the concrete subject, action, result, and relevant side effects. Prefer familiar business vocabulary over translated abstractions or AI-sounding generalities.

Generic construction, conversion, lookup, validation, mutation, and orchestration verbs need a concrete subject, product, rule, or outcome; shape words such as `Batch`, `List`, `Data`, `Info`, `Context`, `Item`, and `Result` are insufficient. Names must expose persistence, remote I/O, transactions, compensation, fallback, and absence behavior.

Do not introduce application-defined `normalize`, `normalized`, or `normalizer` identifiers. Name the exact action or result; substituting vague words such as `standardize`, `canonicalize`, `sanitize`, `adjust`, or `process` remains invalid. Keep normalization terminology only for required framework or external signatures and named standards such as Unicode NFC or URI normalization.

Enum lookups must follow repository convention and expose the result, key, and missing-value contract; bare `find` is insufficient.

## Comments And Formatting

Treat class JavaDoc, method JavaDoc, top-level stage comments, and branch-local comments as separate scopes:

- class JavaDoc states responsibility and collaboration boundaries; public methods and non-obvious caller-visible contracts or lifecycles need JavaDoc for meaningful inputs, outputs, failures, and ownership. Exempt self-evident accessors, delegation, fixed exception construction, and trivial private helpers
- keep API contract, Swagger, and field documentation to caller-visible meaning plus non-obvious defaults, fallbacks, compatibility, units, or boundaries; enum codes already exposed by an enum type or `allowableValues` need not be repeated, and omitted detail is a finding only when it creates concrete misuse risk
- non-trivial methods need top-level intent comments where names and types hide a stage's reason, precondition, result consumer, ordering, compatibility choice, or failure consequence; always inspect independent-source comparisons, filtering or reshaping, compatibility paths, ordered steps, and hidden policy or side effects
- treat adjacent calls as separate stages when responsibility changes, an intermediate result is handed off, or ordering, side effects, or failure boundaries differ; comment before each stage even with the same receiver. One comment covers calls only when purpose, precondition, consumer, and failure semantics all match; preparation or mapping cannot also cover execution, persistence, or response work
- three or more terminating entry guards need one comment before the first guard explaining the validation boundary; a smaller cluster also needs one when it crosses input, configuration, state, security, or error-classification boundaries. Do not comment every `if`
- explain why, boundaries, downstream use, or consequences instead of obvious syntax; do not comment self-evident assignments, pure predicates, getters, or direct calls whose complete contract is visible
- JavaDoc, logs, catch-local comments, and nested comments do not substitute for a separate top-level stage comment
- remove stale comments when behavior or ownership moves; call an operation atomic only when its primitive, lock, or compare-and-set contract guarantees it

Java comments, including JavaDoc and body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations. Report every changed-scope violation even when its severity is only `P3`.

## Exception Paths

Treat every changed `try-catch-finally` as a behavioral boundary: catch the intended exception, preserve unexpected failures and caller-relevant error categories, remove context-free catch-log-rethrow blocks, and prevent cleanup or recovery from masking the original failure.

When a `catch` changes behavior through fallback, degradation, retry, suppression, continuation, compensation, or exception conversion, comment immediately before it: state what failed, what happens next, and which guarantee is skipped or preserved. JavaDoc, a pre-`try` comment, log, or vague helper name cannot replace it. Exempt transparent direct rethrows; do not comment unchanged catches or every return mechanically.

## Verification And Findings

Test changed input, output, absence, failure, and state semantics. Run `scripts/check_java_backend_style.py` directly for worktree or explicit-path checks; load its reference only for routed cases. Never claim tests passed when compilation failed or did not start. Separate confirmed facts, supplied configuration, inference, and runtime assumptions; state residual risks when no findings remain.

Use `P0` for data loss, security exposure, or system-wide outage risk; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics likely to cause defects or unsafe maintenance; and `P3` for local clarity or deterministic style. A needless extraction is `P2` when it conceals ordering, side effects, failure policy, or lifecycle ownership, and otherwise `P3` when it only adds navigation cost. Punctuation, method spacing, and wrapping findings are at most `P3`. Before closing, recheck scope, names, stage comments, guards, behavior-changing catches, applicable lifecycle rules, tests, and checker output.
