---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic; excludes formal code-reviewer and commit-gate workflows.
---

# Java Backend Code Quality

Use for Java backend creation, modification, or review. Apply core rules to every changed production and test source; add contract and lifecycle checks only when behavior requires them.

## Scope And Authority

Repository instructions and explicit user rules take precedence.

Limit work and findings to current-task changes. Prefer an explicit file, line, commit, or branch; otherwise use staged, unstaged, and untracked Java changes. For a clean worktree, use an explicit baseline or upstream merge-base; ask if neither exists. Ignore unrelated historical, generated, vendored, and third-party code. Read unchanged collaborators as context and report them only when the change activates or regresses behavior. A private helper enters scope when the change creates or edits it, or when a changed call site calls it; inspect an unchanged declaration as context and report a needless abstraction activated by that call site.

Do not perform formal `code-reviewer` or commit-gate workflows or issue their approval markers.

## Apply The Skill

### Implementation mode

Before non-trivial code, identify stages, inputs and outputs, ownership, ordering, and failure consequences. Apply names, structure, JavaDoc, stage comments, exception handling, and tests while coding; recheck changed ranges and stage coverage.

### Review mode

Unless fixes are requested, report without editing. Lead with severity, file, line, evidence, impact, and the smallest correction; tie preferences to concrete maintenance or behavioral cost.

### Complexity routing

Always inspect caller-visible correctness, names, comments, exceptions, method design, formatting, and tests. Load only references whose trigger applies:

- Read [references/naming.md](references/naming.md) for generic, state, or collection vocabulary, enum lookups, renames, or unclear call-site responsibility, not otherwise clear new identifiers
- Read [references/exception-communication.md](references/exception-communication.md) when changed code throws, converts, returns, logs, or documents a failure, or changes a `catch` or `finally` path
- Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) for multi-stage or cross-store behavior, transactions, remote or asynchronous work, retries, caches, compensation, locks, resources, or non-obvious failure policy
- Read [references/checker.md](references/checker.md) for `--base`, `--line-range`, `--exclude`, unclear scope, checker errors, or exact CLI and rule behavior; run ordinary worktree and explicit-path checks directly

## Core Correctness And Design

- preserve caller-visible null, empty, absent, disabled, default, and exception semantics
- identify one owner for validation, state transitions, persistence, cleanup, and delayed work
- keep ordering that protects compatibility, idempotency, security, transaction boundaries, and failure isolation
- do not hide meaningful I/O, mutation, retry, fallback, or cleanup inside an apparently pure calculation or condition
- run an inline-substitution test for every in-scope private helper: mentally place its body at the main call sites and prefer the form that makes each branch understandable with less navigation
- inline a compact helper regardless of call count when expansion exposes useful inputs, field sources, null handling, the actual delegate, error category, or error message without obscuring the flow. This includes null-check plus predicate wrappers, field extraction followed by delegation, fixed exception factories, argument forwarding, one-expression wrappers, and a few linear statements
- repetition, DRY, a clear name, JavaDoc, centralized wording, a stable-policy label, or fewer lines do not alone justify extraction; allow small local duplication when it preserves call-site evidence
- retain a helper only when hiding non-trivial branching, an algorithm, or low-level mechanics materially lowers call-site cognitive load; when it owns enforceable transaction demarcation, resource lifecycle, side-effect ordering, compensation, or context-dependent failure classification or conversion; or when framework, annotation, reflection, or serialization contracts require a separate identity. A fixed exception code and message alone are not a failure policy
- use intermediate values and parameters that expose a real stage or contract, not generic carriers created only to reduce line count
- use deferred functions only when locking, retry, transaction, caching, or fallback genuinely requires deferred execution; verify they run only as intended and preserve exception semantics
- remove always-fixed booleans, use enums for stable states with distinct behavior, and group parameters only when they form a cohesive value

## Naming

From only the receiver, method name, arguments, return type, and result use, a caller must understand the concrete subject, action, result, and relevant side effects. Prefer familiar business vocabulary over translated abstractions or AI-sounding generalities.

Generic construction, conversion, lookup, validation, mutation, and orchestration verbs need a concrete subject, product, rule, or outcome; shape words such as `Batch`, `List`, `Data`, `Info`, `Context`, `Item`, and `Result` are insufficient. Names must expose persistence, remote I/O, transactions, compensation, fallback, and absence behavior.

Do not introduce application-defined `normalize`, `normalized`, or `normalizer` identifiers. Name the exact action or result; substituting vague words such as `standardize`, `canonicalize`, `sanitize`, `adjust`, or `process` remains invalid. Keep normalization terminology only for required framework or external signatures and named standards such as Unicode NFC or URI normalization.

