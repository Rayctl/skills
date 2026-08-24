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
3. Reconstruct contracts, stages, ownership, and failure paths when behavior is non-trivial
4. Keep the change scoped and follow established repository patterns
5. Add or update tests in proportion to changed behavior and failure paths
6. Run focused verification and re-read the final changed ranges

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

Do not blacklist generic verbs; evaluate whether they expose the real action contract:

- `normalize` should identify the subject and one concrete canonical form or policy
- `build` should primarily construct a value, not conceal dominant mutation, persistence, compensation, or policy enforcement
- `resolve` should identify the authoritative value or decision and who owns defaults or ambiguity
- `apply` should identify the rule or change, its target, and resulting state
- `finalize` should correspond to a real terminal stage and its preserved guarantees
- `process` and `handle` are acceptable only when the subject and boundary make the dispatch or lifecycle responsibility clear

When a verb hides unrelated actions, choose a specific name, split responsibilities, or expose a stage boundary. Do not report a name solely because it uses a generic verb. Report a misleading responsibility name as `P2` when it can cause callers to omit required policy or lifecycle behavior, and as `P3` when it only increases local reading cost.

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

The checker cannot prove every retry, suppression, continue, compensation, degradation, fallback, or semantic-conversion path. Semantic review remains responsible for those cases and for deciding whether a comment communicates the required guarantee.

## Close The Task

Before closing an implementation or declaring that no review findings remain:

1. Recheck the current task surface and exclude unrelated historical, generated, and vendored code
2. Compare important names with their complete action contracts
3. Inspect behavior-changing catch paths for catch-local intent comments
4. If the deep reference applied, inventory stages, contracts, and lifecycle owners
5. Map tests to changed contracts and meaningful failure paths
6. Run the deterministic checker on the reviewed paths or line ranges

Deliver review findings first, ordered by severity:

- `P0`: data loss, security exposure, or system-wide outage risk
- `P1`: likely incorrect behavior, lifecycle leak, or broken contract
- `P2`: maintainability issue likely to cause defects or make changes unsafe
- `P3`: local clarity or style improvement

For every finding, include a precise file and line, evidence, impact, and the smallest appropriate correction. Distinguish confirmed behavior, supplied configuration, inference, and unverified runtime assumptions. If no findings remain, say so explicitly and list residual risks or verification gaps. Do not turn preferences about method size, naming, wrapping, or comments into findings without concrete behavioral or maintenance cost.
