---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic; excludes formal code-reviewer and commit-gate workflows.
---

# Java Backend Code Quality

Use for Java backend creation, modification, or review. Apply the core gate to every changed production and test source, then load only the references triggered by the code.

## Scope And Authority

Repository instructions and explicit user rules take precedence.

Limit work and findings to current-task changes. Prefer an explicit file, line, commit, or branch; otherwise use staged, unstaged, and untracked Java changes. For a clean worktree, use an explicit baseline or upstream merge-base; ask if neither exists. Ignore unrelated historical, generated, vendored, and third-party code. Read unchanged collaborators as context and report them only when the change activates or regresses their behavior.

A private helper enters scope when the change creates or edits it, or when a changed call site calls it. Inspect an unchanged declaration as context and report a needless abstraction activated by the changed call site. Do not perform formal `code-reviewer` or commit-gate workflows or issue their approval markers.

## Modes And Routing

In implementation mode, identify non-trivial stages, inputs and outputs, ownership, ordering, and failure consequences before coding. Apply the rules while writing code and recheck changed ranges before finishing.

In review mode, report without editing unless fixes are requested. Lead with severity, file, line, evidence, impact, and the smallest correction; connect preferences to concrete behavioral or maintenance cost.

Always apply the core gate below. Load a reference only when its trigger matches:

- Read [references/method-design.md](references/method-design.md) when code adds, edits, extracts, wraps, reuses, or calls an application-defined private helper, introduces deferred execution, or raises a method-granularity question
- Read [references/comments-and-javadoc.md](references/comments-and-javadoc.md) when code adds or changes a class, method, JavaDoc, comment, guard cluster, or non-trivial method body
- Read [references/naming.md](references/naming.md) for generic, state, or collection vocabulary, enum lookups, renames, `normalize` vocabulary, or unclear call-site responsibility; do not load it for otherwise clear identifiers
- Read [references/exception-communication.md](references/exception-communication.md) when code throws, converts, returns, logs, or documents a failure, or changes a `catch` or `finally` path
- Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) for multi-stage or cross-store behavior, transactions, remote or asynchronous work, retries, caches, compensation, locks, resources, or non-obvious failure policy
- Read [references/checker.md](references/checker.md) for `--base`, `--line-range`, `--exclude`, unclear scope, checker errors, or exact CLI and rule behavior; run ordinary worktree and explicit-path checks directly

## Core Quality Gate

- preserve caller-visible null, empty, absent, disabled, default, and exception semantics
- assign one clear owner for validation, state transitions, persistence, cleanup, and delayed work; keep ordering that protects compatibility, idempotency, security, transactions, and failure isolation
- do not hide meaningful I/O, mutation, retry, fallback, compensation, or cleanup inside an apparently pure calculation or condition
- make the receiver, method name, arguments, return type, and result use reveal the concrete subject, action, result, and caller-relevant side effects. Do not introduce application-defined `normalize` vocabulary, generic shape-only names, ambiguous enum lookups, or collection names that hide type, cardinality, state, key relation, or duplicate policy
- require JavaDoc for every public method and every application-defined method that owns an independent business action or processing stage, regardless of visibility, body length, linearity, or a clear name. Exempt only inherited or generated contracts and private helpers with no independent semantics
- add top-level intent comments when names and types do not reveal a stage's reason, precondition, consumer, order, compatibility rule, or failure consequence. Treat adjacent calls as separate stages when responsibility, handoff, side effects, ordering, or failure boundaries differ
- run the inline-substitution test for every in-scope private helper. Prefer compact logic at the call site when it exposes useful inputs, field sources, null handling, the real delegate, or fixed error details; call count, DRY, JavaDoc, or a clear helper name never proves extraction is better
- treat changed `try-catch-finally` code as a behavioral boundary. Immediately before fallback, degradation, retry, suppression, continuation, compensation, or exception conversion, comment what failed, what happens next, and which guarantee is preserved or skipped; transparent direct rethrows are exempt
- ensure every caller-visible error is truthful for every condition reaching it. When failure reasons differ in error category or effective recovery action, preserve the reason and split the branch, error, or typed failure instead of polishing one combined message
- separate caller messages, internal diagnostics, and control-flow comments. Align error code, exception type, message, and actual behavior; never expose raw downstream errors or sensitive implementation details
- Java comments, including JavaDoc and body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations and report every changed-scope violation

## Verification And Findings

Test changed input, output, absence, failure, and state semantics. Run `scripts/check_java_backend_style.py` for the selected worktree or paths. Never claim tests passed when compilation failed or did not start. Separate confirmed facts, supplied configuration, inference, and runtime assumptions.

Use `P0` for data loss, security exposure, or system-wide outage risk; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics likely to cause defects, misleading recovery, unsafe disclosure, or unsafe maintenance; and `P3` for local clarity or deterministic style. Detailed severity rules live with their owning reference.

Before closing, recheck scope, caller-visible semantics, names, method design, JavaDoc, stage and guard comments, behavior-changing catches, error cause and recovery alignment, internal diagnostics, applicable lifecycle rules, tests, and checker output. State residual risks when no findings remain.