Use state words only for values actually in that state: `candidate` requires later selection and a named subject. Application-internal collection variables end in `List`, `Set`, or `Map`; put subject, state, source, and key relationship before the suffix (`requestedAppList`, `appByCodeMap`, `appsByStatusMap`), preserve singular or plural value cardinality, and do not rename external contracts solely for a suffix. If one query result is looked up at least twice by the same stable key with one value per key, build one map instead of repeated scans or a trivial helper. Retain the collection when order, duplicates, or one traversal matters; duplicate keys must be impossible, rejected, grouped, or resolved deterministically.

Enum lookups must follow repository convention and expose the result, key, and missing-value contract; bare `find` is insufficient.

## Comments And Formatting

Treat class JavaDoc, method JavaDoc, top-level stage comments, and branch-local comments as separate scopes:

- class JavaDoc states responsibility and collaboration boundaries. Every public method and every application-defined method that owns an independent business action or processing stage needs method JavaDoc, regardless of visibility, a linear body, or an already clear name. Explain the purpose plus meaningful timing, inputs, outputs, side effects, failures, or downstream use instead of restating the name. Exempt only generated or inherited contracts and private helpers with no independent semantics, such as self-evident accessors, pure delegation, or fixed exception construction
- keep API contract, Swagger, and field documentation to caller-visible meaning plus non-obvious defaults, fallbacks, compatibility, units, or boundaries; enum codes already exposed by an enum type or `allowableValues` need not be repeated, and omitted detail is a finding only when it creates concrete misuse risk
- non-trivial methods need top-level intent comments where names and types hide a stage's reason, precondition, result consumer, ordering, compatibility choice, or failure consequence; always inspect independent-source comparisons, filtering or reshaping, compatibility paths, ordered steps, and hidden policy or side effects
- treat adjacent calls as separate stages when responsibility changes, an intermediate result is handed off, or ordering, side effects, or failure boundaries differ; comment before each stage even with the same receiver. One comment covers calls only when purpose, precondition, consumer, and failure semantics all match; preparation or mapping cannot also cover execution, persistence, or response work
- three or more terminating entry guards need one comment before the first guard explaining the validation boundary; a smaller cluster also needs one when it crosses input, configuration, state, security, or error-classification boundaries. Do not comment every `if`
- explain why, boundaries, downstream use, or consequences instead of obvious syntax; do not comment self-evident assignments, pure predicates, getters, or direct calls whose complete contract is visible
- Method JavaDoc documents the method-level contract but does not force comments inside a linear body; it also cannot replace required top-level stage comments. Logs, catch-local comments, and nested comments do not substitute for a separate top-level stage comment
- remove stale comments when behavior or ownership moves; call an operation atomic only when its primitive, lock, or compare-and-set contract guarantees it

Java comments, including JavaDoc and body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations. Report every changed-scope violation even when its severity is only `P3`.

## Exception Paths

Treat every changed `try-catch-finally` as a behavioral boundary: catch the intended exception, preserve unexpected failures and caller-relevant error categories, remove context-free catch-log-rethrow blocks, and prevent cleanup or recovery from masking the original failure.

When a `catch` changes behavior through fallback, degradation, retry, suppression, continuation, compensation, or exception conversion, comment immediately before it: state what failed, what happens next, and which guarantee is skipped or preserved. JavaDoc, a pre-`try` comment, log, or vague helper name cannot replace it. Exempt transparent direct rethrows; do not comment unchanged catches or every return mechanically.

Choose the audience before writing failure text. Caller-visible errors use the project's language and domain vocabulary to identify the failed subject or action, an understandable cause, and a real next step when one exists. Internal diagnostics identify the failed stage, safe business identifiers, relevant state, and the original cause. Do not make one vague or technical message serve both audiences; keep the error code, exception type, and message aligned, and never expose raw downstream errors or sensitive implementation details to callers.

## Verification And Findings

Test changed input, output, absence, failure, and state semantics. Run `scripts/check_java_backend_style.py` directly for worktree or explicit-path checks; load its reference only for routed cases. Never claim tests passed when compilation failed or did not start. Separate confirmed facts, supplied configuration, inference, and runtime assumptions; state residual risks when no findings remain.

Use `P0` for data loss, security exposure, or system-wide outage risk; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics likely to cause defects or unsafe maintenance; and `P3` for local clarity or deterministic style. Missing method JavaDoc is `P2` when it hides lifecycle, state, side effects, failure policy, or another contract and otherwise `P3` for an independently named action. A needless extraction is `P2` when it conceals ordering, side effects, failure policy, or lifecycle ownership, and otherwise `P3` when it only adds navigation cost. Unsafe error disclosure, mismatched error categories, lost causes, and diagnostics that cannot identify a production failure are normally at least `P2`, unless their concrete impact warrants `P0` or `P1`; wording that only adds local reading cost is `P3`. Punctuation, method spacing, and wrapping findings are at most `P3`. Before closing, recheck scope, method JavaDoc, names, stage comments, guards, behavior-changing catches, caller-visible errors, internal diagnostics, applicable lifecycle rules, tests, and checker output.
