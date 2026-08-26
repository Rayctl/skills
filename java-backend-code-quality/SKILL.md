---
name: java-backend-code-quality
description: Create, modify, or review Java backend code using change-scoped quality rules, with deeper contract and lifecycle checks for non-trivial logic; excludes formal code-reviewer and commit-gate workflows.
---

# Java Backend Code Quality

Use this skill whenever a task creates, modifies, or reviews Java backend code. Apply the common correctness, naming, comment, formatting, exception, and method-design rules to every in-scope changed Java source, including tests. Apply deeper contract and lifecycle checks only when the changed behavior contains those concerns.

## Authority And Scope

Read applicable repository instructions before acting. Repository and explicit user instructions are authoritative when they conflict with this skill.

This skill does not perform a formal `code-reviewer` or commit-gate workflow and does not issue their approval markers.

Limit implementation and findings to the current task surface. Include changed Java production and test sources. Exclude generated sources, vendored code, and unrelated historical files unless the user explicitly includes them. Unchanged callers and collaborators may be read as context, but report an issue in unchanged code only when the current change directly activates or regresses it; state that causal link.

## Choose The Mode

### Implementation Mode

When creating or modifying Java backend code:

1. Establish the current task surface before editing
2. Apply the common rules to every changed Java range
3. Before writing a non-trivial method, partition its work into business or technical stages and identify each stage's reason, input boundary, result consumer, and failure consequence
4. Reconstruct contracts, ownership, and failure paths when behavior is non-trivial
5. Add names, structure, and intent comments while implementing instead of deferring them to a later cleanup pass
6. Keep the change scoped and follow established repository patterns
7. Add or update tests in proportion to changed behavior and failure paths
8. Run focused verification, re-read the final changed ranges, and check every identified stage for intent-comment coverage

### Review Mode

Report findings without editing unless the user requests fixes. Lead with actionable findings tied to the current task or change set, and use surrounding code only to establish evidence and impact.

## Establish The Change Surface

Determine the implementation or review surface in this order:

1. Use a file, line, commit, or branch range explicitly supplied by the user
2. Otherwise use ranges already attributable to the current task
3. Otherwise inspect the `HEAD` worktree, including staged, unstaged, and untracked files
4. If the worktree is clean, use an explicit baseline or a derivable upstream merge base
5. If the intended range still cannot be determined without guessing, ask the user for a baseline

Never crawl a repository to guess authorship or manufacture a review surface. Capture the baseline and file state, and re-read affected paths if files drift while working.

## Apply Rules By Complexity

Always inspect in-scope changed Java code for:

- caller-visible correctness and consistent null, empty, absent, disabled, and default semantics
- names that communicate concrete data, action, and result contracts
- comments and JavaDoc that explain non-obvious intent without restating syntax
- behavior-changing exception branches that expose their fallback or failure consequence locally
- method responsibilities, parameters, and extraction choices that remain understandable at the call site
- deterministic comment punctuation and method-separation rules
- tests and verification proportional to changed behavior

Read [references/contracts-and-lifecycles.md](references/contracts-and-lifecycles.md) when changed code coordinates multiple stages, side effects, resources, transactions, remote calls, asynchronous work, retries, caches, compensation, concurrency-sensitive writes, or non-obvious caller-visible failure policies. Do not load that reference for trivial accessors, data holders, pure predicates, or mechanical edits with none of those concerns.

## Intent Comment Coverage

Treat a non-trivial method as a sequence of semantic stages, not as one block covered by its JavaDoc. During implementation and review, identify the stages first, then verify that a maintainer can understand why each stage exists, what boundary it enforces, where its result goes, and what consequence it owns.

Add a concise comment at the start of a stage when names and types do not already explain the reason, constraint, ordering, or downstream guarantee. Always perform this semantic check around:

- comparisons between values obtained from independent sources, especially when exact agreement or precedence is required
- filtering, flattening, grouping, encoding, or reshaping that changes which data continues or how downstream code interprets it
- steps whose order preserves correctness, compatibility, idempotency, or failure isolation
- compatibility paths that deliberately retain legacy representation, fallback, or caller-visible behavior
- calls whose ordinary-looking name hides policy enforcement, transaction ownership, compensation, cross-boundary persistence, or another special responsibility

Method JavaDoc states the method contract; it does not cover method-body stages. Logs, catch-local comments, and comments nested inside a branch also do not explain a separate top-level stage. When a method contains multiple stages, check coverage stage by stage rather than accepting one arbitrary comment anywhere in the body.

