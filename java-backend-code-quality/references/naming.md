# Java Naming Reference

Read this reference when an added or changed name uses generic vocabulary, an enum lookup is added or changed, a rename is under review, or a caller cannot understand the complete responsibility from the call site. Do not load it merely because a change introduces otherwise clear identifiers.

## Call-Site Test

Read only the receiver, method name, parameter roles, return type, and result use. The call site should reveal:

- the concrete subject, product, or decision
- the primary action and meaningful result or state change
- persistence, remote I/O, transaction, compensation, fallback, retry, or other caller-relevant side effects

Do not make the caller depend on an implementation jump or JavaDoc to learn the basic responsibility. A clear receiver may supply one unambiguous subject, but `Batch`, `List`, `Data`, `Info`, `Context`, `Item`, and `Result` describe shape only.

Apply the same semantic check to fields, parameters, and local variables. When the type does not fully identify the value, the name should reveal its data, state, source, scope, or intended consumer. Do not use generic carriers merely because the static type is broad.

## Generic Actions

Generic verbs need a concrete subject, product, rule, or outcome:

- construction: `build`, `create`, `make`, `prepare`, `generate`
- conversion: `convert`, `map`, `transform`
- lookup or decision: `get`, `find`, `query`, `load`, `resolve`, `check`, `validate`
- mutation: `save`, `update`, `delete`, `apply`, `merge`, `sync`, `refresh`, `finalize`
- orchestration: `process`, `handle`, `execute`, `run`

Apply the action to the actual contract:

- `build` names the concrete product and primarily constructs it; a business-input `XxxBuilder#build(...)` is not automatically exempt
- `convertToXxx` and `mapToXxx` name a concrete target shape and use `To`, not `2`
- `transform` names the actual transformation or target form; adding only a broad subject is insufficient when the action remains unknown
- boolean decisions prefer `is`, `has`, `can`, or `should`; throwing validation names the checked object or contract, such as `validateRequestContract`
- mutation and orchestration names identify their target and must not disguise persistence, remote calls, transactions, compensation, or degradation as ordinary calculation
- a shape or quantity suffix does not make a name specific: `saveBatch`, `buildData`, and `processList` remain unclear

## Avoid Normalize

Do not introduce application-defined identifiers based on `normalize`, `normalized`, or `normalizer`. These words claim that a value becomes normal without revealing the rule, changed fields, defaults, ordering, filtering, or resulting state.

Name the observable operation or result instead:

```text
normalizeSystemContext -> fillMissingSystemIdentity
normalizeHeaderNames   -> convertHeaderNamesToLowerCase
normalizeCodes         -> trimAndDeduplicateCodes
normalizePath          -> removeDuplicatePathSeparators
normalizedConfig       -> configWithResolvedDefaults
```

Do not merely replace `normalize` with `standardize`, `canonicalize`, `sanitize`, `adjust`, or `process`; those words require the same concrete operation or named contract. Retain normalization terminology only when a framework or external signature requires it, or when a named technical standard defines normalization as the actual operation, such as Unicode NFC or URI normalization. Calls to third-party APIs keep their published names.

Report ambiguous normalization vocabulary as `P2` when it hides defaults, security filtering, compatibility behavior, state mutation, or another caller-relevant contract; otherwise use `P3` for local understanding cost.

## State And Collection Names

State suffixes and prefixes are contracts, not generic labels. Use `candidate` only while an item belongs to a deliberately broad set and still awaits an explicit selection rule. Include the subject, scope, and container, such as `routeCandidateList`; do not use bare `candidates`. Replace it when the value is actually a condition builder, an already-filtered result, or an ordinary loop item:

```text
candidates -> routeConditions   // lambda parameter that builds route predicates
schemaCandidates -> activeSchemaList   // query already returned active schemas
for (Schema schemaCandidate : activeSchemaList) -> for (Schema schema : activeSchemaList)
```

Application-internal collection variables include their concrete container suffix so later uses remain understandable without returning to the declaration:

