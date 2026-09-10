# Comments And JavaDoc

Read this reference when changed code adds or changes a class, method, JavaDoc, comment, guard cluster, or non-trivial method body. Skip it for changes limited to imports, annotations, constants, or generated and inherited declarations with no new semantics.

## Separate Documentation Scopes

Treat class JavaDoc, method JavaDoc, top-level stage comments, and branch-local comments as different contracts. One scope cannot substitute for another.

Class JavaDoc states the class responsibility and important collaboration boundaries.

Every public method and every application-defined method that owns an independent business action or processing stage requires method JavaDoc, regardless of visibility, body length, linearity, or an already clear name. Explain the purpose and any meaningful timing, input, output, state change, side effect, failure behavior, or downstream use instead of translating the method name.

Exempt only:

- generated methods and third-party or framework signatures
- inherited contracts that remain complete and gain no new semantics
- private helpers with no independent action or contract, such as self-evident accessors, pure delegation, or fixed exception construction

Method JavaDoc is still required for a linear independent action. It does not force stage comments inside a self-explanatory linear body, and it cannot replace required comments in a non-trivial body.

Keep API, Swagger, field, and enum documentation focused on caller-visible meaning and non-obvious defaults, fallback, compatibility, units, or boundaries. Do not repeat enum values already exposed by the type or `allowableValues` unless omission creates a concrete misuse risk.

## Top-Level Stage Comments

Before non-trivial code, divide the method into business stages. Add a top-level comment at a stage's first statement when names and types do not reveal one or more of:

- why the stage exists or which contract it enforces
- its precondition, data source, or state boundary
- the consumer of its result
- ordering, compatibility, or selection policy
- caller-visible side effects or failure consequences

Always inspect independent-source comparisons, filtering or reshaping, compatibility paths, ordered work, hidden selection rules, and calls whose ordinary-looking name hides a special policy.

Treat adjacent calls as separate stages when responsibility changes, an intermediate result is handed off, or ordering, side effects, failure consequences, or compensation boundaries differ. This applies even when the calls share one receiver. Preparation or mapping cannot share one comment with remote execution, persistence, publication, or response construction unless purpose, precondition, result consumer, and failure semantics are all the same.

When a method begins with three or more terminating guards, add one comment before the first guard that explains the validation boundary. A smaller cluster also needs one comment when it crosses input, configuration, state, security, or error-classification boundaries. Do not comment each `if` mechanically.

Comments explain intent, boundaries, downstream use, or consequences rather than restating syntax. Do not comment self-evident assignments, pure predicates, getters, or direct calls whose full contract is visible. JavaDoc, logs, catch-local comments, and nested comments do not replace a required top-level stage comment.

## Comment Maintenance

Remove or update comments when behavior, ownership, or ordering moves. Describe an operation as atomic only when a transaction primitive, lock, or compare-and-set contract actually guarantees atomicity.

## Formatting And Severity

Java comments, including JavaDoc and method-body comments, must not end with `。` or `.`. Keep exactly one blank line between method declarations. Report every changed-scope violation, even when the impact is only stylistic.

Missing method JavaDoc is `P2` when it hides lifecycle, state, side effects, failure policy, timing, or another contract. Otherwise use `P3` for an independently named action. Missing stage or branch comments are `P2` when they hide ordering, compatibility, selection, error classification, side effects, or failure guarantees; use `P3` when they only add local reading cost. Punctuation, method spacing, and wrapping findings are at most `P3`.