Do not translate syntax into comments. If a proposed comment can only say that code checks, converts, or calls something already clear from names and types, improve the names, introduce a meaningful intermediate value, or split a stable responsibility instead. Do not add comments to obvious assignments, pure conditions, or direct calls whose complete action contract is already visible.

Treat method-entry guard clauses as one validation cluster:

- three or more terminating entry guards require one intent comment before the first guard, explaining the boundary or error categories separated by the cluster
- allow pure local-value extraction between entry guards without ending the cluster
- a guard terminates its rejected path with `throw`, `return`, `break`, or `continue`
- do not add a repetitive comment to every `if`
- fewer than three guards still require a cluster comment when they cross caller input, configuration, state, security, or error-classification boundaries; this remains a semantic review decision

Report missing intent as `P2` when it hides a contract, ordering dependency, error classification, or failure guarantee likely to make later changes unsafe. Report it as `P3` when it only slows local understanding.

## Exception Boundaries

Inspect each changed `try-catch-finally` as a behavioral boundary:

- catch the narrow exception representing the intended recovery or degradation condition
- preserve unexpected runtime failures instead of converting them into ordinary absence or infrastructure misses
- keep validation, conversion, remote-call, and persistence failures distinguishable when callers treat them differently
- remove catch-log-rethrow blocks that add no context or ownership
- prevent cleanup or recovery failures from masking the original exception

Every behavior-changing catch path requires a catch-local intent comment immediately before the changed behavior. This includes fallback return, degradation, retry, suppression or continue, compensation, and conversion to a semantic exception. State:

- what operation or guarantee failed
- what happens next
- which guarantee is skipped and which guarantee is preserved

A method JavaDoc, comment before the `try`, log statement, or vague helper name does not substitute for this local comment. A transparent direct rethrow with no semantic change is exempt. Do not require a comment for every catch or return; require it where the catch changes behavior.

Report a missing or misleading catch-local comment as `P2` when hidden behavior or lifecycle can cause misuse or unsafe maintenance, and as `P3` when the impact is limited to local readability.

## Responsibilities And Method Design

Judge a method by its concrete responsibility rather than line count:

- keep a small method when it names a stable stage, owns a lifecycle, or contains independently meaningful policy
- inline wrappers that only rename delegation, add a routine null check, or construct a fixed exception without adding policy
- keep a rejection condition near its caller-visible consequence when extraction would hide the complete rule
- tolerate small local duplication when it keeps condition, action, and consequence visible together
- split methods that mix orchestration, transformation, side effects, and cleanup into an opaque block
- avoid generic context, builder, coordinator, or helper abstractions created only to reduce line count
- use intermediate values when they name a stage result or expose an important boundary
- keep meaningful mutation and I/O out of control-flow conditions; pure predicates may remain in conditions

Review parameters by semantic role:

- use a supplier, lambda, or method reference only when execution genuinely must be deferred for locking, retry, transaction, caching, or fallback
- verify deferred functions are invoked only as intended and preserve exception semantics
- remove booleans that are always fixed; decide whether paths should split or the rule belongs at the caller
- use an enum for stable states with distinct behavior, not merely to relabel `true` and `false`
- group parameters only when they form a cohesive value

Before extracting code, ask whether the rule is clear at the use site, whether local duplication is cheaper than another jump, and whether the candidate owns independently evolving policy or lifecycle. Reuse alone is not sufficient.

## Action-Contract Naming

Review changed class, method, field, parameter, and local-variable names in proportion to their semantic role. For each important method and value, identify:

- the subject or data shape
- the primary action
- the result or state change
- policy, transaction, compensation, cache, retry, or exception ownership
- how the caller uses the result next

Require the name to match the complete implementation and caller use, not only the return type or a conventional verb. Prefer concrete repository and domain vocabulary familiar to maintainers over translated abstractions or generic wording that only sounds technical. Make a value name identify its data, state, source, or intended consumer when its type alone is insufficient.

Perform a call-site readability check for each important method. Read only the receiver, method name, parameter roles, and how the result is used, without opening the implementation or relying on JavaDoc. The call should reveal:

- the concrete subject, product, or decision
- the primary action and meaningful result or state change
- persistence, remote I/O, transaction, compensation, fallback, or other caller-relevant side effects

The receiver may supply a subject when it identifies one unambiguous responsibility; do not mechanically repeat it. However, quantity, container, transport, and generic carrier words such as `Batch`, `List`, `Data`, `Info`, `Context`, `Item`, and `Result` do not identify the business subject by themselves. A caller must not need an implementation jump merely to learn what is built, saved, transformed, or processed.

