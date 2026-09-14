# Remote Calls

Read this reference when changed Java code adds or changes an HTTP, Feign, RPC, or external SDK call; its request or response logging; downstream error parsing or mapping; or the caller-visible failure produced by that call. Apply repository instructions and explicit user choices first. Do not infer permission to record or disclose data merely because a client library can do so.

## Establish The Local Contract

Before coding, inspect the actual remote boundary and nearby repository conventions:

- client configuration, interceptors, filters, aspects, wrappers, SDK logging, retry policy, and global exception handlers
- the logging framework, event shape, levels, masking or truncation utilities, trace or request identifiers, retention, and environment-specific switches
- equivalent integrations, error catalogs, mapping tables, public API contracts, caller behavior, and tests
- the provider's documented transport status, structured business-error fields, request identifiers, and retry semantics

Identify one layer that owns remote-call diagnostics. Verify whether the effective production path covers the request, successful response, structured business rejection, HTTP or RPC failure, invalid response, transport exception, elapsed time, and final outcome after retries. The presence of a logging dependency, DEBUG output, or wire logging is not proof: it may be disabled in production, omit business failures, duplicate higher-level logs, or expose data the repository does not intend to retain.

If existing infrastructure safely supplies the information needed to investigate the call, reuse it and do not print the same request or response again in the business layer. Add only the missing context at the owning boundary.

## Choose The Logging Scope

A useful remote-call record lets an operator correlate the operation and determine what failed. Depending on repository policy, that may include the provider and operation, safe business identifiers, target identity, selected request fields, outcome, HTTP or RPC status, provider error code and message, provider request ID, elapsed time, retry count, and the original technical exception.

Use the repository's logging framework, event format, level conventions, and diagnostic owner. Avoid layered catch-log-throw records for the same failure because they obscure incident counts and ownership.

Do not universally require or prohibit complete URLs, request and response bodies, files, credentials, tokens, or signatures. Decide their inclusion from evidence:

- explicit repository logging, privacy, security, and audit rules
- available masking, access control, environment separation, retention, and production switches
- payload size, binary or file content, and truncation behavior
- whether the value materially improves reproduction or incident diagnosis
- duplicate logs already emitted by the client or infrastructure

When the repository does not make the policy clear, pause before adding or broadening logs. Show the concrete fields and risks, recommend avoiding raw credential or replayable values, and ask the user to choose among relevant scopes such as selected fields, a masked full payload, an original full payload, or failure-only logging. A full-payload option must also settle size limits, binary and file handling, duplication, production enablement, access, and masking. Do not silently enable wire logging or expand an existing production log.

## Preserve Failure Categories

Transport success does not imply business success. Keep these outcomes distinguishable when the provider exposes them:

- client, timeout, connection, or other transport failure
- non-success HTTP or RPC status
- empty, malformed, or incompatible response
- structured business rejection in a successfully transported response
- successful business response

Do not let a broad catch convert a parsed business rejection into a generic technical failure. When converting a technical exception, preserve its `cause` if the local exception contract supports it; otherwise record it once at the diagnostic owner before returning the stable local failure.

A structured business rejection must retain the provider error code, message, request ID, or equivalent distinguishing context in at least one deliberate caller-visible or internal diagnostic path. A local category such as `BUSINESS_REJECTED` and a message such as `Remote call failed` are not sufficient when they erase the only information needed to investigate a support case.

Structured business errors are not automatically equivalent to an unsanitized `exception.getMessage()`. Evaluate the former against the provider contract, intended audience, repository policy, and actual content; continue treating raw technical exception text under [exception-communication.md](exception-communication.md).

## Map Errors Only From Evidence

Map a provider business failure to a local error only when at least one authoritative source defines the relationship:

- an established repository wrapper, mapping table, or integration convention
- a public local error contract, caller branch, or test that requires the local category
- documented provider semantics with a genuinely equivalent local error code
- an explicit product, business, or user decision

Text similarity, a convenient local enum member, or an undocumented substring check is not enough. A provider message prefix may drive mapping only when the provider defines it as a stable machine-readable contract.

When mapping is supported, retain the original provider code, message, and useful request identifier in the repository-designated diagnostic path or structured failure object. Mapping stabilizes the caller contract; it must not destroy evidence.

When no authoritative mapping or disclosure rule exists, do not guess. Present the observed provider fields, the local contract found or missing, compatibility and data-exposure considerations, and a recommendation, then wait for the user to choose among the relevant options:

- preserve the structured provider business error for the caller
- return a stable local error while retaining provider details internally
- introduce an explicit provider-failure type or reviewed mapping

## Example

This loses the only provider explanation even though the remote response was parsed successfully:

```java
if (response.isError()) {
    LOGGER.warn("carrier.order,errorCategory:{}", "BUSINESS_REJECTED");
    throw new BusinessException("Carrier order failed");
}
```

If the repository permits both caller exposure and this diagnostic content, keep the structured failure visible and diagnose it at the owning layer:

```java
if (response.isError()) {
    LOGGER.warn("carrier.order,orderNo:{},providerCode:{},providerMessage:{}",
            orderNumber, response.getErrorCode(), response.getErrorMessage());
    throw new ProviderBusinessException(
            response.getErrorCode(), response.getErrorMessage());
}
```

If a stable local contract requires mapping, use only a confirmed relationship and keep the provider details in the approved diagnostic path. If neither exposure nor mapping policy can be established, stop and ask instead of choosing one implicitly.

## Review Severity

- use the impact-based `P0` or `P1` level for actual credential or personal-data exposure, security failures, or a wrong mapping that breaks a public contract
- use `P2` for erased provider business details, invented mappings, collapsed failure categories, missing production diagnostics, lost technical causes, or logging that creates a material disclosure or operational risk
- use `P3` for redundant but harmless diagnostics or local wording that increases investigation cost without hiding the failure
