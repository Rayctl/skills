# Evidence, Context, And Final Verification

Read this reference before modifying existing behavior or data semantics, when a quality decision depends on missing or conflicting evidence, or when tools may change files after the initial edit. It governs semantic impact analysis, the distinction between repository facts and Skill defaults, and verification of the code that actually remains on disk.

## Incremental Implementation Loop

Use a light loop for simple changes and a checkpoint loop for complex changes. Complexity is semantic, not a line-count threshold.

A change is usually simple when it is a local rename, direct assignment, getter, pure conversion, isolated branch, or test-data adjustment with no external call, persistent state, cross-field invariant, lifecycle, error-policy, or diagnostic change. Read the target neighborhood, route only triggered references, make the edit, then reread the changed method and final diff. Do not pause after every line or load unrelated references.

Treat a change as complex when it has multiple business stages, changes a boundary call, reads or writes a database, cache, file, queue, or remote service, crosses a transaction or asynchronous boundary, changes state or lifecycle, has retries or compensation, changes error or logging behavior, or relies on related fields jointly expressing a contract. A simple task becomes complex as soon as the edit introduces one of these concerns. Do not downgrade the checks merely because an individual statement is short.

Before the first edit of a complex task:

1. Record the trigger, affected callers, data sources, stage outputs, failure paths, diagnostics, and tests needed to explain the existing behavior
2. Classify the stages and load only references whose triggers are present
3. Identify assumptions that would require a user decision if the evidence remains unresolved

Implement complex work in meaningful slices. After each meaningful stage or boundary call, and before moving to a new responsibility:

1. Read the code just written together with the next consumer
2. Confirm input source, output handoff, validation order, state changes, side effects, error category, recovery path, and diagnostic ownership
3. Check that local names and comments still describe the current behavior and that no helper or constant hides needed branch evidence
4. Recompute the change scope and reference triggers; if a new logging, exception, remote, lifecycle, parameter, or structure concern appeared, load its reference before editing that part

Do not write all stages first and postpone these checks until the final diff. A slice may contain the small statements needed to complete one responsibility, but it must leave a readable handoff to the next consumer before implementation continues. A database write followed by a remote notification, for example, is two checkpoints even if each call is one line.

If a checkpoint reveals that the requirement, data relationship, error meaning, or existing special handling was misunderstood, stop at that boundary. Report the evidence, the changed interpretation, the concrete options and impact, and ask before continuing when behavior would differ. Preserve already-correct stages and discard only conclusions invalidated by the new evidence.

The final pass is not a substitute for checkpoints. It rereads the complete changed path, verifies cross-stage invariants and final callers, runs the deterministic checker and focused tests, and records checks that could not run. For a simple change it may be the only post-edit review; for a complex change it confirms every checkpoint rather than relying on a final diff glance.


## Map The Semantic Neighborhood

The symbol named in the request is an investigation starting point, not automatically the full change boundary. Before editing existing behavior, follow only the paths needed to understand:

- the trigger, relevant callers, and downstream consumers
- input sources, transformations, validation, serialization, persistence, remote calls, caches, outputs, and failure paths
- logs and error details used to diagnose the behavior
- tests, configuration, and contracts that define or preserve it
- other values that participate in the same invariant, decision, identity, state, or diagnostic event

Two fields can be semantically related without referencing each other. If field A and field B jointly determine a validation result, mapping, log event, cache key, state transition, duplicate policy, or caller-visible response, a change to A must explicitly decide whether B and their shared invariant also change. Searching only for A is not sufficient.

Keep the investigation proportional. Stop following a path when it no longer affects the changed behavior, its contract, or the evidence needed to make the decision. Do not read an entire module by default, report unrelated historical defects, or turn context discovery into an unrequested refactor.

Before editing, identify the affected nodes that need a decision. After editing, revisit each node and confirm that it was updated or deliberately preserved with its invariant still valid.

## Explain Existing Behavior Before Changing It

For a non-obvious log field, compatibility branch, special value, ordering rule, or other legacy behavior, first seek its purpose in current callers, tests, configuration, comments, contracts, and comparable implementations. Use focused Git history only when current evidence cannot explain why the behavior exists and changing it could alter results, compatibility, lifecycle guarantees, or diagnostic capability.