- `List<T>` uses `...List`, such as `requestedAppList`
- `Set<T>` uses `...Set`, such as `requestedAppCodeSet`
- `Map<K, V>` and `Map<K, Collection<V>>` use `...Map`

The suffix does not replace semantic naming. Put the subject, established state or source, and map key relationship before it; `dataList`, `itemSet`, and `appMap` remain insufficient. Do not add a container suffix to a serialized field, public API contract, framework signature, or third-party identifier when renaming it would alter compatibility.

Names should also reveal collection cardinality and lookup state. For an index-style map:

- use a singular value noun for one value per key: `Map<Code, Schema> activeSchemaByCodeMap`
- use a plural value noun only when each key maps to multiple values: `Map<Code, List<Schema>> schemasByCodeMap`
- include meaningful state such as `active`, `validated`, `pending`, or `latest` only after the code establishes it

When building an index with `put`, `putIfAbsent`, `Collectors.toMap`, or similar operations, inspect the duplicate-key contract. Duplicates must be impossible by an enforced invariant, rejected, grouped, or resolved by an explicit deterministic rule. If first, last, latest, or highest-priority selection is intentional, make the ordering stable and expose that choice in the name or adjacent intent comment; a neutral `valueByKeyMap` name must not hide arbitrary collision resolution.

When the same query result is subsequently looked up two or more times by one stable business key and the relationship is one value per key, prefer constructing one named map over repeated list scans or a trivial `findXxxByKey` helper. This exposes the access contract at each `get` call and keeps the lookup logic local. Do not convert mechanically when there is only one lookup, encounter order matters, duplicates are meaningful, or the code naturally consumes every element once. `stream().collect(...)` is not required; choose the clearest construction and make duplicate-key behavior deliberate.

For example, a query for several applications followed by repeated `appCode` lookups should normally produce `appByCodeMap`. Before collecting, verify that `appCode` is unique; otherwise reject duplicates, group them, or apply an explicit stable selection rule rather than silently keeping an arbitrary value.

Report a hidden or nondeterministic selection policy as `P2`. Use `P3` when the data contract is sound and only the state, role, or cardinality is unclear from the identifier.

Typical corrections include:

```text
OutboundRequestUrlBuilder#build(config, request) -> buildOutboundRequestUrl
saveBatch                                      -> saveApiConfigChanges
convert                                        -> convertToApiUpdateBO
map                                            -> mapToResponse
```

## Enum Lookups

Inspect nearby enums and repository conventions before choosing a name. Do not assume one global Java convention.

- return the enum value with a local convention such as `getByCode`
- return a property with a result-plus-key name such as `getDescByCode` or `getNameByCode`
- if the repository uses `find` for optional lookup, write `findByCode`; a bare `find` hides the key
- reserve `valueOf` for Java enum-constant-name semantics unless the repository defines a distinct, unambiguous API
- when multiple fields identify the value, include the caller-relevant fields or use an established identity concept

Missing-value behavior follows the repository contract. Make `null`, `Optional`, or throwing-on-missing behavior explicit through the return type, nullability annotation, JavaDoc, or exception contract. Do not change absence semantics solely to improve the name.

## Short-Name Exemptions

A short name is acceptable when its contract is already fixed and unambiguous:

- interface overrides and framework callbacks whose signature cannot be renamed, such as `run`, `handle`, or `execute`
- a standard single-product `Builder#build()` with accumulated state, no business input, and no multi-stage orchestration
- `create`, `save`, `update`, or `delete` on a clearly named `Repository`, `Mapper`, or `DAO` for the conventional single-store operation
- Java, JDK, or third-party methods such as `toString`, `toBuilder`, and `toInstant`

A persistence abstraction that coordinates cross-store writes, compensation, or another special lifecycle must expose that responsibility despite its receiver name.

After implementation, re-read the primary call sites and rename a method if its basic responsibility is not evident there. Split or expose a stage when a generic name hides unrelated actions.

Report a misleading name as `P2` when it hides persistence, absence, exception policy, or lifecycle and could cause misuse. Use `P3` when it mainly adds navigation or local reading cost.
