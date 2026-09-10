# Method Design And Small Abstractions

Read this reference when changed code adds, edits, extracts, wraps, reuses, or calls an application-defined private helper; extracts compact logic or literals into a private field or constant; introduces deferred execution; or raises an abstraction-granularity question. Do not load it for annotations, imports, independent contract constants, or already clear framework methods.

## Compare With The Code At Its Use Sites

For every in-scope private helper and every private field or constant extracted only to reuse a compact literal or expression, mentally replace its uses with the underlying body or value. Prefer the form that makes the current branch understandable with less navigation and exposes the evidence needed to verify behavior.

Write compact logic or values directly at their use sites, regardless of use count, when doing so remains readable and reveals useful details such as:

- null handling, field sources, or the concrete values being compared
- the actual predicate, component, remote client, or repository being called
- the selected error category and exact caller-visible message at the branch that throws it
- pure parameter forwarding, one-expression wrappers, or a few linear statements
- a single guard followed by a simple assignment or direct call
- local caller values that extraction merely turns into a long parameter list

This applies even when the helper or value has three, eight, or more use sites. Repetition, DRY, a clear name, JavaDoc, centralized wording, a stable-policy label, fewer lines, or reuse count do not independently justify extraction. A long constant name summarizes a message but does not let a reader verify its exact wording, error category, or recovery advice. Allow small local duplication when it preserves branch evidence and reduces jumping.

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
- owning enforceable transaction demarcation, resource acquisition and release, side-effect ordering, compensation, or a dynamic failure policy
- classifying failures from context, converting exceptions while retaining the cause, or adding useful diagnostic data
- satisfying a framework callback, annotation, reflection, serialization, or generated contract

Retain a field or constant when the value has an independent identity or externally governed contract, such as a protocol or persistence identifier, a framework-required compile-time constant, a localization key, an externally stable public identifier, or a structured template with real formatting ownership. Stable error-code constants and enum members remain valid semantic categories; this rule targets human-readable message literals extracted only for local reuse.

A fixed exception code and message do not constitute a dynamic failure policy. A wrapper around one persistence or remote call does not own a meaningful boundary unless it also enforces transaction, ordering, compensation, lifecycle, or failure semantics.

Before removing a helper, exclude framework, annotation, reflection, serialization, and other implicit callers. Do not delete a method based only on textual reference counts.

## Method Shape

Use intermediate values and parameters only when they expose a real processing stage, contract, state, source, or result consumer. Do not introduce generic carriers or parameter objects merely to shorten a signature or reduce visible lines.

Use deferred functions only when a lock, retry, transaction, cache, fallback, or asynchronous API genuinely requires deferred execution. Verify when and how often the function runs, which state it captures, and whether exception behavior remains unchanged.

Remove booleans that are always passed with one value. Use an enum when stable states have distinct behavior. Group parameters only when they form a cohesive value with an independent contract.

Do not hide meaningful I/O, mutation, retry, fallback, compensation, or cleanup behind a method that appears to be a pure calculation or predicate. Method names and boundaries must expose caller-relevant effects.

## Scope And Severity

A helper is in scope when the current change creates or edits it or when a changed call site continues to use it. A field or constant is in scope only when the change creates or edits it as a compact reuse abstraction, or a changed use site relies on it in that role. Read unchanged declarations only as context and do not expand the review into unrelated historical abstractions.

Report a needless extraction as `P2` when it conceals ordering, side effects, failure policy, lifecycle ownership, different failure causes, error categories, recovery actions, or information needed to judge correctness. Use `P3` when it only adds navigation and local reading cost.
