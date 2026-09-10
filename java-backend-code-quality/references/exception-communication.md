# Exception Communication

Read this reference when changed Java code throws or converts an exception, returns an error response, writes a failure log, documents a failure contract, or changes a `catch` or `finally` path. Apply repository-specific exception types, error catalogs, localization, logging ownership, and privacy rules first.

## Separate The Audiences

Treat failure communication as three distinct contracts:

- caller-visible error codes and messages help a person or API consumer understand the outcome safely
- internal exceptions and logs help developers or operators locate and diagnose the failure
- source comments explain why the failure path changes control flow and what guarantee is preserved or skipped

Do not ask one message to satisfy all three. A clear `catch` comment does not repair a vague caller message, and a detailed log does not make it safe to return technical details to a caller.

## Caller-Visible Errors

Use the project's established language and domain terms. A caller-visible error should identify the failed subject or action, give the most specific cause the current boundary can state truthfully, and include a next step only when the caller can actually take one.

Reject vague business or interface-layer messages such as `invalid parameter`, `operation failed`, `system error`, or `data not found` when the code knows the field, resource, state, constraint, or action involved. Do not claim a resource is missing when it may instead be disabled or inaccessible; describe the combined contract accurately when the source cannot distinguish those cases.

Keep the error code, exception type, HTTP or RPC status, and human-readable message in the same category. A format violation is not `NOT_FOUND`; a state conflict is not an authentication failure. Preserve established public codes and response shapes unless the task explicitly changes that contract.

Never expose stack traces, Java class or method names, SQL, storage structure, internal URLs, credentials, tokens, secret or personal data, sensitive configuration, or an unsanitized downstream `exception.getMessage()`. Do not invent a trace identifier field, but include the project's existing safe correlation identifier in an outer-boundary fallback when available.

An outermost handler for an unexpected, unclassified failure may return a safe generic message such as `Service is temporarily unavailable; try again later` when it also returns the established stable error code and records the full internal diagnosis. Known validation, state, permission, dependency, and persistence failures still require their specific caller contract.

```java
// Too vague for a known validation failure
throw new BusinessException(ErrorCode.INVALID_ARGUMENT, "Invalid parameter");

// Names the field, constraint, and a real correction
throw new BusinessException(
        ErrorCode.INVALID_ARGUMENT,
        "Callback URL must use HTTPS");
```

## Internal Diagnostics

At the layer that owns failure reporting, record the failed operation or stage, the affected subject, safe business identifiers, relevant state, and the original exception. Include only values needed to distinguish and investigate the incident.

Preserve the original `cause` when converting an internal exception and the project exception type supports it. If the public exception contract cannot retain the cause, log it once at the diagnostic owner before conversion. Avoid catch-log-rethrow at every layer because duplicated logs obscure ownership and incident counts.

Do not log secrets or broad request objects merely to gain context. Use explicit safe fields, and follow repository masking and privacy rules for personal or regulated data.

```java
catch (StorageException exception) {
    // Persistence failure becomes a stable caller error while the original cause remains available internally
    LOGGER.error("Order persistence failed, orderId={}, status={}",
            orderId, orderStatus, exception);
    throw new BusinessException(
            ErrorCode.DATA_ACCESS_ERROR,
            "Order could not be saved; try again later",
            exception);
}
```

## Control-Flow Comments

Keep the `SKILL.md` catch-comment rule independent from message quality. When a catch falls back, retries, suppresses, continues, compensates, or converts an exception, its local comment names the failed operation, the next path, and the guarantee skipped or preserved. Logs and exception messages describe audiences and diagnosis; they do not explain hidden control-flow policy by themselves.

## Review Severity

- use the impact-based `P0` or `P1` level for actual sensitive-data exposure, security failure, or broken public contracts
- use `P2` for unsafe disclosure risk, mismatched error categories, lost causes, misleading recovery advice, or insufficient diagnostics that can block production investigation
- use `P3` when the meaning remains correct and safe but wording creates only local reading or support cost
