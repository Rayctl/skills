# Deterministic Style Checker

Read this reference when using `--base`, `--line-range`, or `--exclude`, when scope cannot be established, or when checker errors, exact CLI behavior, or rule identifiers need investigation. Default worktree and explicit-path checks can run without loading it.

## Commands

Use the checker on changed Java files, selected ranges, or explicit paths:

```text
py -3 "<skill-directory>\scripts\check_java_backend_style.py" --changed [--base <ref>] [--repo <path>] [--exclude <path>]... [paths...]
py -3 "<skill-directory>\scripts\check_java_backend_style.py" --line-range "<file>:<start>-<end>" [...]
py -3 "<skill-directory>\scripts\check_java_backend_style.py" [--exclude <path>]... <full-path> [<full-path>...]
```

`--changed` selects staged, unstaged, and untracked Java changes after `HEAD`. With `--base`, select the merge-base between that ref and `HEAD` through the current worktree. Positional paths narrow the selected files. In changed mode, resolve relative paths and exclusions from `--repo`; in explicit-path mode, resolve them from the current directory.

`--line-range` checks only the supplied changed lines and cannot be combined with `--exclude`. Method-level findings are reported when the selected range intersects the containing method. Exclusions win over inclusion, may name absent files, do not accept globs, and must resolve inside the selected repository where applicable.

The checker is read-only. It must not infer authorship by scanning the whole project or report unrelated historical, generated, or vendored code. Read surrounding code only as context. If Git cannot establish a safe change surface, require an explicit baseline instead of guessing.

## Rule Identifiers

- `STYLE-COMMENT-001`: a Java comment ends with `。` or `.`
- `STYLE-METHOD-001`: adjacent method declarations are not separated by exactly one blank line
- `STYLE-CATCH-001`: a behavior-changing `catch` lacks a local intent comment before the changed behavior
- `STYLE-GUARD-001`: at least three terminating method-entry guards lack one leading cluster comment
- `STYLE-INTENT-001`: a method with at least 15 non-blank code lines and three control-flow nodes has no top-level stage intent comment
- `STYLE-BRACE-001`: an `if`, `else`, `for`, `while`, or `do while` body is not enclosed in braces

The guard rule permits pure local-value extraction between guards. `STYLE-BRACE-001` ignores comments, strings, text blocks, and the `while` condition belonging to a `do while` statement. JavaDoc, logs, catch-local comments, and nested comments do not satisfy the top-level intent rule. The checker conservatively detects complete absence only; it cannot judge comment quality, stage coverage, whether adjacent calls belong to separate processor stages, whether a private helper should be written out at its use sites at any reference count, whether a reuse-only message constant should remain visible at its failure sites, whether current variation justifies a design pattern, or whether a ternary expression is harder to read than an `if`. It also cannot determine a change's semantic neighborhood, relationships between fields without direct references, or the diagnostic purpose of legacy logs. Error-message audience or clarity, distinguishable causes, recovery actions, error-code alignment, diagnostic sufficiency, sensitive-information disclosure, remote-call log coverage, raw-payload policy, failure classification, mapping evidence, and downstream diagnostics require semantic skill review. Reference counts, call-site readability, structure choice, line wrapping, retries, suppression, compensation, degradation, and other semantic decisions also require skill review.

## Exit Codes

- `0`: no violations for the selected scope
- `1`: one or more violations, with file, line, rule identifier, and evidence
- `2`: usage, input, path, Git, or environment error

Excluding every selected Java file is clean and must produce a clear message. Run semantic review separately for lifecycle, naming, and comment-quality decisions that are outside deterministic checks.
