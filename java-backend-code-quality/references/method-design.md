# Method Design And Small Abstractions

Read this reference when changed code adds, edits, extracts, wraps, reuses, or calls an application-defined private helper; extracts compact logic or literals into a private field or constant; introduces deferred execution; designs or changes parameters; adds or edits a nested class, local class, or nested enum; or raises an abstraction-granularity question. Do not load it for annotations, imports, independent contract constants, or already clear framework methods unless their changed use makes parameter meaning unclear.

## Compare With The Code At Its Use Sites

For every in-scope private helper and every private field or constant extracted only to reuse a compact literal or expression, mentally replace its uses with the underlying body or value. Prefer the form that makes the current branch understandable with less navigation and exposes the evidence needed to verify behavior.

Write compact logic or values directly at their use sites, regardless of use count, when doing so makes the caller easier to understand and reveals useful details such as:

- null handling, field sources, or the concrete values being compared
- the actual predicate, component, remote client, or repository being called
- the selected error category and exact caller-visible message at the branch that throws it
- pure parameter forwarding or short expressions and linear statements that add no useful concept beyond their underlying operations
- a single guard followed by a simple assignment or direct call
- local caller values that extraction merely turns into a long parameter list

This applies even when the helper or value has three, eight, or more use sites. Repetition, DRY, a clear name, JavaDoc, centralized wording, a stable-policy label, fewer lines, or reuse count do not independently justify extraction. A long constant name summarizes a message but does not let a reader verify its exact wording, error category, or recovery advice. Allow small local duplication when it preserves branch evidence and reduces jumping.

Body length and expression count are not deletion criteria either. Compare the actual caller in both forms: does the helper let the reader make the next decision using a meaningful concept, or merely force a jump to recover field sources, null handling, or an already named operation? Apply the short-rule criteria below before expanding a composed predicate.

Typical helpers to write out at their use sites include:

```java
private boolean isCatalogReference(Field field) {
    return field != null
            && FieldCatalog.isReference(field.getCode(), field.getPath());
}

private CommonException invalidReferenceException() {
    return new CommonException(
            ErrorCode.ILLEGAL_ARGUMENT,
            "字段引用不符合约束");
}

private static final String FIELD_DEFINITION_MISMATCH_MESSAGE =
        "字段定义已更新，请刷新页面后重新配置";
```

At each call site, the expanded predicate shows the null rule and source fields, while the expanded exception or message literal shows the exact failure category and caller message. A private human-readable message constant created only for reuse should normally be replaced by its literal at every throw site.

## When A Helper May Remain

Retain a helper only when its separate boundary materially lowers call-site cognitive load or an external contract requires the method identity. Valid reasons include:

- hiding non-trivial branching, iteration, an algorithm, or low-level mechanics
- combining low-level checks into a useful business or protocol concept, including a short predicate, under the criteria below
- owning enforceable transaction demarcation, resource acquisition and release, side-effect ordering, compensation, or a dynamic failure policy
- classifying failures from context, converting exceptions while retaining the cause, or adding useful diagnostic data
- satisfying a framework callback, annotation, reflection, serialization, or generated contract

Retain a field or constant when the value has an independent identity or externally governed contract, such as a protocol or persistence identifier, a framework-required compile-time constant, a localization key, an externally stable public identifier, or a structured template with real formatting ownership. Stable error-code constants and enum members remain valid semantic categories; this rule targets human-readable message literals extracted only for local reuse.

A fixed exception code and message do not constitute a dynamic failure policy. A wrapper around one persistence or remote call does not own a meaningful boundary unless it also enforces transaction, ordering, compensation, lifecycle, or failure semantics.

Before removing a helper, exclude framework, annotation, reflection, serialization, and other implicit callers. Do not delete a method based only on textual reference counts.

## Short Methods That Express A Useful Rule

A short predicate may remain when it actually combines checks into one coherent concept used by the caller, and expanding those checks distracts from the caller's decision. For example, `isXmlContentType` can group application/xml, text/xml, and structured +xml suffix recognition; `isJsonContentType` can group JSON compatibility matching and +json suffix recognition. Two lines or one caller do not remove that benefit.

Compare these cases:

- a content-type classifier composes recognition rules so the caller can choose an encoder or decoder without repeating media-type details
- a null-safe Schema getter only traverses fields; writing it out exposes the data source and absence behavior
- a helper that checks null, extracts two fields, and delegates to an existing named predicate usually adds no new classification rule; writing it out exposes the actual arguments
- a fixed exception factory hides the error code and message needed to understand the failing branch

A descriptive name or multiple boolean operators alone is insufficient. The grouped conditions must express one concept; do not group unrelated eligibility, authorization, or state checks if the caller needs their separate failure reasons or recovery actions. A newly extracted pure predicate must not conceal I/O, mutation, or failure handling.

