# Evidence And Final Verification

Read this reference when a quality decision depends on missing or conflicting evidence, or when formatters, generators, test fixes, hooks, or other tools may change files after the initial edit. It governs how to distinguish repository facts from Skill defaults and how to verify the code that actually remains on disk.

## Classify Evidence

Do not treat every nearby example as a project rule. Classify what supports a decision:

- **authority**: explicit user and repository instructions, published API or schema contracts, compatibility commitments, and approved product decisions
- **observed behavior**: current source, executable tests, configuration, call paths, generated output, and reproducible tool results
- **external contract**: official protocol, provider, framework, or dependency documentation confirmed for the version in use
- **local convention**: repeated nearby patterns that are consistent but not declared as a contract
- **recommendation**: a Skill default or engineering preference used when stronger evidence does not decide the issue

Authority defines intended constraints; observed behavior establishes what the system currently does. Neither automatically overrides the other when they conflict. Surface the conflict and its impact instead of selecting whichever source is more convenient. Tests may preserve a bug, source may violate a published contract, and a common local pattern may still be unsafe.

When applying a rule, state material evidence in the reasoning or finding. Do not present a recommendation as an existing repository standard. Examples illustrate a rule; they do not create a universal ban.

## Decide Under Uncertainty

Resolve low-risk, local readability choices using the Skill default and the surrounding style. Ask the user only when missing or conflicting evidence leaves materially different outcomes, including:

- public API, persistence, event, or error-contract compatibility
- authorization, privacy, disclosure, data-loss, or irreversible side effects
- transaction, retry, idempotency, compensation, or resource ownership
- third-party error mapping or logging scope
- a new cross-cutting abstraction or architectural boundary

Before asking, report the evidence found, the unresolved decision, the concrete options, their costs, and a recommendation. If an established extension point or contract already resolves the choice, follow it without pausing.

## Read Back The Final State

The code produced by an edit is provisional until later tools finish. Formatters, code generators, test repairs, IDE actions, Git hooks, and external tools can alter code, filenames, comments, imports, or generated contracts after an earlier review.

After the last mutating tool for the task:

1. reread repository status, the final task-owned diff, and every affected file whose behavior or documentation matters
2. include newly generated, renamed, staged, and untracked files in the task scope
3. recompute reference triggers when the final code introduces a helper, exception, remote call, lifecycle boundary, control-flow change, or other routed concern
4. rerun checks invalidated by the final changes, including compilation, focused tests, and the deterministic style checker where applicable
5. distinguish checks that passed from checks that did not run, could not start, or observed only part of the final surface

Do not claim success from the intended patch, an earlier diff, stale test output, or a hook's exit code alone. If a commit or other tool rewrites files, read back the resulting files and metadata before reporting the outcome. Any later change invalidates the earlier verification for the affected surface.

## Semantic Evaluation

The deterministic checker proves only its documented rules. Use the cases under `evals/` to forward-test whether an agent makes the required semantic decisions without requiring exact wording. A case passes only when all expected decisions are present, no disallowed decision is made, and the answer stays within the stated scope.

Do not describe structural validation of the case file as proof that model behavior passed. Behavioral confidence requires running the cases with a fresh evaluator or manually reviewing the resulting decisions.
