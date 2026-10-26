# PRD Business Understanding

Use this skill for PRD-driven planning and implementation. It helps establish old behavior, requested changes, compatibility, and unresolved business decisions, then explains behavior-changing code in context.

Use the user's wording to select the working mode: a clear request to discuss or align the requirement means 一起梳理业务; a clear request for an implementation plan means 直接规划. Ask only when the intent is genuinely ambiguous. Answer narrow questions about current behavior with evidence even before giving a plan.

Before proposing a material decision, inspect current code, tests and formal contracts, and trace the affected entry points. Separate verified current facts, accepted requirements, proposed solutions and unresolved decisions. Preserve existing behavior and contracts unless the user or an accepted requirement changes them. Do not add business restrictions, APIs, locks, retries or stronger failure guarantees just because they seem useful; explain the effect and confirm them first. Prefer existing interfaces and service structure unless they cannot express the accepted behavior.

For the affected scenarios, map current behavior, requested change, compatibility, open decisions and verification. Keep important terms such as order, shipment, package and successful purchase request consistent with the observed counting unit. AI authorship alone neither invalidates nor verifies a PRD statement. When authoritative evidence settles a current-state fact, note the discrepancy and proceed from that evidence. Ask one focused question at a time only for material decisions evidence cannot settle, and continue unaffected work.

During implementation, explain only business-significant changes. Finish with a short mapping from scenarios to changed locations and verification. The skill does not apply to unrelated work or replace existing brainstorming, planning, or code-quality skills.

## Install

PowerShell:

    Copy-Item -Recurse -Force ".\prd-business-understanding" "$env:USERPROFILE\.codex\skills"

Git Bash:

    cp -R ./prd-business-understanding "$HOME/.codex/skills/"

The skill entrypoint is ~/.codex/skills/prd-business-understanding/SKILL.md.

## Semantic evaluation

The evals/semantic-cases.json catalog covers mode selection, evidence provenance, path coverage, contract reuse, scope preservation, concurrency boundaries, terminology and focused implementation explanations. Use a clean evaluation conversation and judge decisions by meaning, not fixed wording. See evals/README.md.

The catalog validator checks structure only. Passing it or Skill Creator's quick_validate.py does not demonstrate model behavior; behavioral evaluation requires running the cases with a model and reviewing its responses.
