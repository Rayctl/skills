# Structure Choice Before Coding

Read this reference only in implementation mode when current production code or shared test infrastructure shows one of the variation signals routed from `SKILL.md`. This is an advisory before editing, not a review rule or a source of `P2` or `P3` findings.

## Evaluate Current Variation

The following signals require evaluation but do not prove that a design pattern is useful:

- the task adds another implementation of one responsibility
- type, state, protocol, provider, or channel branches are growing
- several flows share an overall sequence but vary at particular steps
- construction choices for one product are spread across callers
- configuration or runtime state selects an algorithm, validation rule, or processing policy

Keep a local `if`, `switch`, enum map, direct method, or constructor when the decision has one clear owner and remains easy to understand. Ordinary guards, one-off branches, simple enum mappings, a single implementation, and speculative future variants do not justify another interface or class hierarchy. A second implementation is a reason to inspect the structure, not a reason to change it.

Recommend a new structure only when all of these are true:

- the variation already exists in current code or requirements
- selection or construction repeats in several places, or several flows must preserve one shared sequence
- the proposed owner concentrates that variation and reduces the places changed for the next known case
- the interfaces, classes, and indirection added cost less to understand than the branches and duplication they replace

## Choose The Smallest Useful Structure

Reuse an established repository extension point first. When the task only adds an implementation to that existing contract, follow it without pausing for another design choice.

If a new structure is justified, match it to the actual problem:

- use a strategy-style interface when callers select interchangeable behavior with one real contract; do not wrap tiny branches that are clearer in place
- use a factory when meaningful construction or dependency selection is duplicated or scattered; do not replace one direct constructor with a pass-through factory
- use state-specific objects when state controls both behavior and valid transitions; keep an enum or local branch when state is only data
- use a composed flow when the overall sequence is fixed and selected steps vary; consider a template method only when inheritance already fits the domain and lifecycle hooks are the intended contract
- use an ordered handler chain only when processor order, continuation, stop, and failure rules are explicit

Do not add empty interfaces, pass-through classes, behavior-free hierarchies, short wrappers, or extension points based only on possible future needs. Existing project conventions and framework contracts take precedence over introducing a different pattern.

## Present A Material Suggestion

Stay silent and continue when the simple structure is sufficient. When a new interface, class set, or flow reorganization would materially improve the current task, explain before editing:

1. the concrete repeated decision or varying behavior in the current code
2. the simplest direct implementation
3. the proposed structure and which variation it owns
4. the added maintenance cost and the benefit over the direct option
5. the recommended option and why

Then pause for the user's choice. An explicit user request or repository rule selecting the structure removes the need to ask again. If the user declines, implement the simplest correct option and do not report the choice as a quality problem.

Do not run this advisory during review-only work. Existing correctness, ownership, naming, method-design, and lifecycle rules still apply independently when they reveal a concrete defect or maintenance risk.
