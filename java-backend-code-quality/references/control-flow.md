# Control Flow And Line Wrapping

Read this reference when Java code adds or changes a ternary expression, an `if`, `else`, `for`, `while`, or `do while`, or when a chained call is being wrapped for readability.

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