Verify that the name and contract match the actual accepted values, exclusions, and null behavior. Retain meaningful recognition details in concise JavaDoc when they are not evident from the name, including whether null is rejected or returns false. Do not silently change matching or null behavior to justify extraction. An isXxx prefix is not an exemption, and allowing a useful local helper does not itself justify introducing a shared utility or new class.

## Method Shape

Use intermediate values and parameters only when they expose a real processing stage, contract, state, source, or result consumer. Do not introduce generic carriers or parameter objects merely to shorten a signature or reduce visible lines.

Use deferred functions only when a lock, retry, transaction, cache, fallback, or asynchronous API genuinely requires deferred execution. Verify when and how often the function runs, which state it captures, and whether exception behavior remains unchanged.

Do not hide meaningful I/O, mutation, retry, fallback, compensation, or cleanup behind a method that appears to be a pure calculation or predicate. Method names and boundaries must expose caller-relevant effects.

## Make Parameters Understandable At Calls

Read the changed call without entering the implementation. Adjacent boolean arguments, especially literal sequences such as `validateNode(node, false, true, false)`, require review because positional values can hide different responsibilities or invite swaps. Judge their actual meaning, not a fixed flag count. A clearly named dynamic boolean, an obvious single switch such as `setEnabled(true)`, or a framework or third-party signature can remain; do not introduce wrappers merely to remove booleans.

Separate three kinds of information:

- object properties: derive them from the existing object only when that object actually owns the fact
- invocation context: fixed regions, roles, or modes can use an existing or lightweight named enum; do not attach a request position or policy to a reusable domain object solely for this call
- traversal state: ancestor conditions and root identity may differ from the current node's properties; preserve them explicitly or simplify traversal only when equivalent behavior is demonstrated

Remove an application-controlled parameter whose relevant callers always pass one value and which has no present variation requirement, after checking implicit callers and signature contracts. This applies to fixed paths and other values as well as booleans. Preserve externally required signatures. Retain genuine dynamic state with clear names; group parameters only when they form a cohesive value with an independent contract.

Keep readable explicit entry calls when they already reveal the processed regions and order. A location enum should describe location; it need not also select nodes, run validation, or own changing traversal state. Do not add selectors, automatic loops, short forwarding methods, or parameter carriers solely to hide literal flags. Compare the whole proposed change with the original call, including new navigation and types.

When eliminating traversal flags, verify ancestor versus current-node behavior, subtree and array boundaries, cleanup, validation order, null semantics, and error category and message. Equivalent final output alone does not prove equivalent validation or failure behavior.

## Default To Fewer Nested Types

Apply this preference to new or edited non-static inner classes, static nested classes, local classes, and nested enums. First consider direct local values or an existing type. A type with an independent responsibility normally belongs in a separate file with the minimum visibility needed by its callers; moving it out must not make it a public API by default. Do not replace a tiny temporary carrier with a separate file merely to satisfy this preference.

Nesting may remain when the type truly belongs to its enclosing implementation and reading the non-trivial behavior together reduces navigation, or when a meaningful Builder or a framework contract requires that identity. A one-place flag bag, fewer files, or access to outer fields alone does not justify nesting. If outer-instance access is unnecessary and the language permits it, prefer a static nested type to avoid an implicit enclosing-instance reference.

Ordinary tests and mocks do not trigger a type hierarchy rewrite; framework-required nested tests can remain. This is a default preference subordinate to formal project conventions and explicit user rules, not a categorical ban.

## Scope And Severity

A helper is in scope when the current change creates or edits it or when a changed call site continues to use it. A field or constant is in scope only when the change creates or edits it as a compact reuse abstraction, or a changed use site relies on it in that role. Read unchanged declarations only as context and do not expand the review into unrelated historical abstractions.

For parameters, examine changed application-defined signatures and calls plus only the declarations needed to understand them. For nested types, examine only types added or edited by this task; using an unchanged nested type does not activate a historical nesting cleanup.

Report a needless extraction as `P2` when it conceals ordering, side effects, failure policy, lifecycle ownership, different failure causes, error categories, recovery actions, or information needed to judge correctness. Use `P3` when it only adds navigation and local reading cost.

Assign a finding only to an evidenced rule violation or concrete readability or behavior problem. Another valid representation or a user-requested improvement alone is not a `P2` or `P3` issue. Clear fixed path strings can remain without a required typed contract or demonstrated defect; an enum may be discussed as an option without grading the existing form. This does not exempt opaque flags, hidden semantics, or applicable explicit/default rules.

Use `P3` for unclear parameter presentation or unjustified nesting that only affects reading. A preference-only nesting issue is at most `P3`; wrong flag semantics, changed validation order, unintended object retention, or other demonstrated behavior and lifecycle risks follow impact-based severity.
