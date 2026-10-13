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

### Avoid Mechanical Comments

Before writing a body comment, ask what information it adds: identify the business reason, source boundary, ordering guarantee, compatibility role, selection policy, or failure consequence a reader would otherwise have to infer. For self-explanatory code without a documentation obligation, omit a comment that adds nothing.

Apply a deletion test after drafting: would removing the comment lose useful information? Remove redundant optional body comments; rewrite required JavaDoc, guard-cluster, behavior-changing catch, and hidden-stage explanations instead of deleting their coverage. Clear names or a linear body do not exempt an independent action from JavaDoc. A comment that could be pasted above unrelated code without becoming false is too generic. Length or visual spacing alone does not justify comments.

One precise comment can explain several statements enforcing the same invariant. Independent preparation, remote execution, persistence, or response stages still need their own explanations when their hidden contracts differ. Improve names or types when they express the missing fact better; do not extract trivial helpers merely to replace comments.

## Write Clear, Natural Wording

Check both factual content and wording while writing each stage and during final readback. A useful fact can still be expressed mechanically.

- Name the actual object and action. Replace ambiguous subjects such as "状态", "结果", "该阶段", or "后续逻辑" when the reader cannot tell which value or operation they mean
- Use ordinary project language. Expressions such as "消费结果", "承接状态", or "收敛逻辑" are examples of potentially vague wording, not banned words; retain established domain terms when they accurately identify a concept
- State one main point first. Add a second sentence or line when another necessary condition would overload it; preserve qualifiers rather than shortening away null behavior, ordering, compatibility, or failure guarantees
- Explain a specific rule directly. Do not force every sentence into "为了...先...避免...", write numbered stage labels, or paraphrase method names. Genuine causal statements and necessary negative guarantees remain valid
- Verify claims against implementation, callers, tests, configuration, or a confirmed contract. Never invent a business reason, automatic retry, atomicity, or recovery guarantee to make prose sound purposeful. If the reason is unknown, investigate it; describe only supported behavior and ask when the unresolved choice affects correctness
- JavaDoc starts with a concise description of the action or contract, without padding such as "本方法用于". Describe meaningful inputs, absence behavior, outputs, side effects, and errors as applicable; do not fill a fixed checklist with irrelevant sentences. Preserve tags required by repository documentation rules

Read the comment with its code as a maintainer who did not participate in the task. They should identify the object, rule, and supported consequence in one pass without guessing pronoun references or translating abstract prose. Wording improvements must not change the documented behavior.

Examples below assume the stated behavior is established by the code and contract; they are not phrases to paste into unrelated code:

```java
// Vague: 完成校验后执行后续持久化逻辑
// Specific: 全部明细校验通过后再保存，任一明细无效时不写入订单

// Vague: 异常时执行降级处理，保证主流程正常进行
// Specific: 缓存写入失败仍返回渠道结果，不重试缓存写入

// Dense: 消费当前有效状态完成结果收敛并维持接口输出一致性
// Specific: 将渠道响应转换为调用方约定的响应格式，保留渠道返回的业务错误
```

## Sources And Local Choices

These rules adapt Robert C. Martin's public [redundant-comment guidance](https://www.informit.com/articles/article.aspx?p=1327761), [poorly-written-comment guidance](https://www.informit.com/articles/article.aspx?p=1328957), and [obsolete-comment guidance](https://www.informit.com/articles/article.aspx?p=1326509), alongside [Google's JavaDoc guidance](https://google.github.io/styleguide/javaguide.html#s7-javadoc) and [Oracle's API documentation guidance](https://www.oracle.com/technical-resources/articles/java/javadoc-tool.html). They support informative, concise wording, accurate maintenance, and caller-visible contracts. Reading those pages is not a task prerequisite. This Skill's independent-action JavaDoc coverage and punctuation preferences are local choices, not universal requirements attributed to these sources.

## Describe The Current Contract

Write comments from the accepted current behavior and invariant, assuming the reader did not see the implementation history or working discussion. Do not make a superseded implementation, rejected option, old field, or unused input the center of a comment merely because it was considered during the change.

Treat wording such as "X is not used", "X does not participate", "only Y", or "instead of X" as a prompt to check relevance, not as an automatic violation:

- if X no longer affects the current contract and omitting it cannot mislead a maintainer, remove the comparison and state the positive rule directly
- if X still exists for deserialization, stored-data compatibility, public API stability, migration, fallback, or another current constraint, retain the fact and explain X's present role rather than only saying what it does not do
- if the explanation is only a record of how the implementation changed, keep it in Git history, a migration note, or a decision record instead of an inline code comment
- if coexistence remains confusing, improve the name, type, deprecation marker, validation, or code structure rather than relying on a historical aside

Necessary negative guarantees remain valid. State that a failure path skips a cache write, a branch must not publish, an input is intentionally unsupported, or a compatibility field is excluded when that fact changes caller expectations, safety, ordering, or future maintenance. The test is whether a reader without the change history needs the exclusion to understand or safely modify the current code, not whether the sentence contains negative wording.

For example, prefer `// Select the request encoder from the resolved content type` over `// Only the resolved content type selects the encoder; legacyFormat is not used`. If `legacyFormat` is still accepted for stored-data compatibility, say `// Select the request encoder from the resolved content type; legacyFormat is retained only when reading stored configurations`.

## Comment Maintenance

Remove or update comments when behavior, ownership, or ordering moves. Describe an operation as atomic only when a transaction primitive, lock, or compare-and-set contract actually guarantees atomicity.

## Formatting And Severity

An unsupported claim about retries, state, ordering, compatibility, or failure guarantees is graded by its actual maintenance or behavioral risk, normally P2 when it can cause a wrong change. Wording that obscures an object or condition is P3 when it only adds local reading cost. Another equally accurate, readable phrasing is not a finding; explain a concrete ambiguity before reporting prose style.

Absent a stronger user or formal repository rule, Java comments, including JavaDoc and method-body comments, do not end with `。` or `.`, and exactly one blank line separates method declarations. These are default preferences: follow the project's formatter and documentation requirements when they differ. Inspect changed-scope checker reports against that authority; an overridden preference is not a violation.

Missing method JavaDoc is `P2` when it hides lifecycle, state, side effects, failure policy, timing, or another contract. Otherwise use `P3` for an independently named action. Missing stage or branch comments are `P2` when they hide ordering, compatibility, selection, error classification, side effects, or failure guarantees; use `P3` when they only add local reading cost. A historical comparison is `P2` when it misstates current compatibility or can cause a wrong change, and `P3` when it only distracts from an otherwise clear current rule. Punctuation, method spacing, and wrapping findings are at most `P3`.