Generic action verbs require a concrete subject, product, rule, or outcome. Reject a bare verb or a name whose remaining words still do not expose the action contract. Apply this default to:

- construction: `build`, `create`, `make`, `prepare`, `generate`
- conversion: `convert`, `map`, `transform`, `normalize`
- lookup and decision: `get`, `find`, `query`, `load`, `resolve`, `check`, `validate`
- mutation: `save`, `update`, `delete`, `apply`, `merge`, `sync`, `refresh`, `finalize`
- orchestration: `process`, `handle`, `execute`, `run`

Apply these verb-specific rules:

- `build` names the concrete product and primarily constructs that product; `OutboundRequestUrlBuilder#build(config, request)` should be `buildOutboundRequestUrl`
- `convertToXxx` and `mapToXxx` name a concrete target shape; keep the Java `To` convention and do not replace it with `2`
- `transform` and `normalize` name the actual transformation, canonical form, or policy; adding only a broad subject, as in `normalizeSystemContext`, is insufficient when the performed action remains unknown
- lookup names make caller-relevant absence behavior visible, distinguishing an optional search from a required value that throws when missing when repository conventions and types do not already do so
- enum lookup methods follow the naming pattern established by nearby enums before introducing a new convention; inspect the current repository rather than assuming one global Java style
- enum lookup names expose both the returned value or property and every caller-relevant lookup field: use a repository convention such as `getByCode` for the enum value and `getDescByCode` for its description; reject bare `find`, `get`, or `of` because the lookup key and result contract are not visible
- when a repository uses `find` specifically for optional lookup, retain that semantic but include the key, such as `findByCode`; do not use `find` alone merely because the method can return `null`
- enum lookup absence behavior follows the repository contract and is made explicit through the return type, a nullability annotation, JavaDoc, or a documented exception; do not introduce `Optional`, nullable returns, or throwing behavior solely to satisfy a naming preference
- reserve `valueOf` for Java's enum-constant-name contract unless the repository defines a distinct, unambiguous API; a business `code` lookup must say `ByCode` or follow an equally explicit local convention
- boolean decisions use `is`, `has`, `can`, or `should`; throwing validation uses a concrete contract name such as `validateRequestContract` or `requireEditableState`
- mutation and orchestration names identify their target and must not disguise persistence, remote calls, transactions, compensation, or degradation as ordinary calculation
- shape or quantity is only a qualifier: `saveBatch`, `buildData`, and `processList` remain unclear; prefer a concrete responsibility such as `saveApiConfigChanges`

Allow a conventional short name only when its contract is already fixed and unambiguous:

- an interface override or framework callback whose signature cannot be renamed, such as `run`, `handle`, or `execute`
- a standard `Builder#build()` dedicated to one product, where state is accumulated before the call and the method accepts no business input or multi-stage orchestration responsibility
- `create`, `save`, `update`, or `delete` on a receiver clearly identified as a `Repository`, `Mapper`, or `DAO`, when it performs the conventional single-store persistence operation
- Java, JDK, or third-party conventions such as `toString`, `toBuilder`, and `toInstant`

An `XxxBuilder#build(...)` that accepts business inputs and executes a complete flow does not receive the standard Builder exemption. A persistence abstraction that coordinates cross-store writes, compensation, or another special lifecycle must expose that responsibility despite its receiver name.

After implementation, re-read the primary call sites and rename the method if its basic responsibility is not evident there. When a generic verb hides unrelated actions, choose a specific name, split responsibilities, or expose a stage boundary. Report a misleading responsibility name as `P2` when hidden persistence, absence, exception policy, or lifecycle behavior can cause misuse; report it as `P3` when it only increases navigation and local reading cost.

## Comments And Formatting

Treat class JavaDoc, method JavaDoc, and method-body comments as independent scopes:

- class JavaDoc describes responsibility and collaboration boundaries
- method JavaDoc describes the contract, meaningful input/output semantics, failure behavior, and non-obvious lifecycle ownership
- require method JavaDoc for public methods and methods that own a caller-visible contract, lifecycle, or non-obvious behavior
- inherited overrides with a sufficient contract, getters, setters, simple delegation, fixed exception construction, and self-evident private helpers are exempt
- method JavaDoc does not replace method-body comments for non-obvious stages, ordering, or changed failure behavior
- method-body comments expose non-obvious stage intent, ordering, cross-boundary work, state changes, compensation, admission, and changed exception behavior
- stage comments explain why a step is required, where its result goes, or which consequence it owns; they do not merely restate the call
- do not require line-by-line comments for obvious assignments, pure predicates, getters, or direct calls
- update or remove comments when behavior and ownership move
- do not describe an operation as atomic unless the actual primitive, lock, or compare-and-set contract makes it atomic

