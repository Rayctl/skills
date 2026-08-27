# Contracts And Lifecycles

Read this reference only when changed Java backend code coordinates multiple stages, side effects, resources, transactions, remote calls, asynchronous work, retries, caches, compensation, concurrency-sensitive writes, or non-obvious caller-visible failure policies. Return to `SKILL.md` without applying this reference when the change is a trivial accessor, data holder, pure predicate, or mechanical edit with none of those concerns.

## Reconstruct The Behavior

Write down the actual stages before judging individual methods. A common shape is:

```text
entry -> resolve inputs/state -> validate -> transform -> execute side effects -> persist/publish -> respond
```

Treat consecutive calls as separate stages when they change processor responsibility, hand an intermediate result to the next operation, or introduce a different side-effect, ordering, or failure boundary. A shared receiver does not merge those stages. At the call site, add a separate intent comment immediately before each stage so the reader can see why the preparation or mapping result is produced, why execution waits for it, and which later stage consumes the result. Keep one comment for multiple calls only when their purpose, precondition, result consumer, and failure semantics are genuinely cohesive

For each stage, identify:

- input ownership and null, empty, absent, disabled, and default semantics
- output contract and the next consumer
- state or configuration snapshot used
- validation owner and caller-visible failure behavior
- resource, transaction, retry, and cleanup owner
- authentication, authorization, and idempotency boundaries
- ordering constraints before irreversible side effects
- synchronous, asynchronous, and cross-module boundaries

Trace the happy path and meaningful absence, rejection, concurrency, and failure paths. Do not assume another layer enforces a contract without tracing the real call path.

## Correctness And Contracts

Check for behavior that can change caller-visible results:

- inconsistent absence contracts across layers
- branch ordering that changes the result or error
- ambiguous null, empty, disabled, absent, and default semantics
- stale or mixed state snapshots
- validation against a different state than the state eventually written
- authentication or authorization against the wrong identity or after a protected side effect
- retries, callbacks, or concurrent requests that can repeat non-idempotent work
- persistence conditions that fail to repeat concurrency-sensitive preconditions
- transaction or asynchronous boundaries that outlive state or resources they depend on
- timeout, retry, and circuit-breaker layers that multiply attempts or obscure the final failure owner

Confirm contracts from source, repository documentation, or supplied configuration. Label runtime assumptions that cannot be verified.

## Resource And Side-Effect Lifecycles

Assign each resource and delayed action to one visible owner:

- release locks and temporary resources on success, rejection, conversion failure, and unexpected exceptions
- give delayed persistence, publication, or cache candidates one final consumer
- prevent `finally` cleanup from duplicating deeper cleanup or masking the original failure
- perform admission or commit only after all required conditions succeed
- avoid holding a lock across remote I/O unless the contract explicitly requires it
- align transaction propagation with the actual unit of work
- do not let asynchronous work depend on a caller transaction or request resource that has ended
- expose compensation boundaries and crash windows when side effects cannot be atomic
- bound outbound calls and make retries consistent with idempotency

Prefer a visible acquire/use/commit-or-cancel lifecycle. Flag cleanup or compensation spread across unrelated layers when ownership becomes ambiguous.

## Validation Ownership

Locate one authoritative owner for each rule:

- distinguish unconditional protocol or safety checks from optional data-shape validation
- do not duplicate downstream validation unless the current layer owns a different caller-visible contract
- retain validation that protects irreversible side effects, security, cache safety, or persistence consistency
- make validation paths and messages identify the real caller-visible field or state
- keep configuration-time and runtime semantics aligned when they enforce the same rule
- when validation is non-blocking, ensure its result controls only the intended later action

## Deep Verification

Map tests to the changed contracts and lifecycles that apply:

- null, empty, absent, disabled, invalid, and default cases
- expected fallback or degradation versus unexpected exception propagation
- retry, timeout, repeated-attempt, and idempotency behavior
- lock release, cleanup, commit, cancel, and compensation paths
- concurrent state changes enforced at the final side-effect boundary
- authentication and authorization rejection before protected work
- transaction rollback, propagation, and asynchronous boundaries
- stale references after behavior, names, or ownership move
