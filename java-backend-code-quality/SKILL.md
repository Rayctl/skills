---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic.
---

# Java Backend Code Quality

Use for Java backend creation, modification, or review. Apply the core rules to task-owned production and test changes, then load only triggered references.

## Scope And Authority

Repository instructions and explicit user rules take precedence.

Base material decisions on authoritative contracts and repository evidence, not recommendations presented as facts. Ask only when unresolved evidence materially changes a public contract, data or security behavior, diagnostics, or architecture.

Limit findings to an explicit task file, range, commit, or branch; otherwise use staged, unstaged, and untracked Java changes. For a clean worktree, require a baseline or upstream merge-base. Ignore unrelated historical, generated, vendored, and third-party code; report unchanged collaborators only when the change activates or regresses them.

A private helper, field, or constant enters scope when created or edited, or when a changed use site relies on it as a compact abstraction. Inspect unchanged declarations only as context for that changed use.

## Modes And Routing

In implementation mode, treat the named class, method, or field as the starting point rather than the change boundary. Before editing existing behavior, map its semantic neighborhood: trigger and call path, data sources and related invariants, transformations, consumers, side effects, diagnostics, failures, and tests. Apply the structure-choice triggers before editing production behavior: pause with simple and structured options only when a new pattern has material current benefit. After coding, account for each discovered dependency as changed or deliberately preserved, then recheck changed ranges.

In review mode, do not edit unless asked. Lead with severity, location, evidence, impact, and the smallest correction. Skip the optional structure-choice advisory.

Always apply the core rules below. Load a reference only when its trigger matches:

- Read [references/method-design.md](references/method-design.md) for application private helpers, compact reuse fields or constants, deferred execution, or abstraction-granularity questions
- Read [references/structure-choice.md](references/structure-choice.md) in implementation mode for growing implementations or branches, varying repeated flows, scattered creation, or runtime-selected behavior
- Read [references/comments-and-javadoc.md](references/comments-and-javadoc.md) for changed classes, methods, JavaDoc, comments, guard clusters, or non-trivial method bodies
- Read [references/naming.md](references/naming.md) for generic, state, or collection vocabulary, enum lookups, renames, `normalize`, or unclear call-site responsibility
- Read [references/exception-communication.md](references/exception-communication.md) for changed failure behavior, messages, logs, `catch`, or `finally`
- Read [references/remote-calls.md](references/remote-calls.md) for changed HTTP, Feign, RPC, or external SDK calls, logging, error parsing, mapping, or returned failures
- Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) for multi-stage or cross-store behavior, transactions, asynchronous work, retries, caches, compensation, locks, resources, or non-obvious failure policy
- Read [references/control-flow.md](references/control-flow.md) for changed ternaries, branches, loops, or long expressions
- Read [references/evidence-and-verification.md](references/evidence-and-verification.md) when modifying existing behavior or data semantics, evidence is missing or conflicting, legacy logic lacks an explanation, or tools change files after editing
- Read [references/checker.md](references/checker.md) for advanced scope options, unclear scope, errors, or exact checker behavior

## Core Quality Rules

- preserve caller-visible null, empty, absent, disabled, default, and exception semantics
- trace changed values through validation, mapping, serialization, persistence, remote calls, caches, logs, errors, and outputs. Treat values as related when they jointly express one business fact, even without a direct reference
- assign one clear owner for validation, state transitions, persistence, cleanup, and delayed work; keep ordering that protects compatibility, idempotency, security, transactions, and failure isolation
- do not hide meaningful I/O, mutation, retry, fallback, compensation, or cleanup inside an apparently pure calculation or condition
- make call sites reveal the subject, action, result, and caller-relevant side effects. Avoid application-defined `normalize`, shape-only names, ambiguous enum lookups, and collection names that hide cardinality, state, key relation, or duplicate policy
- require JavaDoc for every public method and every application-defined method that owns an independent business action or processing stage, regardless of visibility, body length, linearity, or a clear name. Exempt only inherited or generated contracts and private helpers with no independent semantics
- add top-level intent comments when names and types do not reveal a stage's reason, precondition, consumer, order, compatibility rule, or failure consequence. Treat adjacent calls as separate stages when responsibility, handoff, side effects, ordering, or failure boundaries differ
- compare compact private helpers, fields, and constants with writing their logic or value at the use sites. Prefer the form that exposes inputs, null handling, the real delegate, or error text; reuse count, DRY, JavaDoc, or a clear name never proves extraction is better
- treat changed `try-catch-finally` code as a behavioral boundary. Immediately before fallback, degradation, retry, suppression, continuation, compensation, or exception conversion, comment what failed, what happens next, and which guarantee is preserved or skipped; transparent direct rethrows are exempt
- ensure every caller-visible error is truthful for every condition reaching it. When failure reasons differ in error category or effective recovery action, preserve the reason and split the branch, error, or typed failure instead of polishing one combined message
- separate caller messages, internal diagnostics, and control-flow comments. Align error code, exception type, message, and actual behavior
- for third-party calls, distinguish business rejection, HTTP or RPC failure, invalid response, and transport failure. Preserve structured business-error details in a deliberate caller or diagnostic path; do not invent error mappings or logging and disclosure policy when repository evidence is absent
- keep ternaries for short pure value choices only; when null handling, comparison, method calls, side effects, or multiple operations make the condition dense, prefer a braced `if`
- brace every `if`, `else`, `for`, `while`, and `do while` body. Follow the repository formatter and wrap only when the line exceeds the local limit or becomes harder to scan
- Java comments, including JavaDoc and body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations and report every changed-scope violation

## Verification And Findings

Test changed input, output, absence, failure, and state semantics. Run `scripts/check_java_backend_style.py`. Never claim tests passed when compilation failed or did not start; separate facts, configuration, inference, and runtime assumptions.

After a formatter, generator, test fix, hook, or tool changes files, reread affected files and the final diff, recompute reference triggers, and rerun invalidated checks. Report the observed final state, not an intended patch or stale snapshot.

Use `P0` for data loss, security exposure, or system-wide outage risk; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics likely to cause defects, misleading recovery, unsafe disclosure, or unsafe maintenance; and `P3` for local clarity or deterministic style. Detailed severity rules live with their owning reference.

Before closing, recheck scope, caller semantics, names, method design, JavaDoc, intent comments, catches, error alignment, diagnostics, applicable remote-call and lifecycle rules, tests, and checker output. State residual risks.
