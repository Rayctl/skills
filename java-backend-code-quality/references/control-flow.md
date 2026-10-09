# Control Flow And Line Wrapping

Read this reference when Java code adds or changes a ternary expression, branch, loop, structural count, index, or separator; when repeated decisions scatter a path; or when a chained call is being wrapped for readability.

## Ternary Expressions

Keep a ternary only when it is a short, pure value choice and both branches are immediately obvious:

```java
String statusText = enabled ? "启用" : "停用";
```

Prefer a braced `if` when the expression combines assignment with comparison, null handling, field access, or a method call; when either branch performs a business action, conversion, exception construction, or other side effect; or when the expression is nested or visually long. A short line is not automatically a readable line:

```java
String userName = null;
if (user != null) {
    userName = user.getName();
}
```

Do not recommend this form merely because it fits one line:

```java
String name = user == null ? null : user.getName();
```

The quality finding is semantic. Report `P2` when a ternary hides null, default, error, or side-effect behavior that can lead to a wrong change; use `P3` when it only makes a local expression harder to scan. Do not mechanically flag every ternary.

## Keep One Processing Path Together

When an unchanged discriminator selects the same path more than once in a method, compare the current layout with one branch containing that path's validation, value extraction, and action. Prefer the concentrated form when it reduces backtracking and preserves validation order, error precedence, evaluation count, and side effects. Mutually exclusive shapes can use a braced `if` / `else if` / `else` with each path completed locally; a final branch rejects unsupported shapes.

For example, after splitting a qualified identifier, a two-part path can validate and name its prefix and local name, resolve the prefix, then create the result. A one-part path handles an unqualified name. Repeating the two-part test on either side of a mutable `validName` variable can scatter this path without providing a useful phase boundary.

A named boolean may clarify a meaningful condition, but merely changing both tests to `hasPrefix` does not concentrate the path. Decide the layout first. Introduce a boolean only when it exposes a useful fact, not solely to hide repeated syntax.

Repeated tests can remain when they serve distinct necessary phases: all inputs must be validated before any action, shared prevalidation protects multiple paths, or intervening work can change the tested state. Do not merge independent guards, move I/O before validation, cache a changing predicate, or duplicate shared validation just to remove a repeated condition. Read the intervening code and relevant contracts before deciding.

## Explain Structural Values Locally

For counts, indexes, separators, and other literals that control structure, make the relationship understandable at the use site. Use meaningful local names for the extracted parts and a concise comment when the protocol or shape is not evident:

```java
// A qualified name contains a prefix and a local name separated by a colon
if (nameParts.length == 2) {
    String prefix = nameParts[0];
    String localName = nameParts[1];
    // Validate both parts before resolving the prefix and creating the result
}
```

This is an illustrative branch fragment, not a complete implementation. The comment explains why two parts are expected; the names explain their roles. Do not invent a constant, enum, wrapper, or helper for every `0`, `1`, or `2`. A constant is appropriate when a value has an independently governed contract, configurable limit, or identity used across responsibilities. Names and comments must match the actual accepted structure and preserve invalid-input handling.

## Final Control-Flow Review

After editing, trace each changed path from condition to outcome. Check scattered repeated decisions, meaningful structural literals, and dense ternaries as well as braces and wrapping. Reapply the ternary rule to expressions combining null handling with allocation or calls; do not overlook them merely because the style checker passes.

A demonstrated local reading problem is `P3`. Hidden validation order, error precedence, state, or side effects follow actual impact and may be `P2` or higher. Repetition or literals alone are not findings; another valid layout is not automatically a defect.

## Braces

Every Java `if`, `else`, `for`, `while`, and `do while` body uses braces, including a single `return`, `throw`, `break`, or `continue`. An `else if` chain is valid when every actual branch body is braced; no extra wrapper is needed around the chain.

```java
if (request == null) {
    return emptyResult();
} else if (request.isCached()) {
    return cachedResult(request);
} else {
    return loadResult(request);
}
```

The deterministic checker reports a missing body brace as `STYLE-BRACE-001`. It ignores comments, strings, text blocks, and unchanged historical code. Braces do not replace intent comments when a branch has a non-obvious business consequence.

## Line Wrapping

Use the repository's formatter or documented maximum line length first. If no project limit exists, use the active IDE's normal code viewport as a practical guide, but never optimize for a guessed pixel width.

- Keep a variable, receiver, method name, and short argument list on one line when the complete expression fits and remains easy to scan
- Wrap when the line exceeds the project limit, hides an important argument boundary, or contains multiple independent operations
- Prefer wrapping at argument or chain boundaries and align continuation lines consistently with nearby code
- Do not break a short `receiver.method(...)` only because the receiver or method name looks long
- Do not keep a visually dense one-line expression merely to avoid wrapping; split the computation into named steps when that exposes data flow better

Line wrapping is a readability decision, not a fixed screen-size rule. The checker does not enforce a universal column count; semantic review must follow the local formatter and surrounding style.