Treat logs as diagnostic behavior rather than decoration. Before adding, removing, or changing logged fields, identify the failure or investigation scenario, how the fields correlate to locate it, which layer owns the record, and whether the resulting event still supports that investigation. A request that names field A does not justify dropping or ignoring field B when both fields make the event understandable.

If the purpose remains unknown and materially different changes are possible, pause before editing. State the evidence inspected, the exact unresolved relationship, the concrete options and effects, and a recommendation. Do not ask broad questions such as "What is the business logic here?"

## Classify Evidence

Do not treat every nearby example as a project rule. Classify what supports a decision:

- **authority**: explicit user and repository instructions, published API or schema contracts, compatibility commitments, and approved product decisions
- **observed behavior**: current source, executable tests, configuration, call paths, generated output, and reproducible tool results
- **external contract**: official protocol, provider, framework, or dependency documentation confirmed for the version in use
- **local convention**: repeated nearby patterns that are consistent but not declared as a contract
- **local guidance**: deliberately recorded `.codex/project-guidance.md` hints that reduce repeated discovery but remain below current repository evidence
- **recommendation**: a Skill default or engineering preference used when stronger evidence does not decide the issue

Authority defines intended constraints; observed behavior establishes what the system currently does. Neither automatically overrides the other when they conflict. Surface the conflict and its impact instead of selecting whichever source is more convenient. Tests may preserve a bug, source may violate a published contract, and a common local pattern may still be unsafe.

When applying a rule, state material evidence in the reasoning or finding. Do not present local guidance or a recommendation as an existing repository standard. Local guidance may direct targeted verification and may beat a generic recommendation when stronger evidence is silent, but it cannot create a finding by itself. Examples illustrate a rule; they do not create a universal ban.

## Decide Under Uncertainty

Resolve low-risk, reversible readability choices using the Skill default and the surrounding style, and disclose a consequential assumption in the result. Ask the user only when missing or conflicting evidence leaves materially different outcomes, including:

- public API, persistence, event, or error-contract compatibility
- authorization, privacy, disclosure, data-loss, or irreversible side effects
- transaction, retry, idempotency, compensation, or resource ownership
- third-party error mapping, logging scope, or loss of diagnostic capability
- the meaning or relationship of data that drives validation, mapping, state, persistence, or output
- a new cross-cutting abstraction or architectural boundary

Before asking, report the evidence found, the unresolved decision, the concrete options, their costs, and a recommendation. If an established extension point or contract already resolves the choice, follow it without pausing.

Report a missed semantic relationship according to its actual effect: likely incorrect behavior or a broken contract is `P1` or `P2` depending on certainty and impact, loss of material diagnostic capability is normally `P2`, and unnecessary navigation or local understanding cost is `P3`.

## Read Back The Final State

The code produced by an edit is provisional until later tools finish. Formatters, code generators, test repairs, IDE actions, Git hooks, and external tools can alter code, filenames, comments, imports, or generated contracts after an earlier review.

After the last mutating tool for the task:

1. reread repository status, the final task-owned diff, and every affected file whose behavior or documentation matters
2. include newly generated, renamed, staged, and untracked files in the task scope
3. recompute reference triggers when the final code introduces a helper, exception, remote call, lifecycle boundary, control-flow change, or other routed concern
4. rerun checks invalidated by the final changes, including compilation, focused tests, and the deterministic style checker where applicable
5. distinguish checks that passed from checks that did not run, could not start, or observed only part of the final surface

Do not claim success from the intended patch, an earlier diff, stale test output, or a hook's exit code alone. If a commit or other tool rewrites files, read back the resulting files and metadata before reporting the outcome. Any later change invalidates the earlier verification for the affected surface.

## Semantic Evaluation

The deterministic checker proves only its documented rules. Use the cases under `evals/` to forward-test whether an agent makes the required semantic decisions without requiring exact wording. A case passes only when all expected decisions are present, no disallowed decision is made, and the answer stays within the stated scope.

Do not describe structural validation of the case file as proof that model behavior passed. Behavioral confidence requires running the cases with a fresh evaluator or manually reviewing the resulting decisions.