Apply these exact formatting rules unless an explicit user instruction or repository-enforced rule requires otherwise:

- Java comments, including JavaDoc and method-body comments, must not end with a Chinese or English full stop (`。` or `.`)
- keep exactly one blank line between method declarations; do not leave zero or multiple blank lines

Treat pure punctuation, method-separation, and wrapping findings as `P3` at most, but report every in-scope deterministic violation during review.

## Tests And Verification

Map tests to changed input, output, absence, failure, and state semantics. Load the deep reference for its additional lifecycle scenarios when applicable. Report compilation and test execution separately; never claim tests passed when compilation failed or tests did not start.

## Deterministic Style Checker

Run `scripts/check_java_backend_style.py` on in-scope Java ranges before closing an implementation or review:

```text
py -3 "<skill-directory>\scripts\check_java_backend_style.py" --changed [--base <ref>] [--repo <path>] [--exclude <path>]... [paths...]
py -3 "<skill-directory>\scripts\check_java_backend_style.py" [--exclude <path>]... <full-path> [<full-path>...]
py -3 "<skill-directory>\scripts\check_java_backend_style.py" --line-range "<file>:<start>-<end>" [--line-range "<file>:<start>-<end>"]
```

In `--changed` mode, positional paths include only matching changed files and `--exclude` paths remove files or directory descendants from that set. Exclusion wins over inclusion. Resolve relative exclusions from `--repo` in changed mode and from the current directory in full-path mode. Exclusions may name absent paths, do not accept globs, and cannot be combined with `--line-range`.

The checker does not guess which directories are generated or vendored. When selected paths contain such code, identify it from repository configuration or source layout and pass each known file or directory with `--exclude`.

Exit codes are `0` for clean, `1` for violations, and `2` for usage, input, or environment errors. Excluding every selected Java file is clean and must produce a clear message.

Use these deterministic rule identifiers:

- `STYLE-COMMENT-001`: Java comment ends with a Chinese or English full stop
- `STYLE-METHOD-001`: method declarations are not separated by exactly one blank line
- `STYLE-CATCH-001`: a behavior-changing catch path lacks the required catch-local intent comment
- `STYLE-GUARD-001`: at least three terminating method-entry guards lack one leading cluster intent comment
- `STYLE-INTENT-001`: an obviously complex method has no top-level stage intent comment

`STYLE-INTENT-001` is intentionally conservative: it requires at least 15 non-blank code lines and at least three control-flow nodes before reporting a total absence of top-level stage comments. JavaDoc, catch-local comments, logs, and nested comments do not satisfy it. `STYLE-GUARD-001` recognizes terminating entry guards and permits pure local-value extraction between them. Both findings cover the containing method as evidence, so changed and line-range modes report them only when the selected scope intersects that method.

The checker cannot judge comment quality, determine how many stages need comments, or prove every retry, suppression, continue, compensation, degradation, fallback, cross-source validation, or semantic-conversion path. Semantic review remains responsible for those cases, for guard clusters below the automatic threshold, and for deciding whether a comment communicates the required intent and guarantee.

## Close The Task

Before closing an implementation or declaring that no review findings remain:

1. Recheck the current task surface and exclude unrelated historical, generated, and vendored code
2. Compare important names with their complete action contracts
3. Partition every non-trivial changed method into stages and check top-level intent-comment coverage
4. Inspect entry guard clusters and behavior-changing catch paths for their local intent comments
5. If the deep reference applied, inventory stages, contracts, and lifecycle owners
6. Map tests to changed contracts and meaningful failure paths
7. Run the deterministic checker on the reviewed paths or line ranges

Deliver review findings first, ordered by severity:

- `P0`: data loss, security exposure, or system-wide outage risk
- `P1`: likely incorrect behavior, lifecycle leak, or broken contract
- `P2`: maintainability issue likely to cause defects or make changes unsafe
- `P3`: local clarity or style improvement

For every finding, include a precise file and line, evidence, impact, and the smallest appropriate correction. Distinguish confirmed behavior, supplied configuration, inference, and unverified runtime assumptions. If no findings remain, say so explicitly and list residual risks or verification gaps. Do not turn preferences about method size, naming, wrapping, or comments into findings without concrete behavioral or maintenance cost.
