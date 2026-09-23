---
name: java-backend-code-quality
description: Create, modify, or review Java backend code with change-scoped correctness checks, progressive references, and deterministic style validation
---

# Java Backend Code Quality

Use for Java backend creation, modification, or review. Apply rules only to the task-owned production and test changes; load detailed references only when their trigger matches.

## Scope And Authority

Repository instructions and explicit user rules take precedence. Base decisions on current contracts and repository evidence. Do not turn a local pattern or Skill preference into a project fact.

Limit findings to an explicit file, range, commit, branch, or current staged, unstaged, and untracked Java changes. Ignore unrelated historical, generated, vendored, and third-party code. An unchanged collaborator is context unless the change activates or regresses it.

Before implementation, treat the named class, method, or field as the starting point, inspect its semantic neighborhood, and account for affected callers, data relationships, validation, mapping, persistence, remote calls, logs, errors, outputs, and tests. Ask only when unresolved evidence can change a contract, data, security, diagnostic, lifecycle, or architecture decision. Review mode reports findings without editing and skips the optional structure advisory.

## Git Baseline And Project Hints

Reuse the full `local` commit from a successful `$git-latest-code-check` result; do not rerun the remote check. `CURRENT`, `AHEAD`, and `UPDATED` confirm remote freshness. A dirty warning or failed remote read may provide a local reading baseline, but its `remoteFreshness` is `unconfirmed` and cannot refresh local project guidance.

For implementation in a confirmed Git worktree, read [references/project-guidance.md](references/project-guidance.md) only when the task touches logging, dependencies or utilities, remote calls, exception handling, formatting, or build verification. If guidance is missing, ask once only for such a task whether to initialize it. Never create or refresh it without approval. Load only relevant sections. A simple rename, comment-only change, local branch adjustment, or ordinary CRUD change does not trigger initialization.

## Reference Routing

Read only the matching references:

- [method-design.md](references/method-design.md): private helpers, compact fields or constants, wrappers, deferred work, or method-granularity questions
- [structure-choice.md](references/structure-choice.md): growing implementations, repeated varying flows, scattered creation, or runtime-selected behavior during implementation
- [comments-and-javadoc.md](references/comments-and-javadoc.md): changed classes, methods, JavaDoc, comments, guard clusters, or non-trivial method bodies
- [naming.md](references/naming.md): broad names, state or collection vocabulary, enum lookups, renames, `normalize`, or unclear caller responsibility
- [exception-communication.md](references/exception-communication.md): changed failures, messages, logs, `catch`, `finally`, or error mapping
- [remote-calls.md](references/remote-calls.md): HTTP, Feign, RPC, SDK, request/response logging, parsing, mapping, or provider failures
- [contracts-and-lifecycles.md](references/contracts-and-lifecycles.md): transactions, cross-store behavior, async work, retries, caches, compensation, locks, resources, or non-obvious failure policy
- [control-flow.md](references/control-flow.md): ternaries, branches, loops, braces, or long expressions
- [evidence-and-verification.md](references/evidence-and-verification.md): existing behavior or data semantics, related fields, legacy logic, evidence conflicts, or tools that rewrite files
- [checker.md](references/checker.md): advanced scope, exact CLI behavior, errors, or rule identifiers

## Quality Gates

These are hard quality gates for changed behavior:

- preserve caller-visible null, empty, absent, default, state, and exception semantics
- make names and call sites reveal the subject, action, result, and meaningful side effects; expose collection key/cardinality and duplicate policy
- trace related values through validation, mapping, serialization, persistence, remote calls, caches, logs, errors, and outputs
- assign clear owners and safe ordering for validation, state transitions, persistence, cleanup, delayed work, retries, compensation, and resources
- do not hide meaningful I/O, mutation, fallback, retry, compensation, cleanup, or lifecycle changes inside an apparently pure calculation
- document independent public or application-defined business actions and processing stages; add top-level intent comments where reason, precondition, handoff, order, compatibility, or failure consequence is not visible from code
- compare short helpers, fields, and constants with writing them at use sites; reuse count, JavaDoc, or a clear name alone does not justify extraction
- comment behavior-changing `catch` branches before fallback, degradation, retry, suppression, continuation, compensation, or exception conversion; transparent direct rethrows are exempt
- keep error code, exception type, message, actual failure reason, and effective recovery action aligned
- distinguish third-party business rejection, protocol failure, parse failure, and transport failure while preserving useful provider diagnostics; do not invent mappings or disclosure policy without evidence
- run the deterministic checker, tests, and final-state readback after the last tool that can change files

These are default coding preferences, subordinate to project formatter, `AGENTS.md`, formal documentation, and explicit user rules:

- comments do not end with Chinese or English full stops
- exactly one blank line separates method declarations
- control-flow bodies use braces
- collection variables expose `List`, `Set`, or `Map` where that improves call-site reading
- dense ternaries become braced `if` statements; line wrapping follows project limits and scanability

A preference-only violation is at most `P3`; a contract, lifecycle, diagnostic, security, or unsafe-maintenance consequence may be `P2` or higher. The preference layer never overrides stronger repository evidence.

## Coding-Only Structure Advisory

Before changing production behavior, quietly check whether the current task adds real alternative implementations, repeated varying flows, scattered creation rules, or runtime-selected algorithms. Recommend a strategy, factory, state, composed flow, or handler chain only when the existing change points repeat and the new structure clearly reduces current maintenance risk. A single local branch or one implementation continues directly. If a new interface, class family, or flow reorganization would materially change the design, show the simple and structured options, costs, and recommendation, then wait for the user's choice. This advisory never creates a finding and does not run in review mode.

## Verification And Findings

Test changed input, output, absence, failure, and state semantics. After formatter, generator, hook, test repair, or any other file-changing tool, reread status, final task diff, affected files, recompute reference triggers, and rerun invalidated checks. Separate passed checks from checks that did not run or could not start.

Use `P0` for data loss, security exposure, or system-wide outage; `P1` for likely incorrect behavior, lifecycle leaks, or broken contracts; `P2` for hidden semantics, misleading recovery, unsafe disclosure, or unsafe maintenance; `P3` for local clarity or preference style. Before closing, recheck scope, callers, names, method design, JavaDoc, stages, catches, errors, diagnostics, remote and lifecycle rules, tests, checker output, and residual risks.

Semantic cases under `evals/` are forward tests, not proof from JSON structure alone. The deterministic checker cannot judge natural-language quality, helper extraction, structure choice, semantic neighborhoods, error mapping, logging disclosure, or other meaning-dependent decisions.
