# Method Design

Read this reference when changed code adds, edits, extracts, wraps, reuses, or calls an application-defined private helper, introduces deferred execution, or raises a method-granularity question. Do not load it for changes limited to fields, annotations, imports, or already clear framework methods.

## Inline-Substitution Test

For every in-scope private helper, mentally replace its main call sites with its body. Prefer the form that makes the current branch understandable with less navigation and exposes the evidence needed to verify behavior.

Inline compact logic regardless of call count when expansion remains readable and reveals useful details such as:

- null handling, field sources, or the concrete values being compared
- the actual predicate, component, remote client, or repository being called
- fixed error codes and messages at the branch that throws them
- pure parameter forwarding, one-expression wrappers, or a few linear statements
- a single guard followed by a simple assignment or direct call
- local caller values that extraction merely turns into a long parameter list

This applies even when the helper has three, eight, or more call sites. Repetition, DRY, a clear method name, JavaDoc, centralized wording, a stable-policy label, fewer lines, or reuse count do not independently justify extraction. Allow small local duplication when it preserves branch evidence and reduces jumping.

Typical helpers to inline include:

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
```

At each call site, the expanded predicate shows the null rule and source fields, while the expanded exception shows the exact failure category and caller message.

## When A Helper May Remain

Retain a helper only when its separate boundary materially lowers call-site cognitive load or an external contract requires the method identity. Valid reasons include:

- hiding non-trivial branching, iteration, an algorithm, or low-level mechanics
- owning enforceable transaction demarcation, resource acquisition and release, side-effect ordering, compensation, or a dynamic failure policy
- classifying failures from context, converting exceptions while retaining the cause, or adding useful diagnostic data
- satisfying a framework callback, annotation, reflection, serialization, or generated contract

A fixed exception code and message do not constitute a dynamic failure policy. A wrapper around one persistence or remote call does not own a meaningful boundary unless it also enforces transaction, ordering, compensation, lifecycle, or failure semantics.

Before removing a helper, exclude framework, annotation, reflection, serialization, and other implicit callers. Do not delete a method based only on textual reference counts.

## Method Shape

Use intermediate values and parameters only when they expose a real processing stage, contract, state, source, or result consumer. Do not introduce generic carriers or parameter objects merely to shorten a signature or reduce visible lines.

Use deferred functions only when a lock, retry, transaction, cache, fallback, or asynchronous API genuinely requires deferred execution. Verify when and how often the function runs, which state it captures, and whether exception behavior remains unchanged.

Remove booleans that are always passed with one value. Use an enum when stable states have distinct behavior. Group parameters only when they form a cohesive value with an independent contract.

Do not hide meaningful I/O, mutation, retry, fallback, compensation, or cleanup behind a method that appears to be a pure calculation or predicate. Method names and boundaries must expose caller-relevant effects.

## Scope And Severity

A helper is in scope when the current change creates or edits it or when a changed call site continues to use it. Read unchanged declarations only as context and do not expand the review into unrelated historical helpers.

Report a needless extraction as `P2` when it conceals ordering, side effects, failure policy, lifecycle ownership, or information needed to judge correctness. Use `P3` when it only adds navigation and local reading cost.
