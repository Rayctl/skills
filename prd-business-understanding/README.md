# PRD Business Understanding

Use this skill for PRD-driven planning and implementation. It helps establish old behavior, requested changes, compatibility, and unresolved business decisions, then explains behavior-changing code in context.

At the start of a task, ask the user to choose 一起梳理业务 or 直接规划 unless they have explicitly chosen one for that task. Both paths compare current behavior with the PRD. Collaborative clarification asks one material question per turn and waits for the answer. Direct planning labels evidence and assumptions and still confirms unresolved decisions that could change behavior or contracts.

Treat the PRD as a source of requested product intent, not automatic proof that its claims about current facts or proposed solution are correct. Verify material claims against the appropriate source: current code and tests for existing behavior, current formal contracts for interface details, and an accepted user or product decision for unclear or conflicting desired behavior. AI authorship alone neither invalidates nor verifies a statement. When authoritative evidence settles a current-state fact, state the PRD discrepancy and use the verified fact. When sources leave a material business, contract, or failure decision unresolved, explain the impact and ask one focused question before proceeding with dependent decisions.

During implementation, explain only business-significant changes. Finish with a short mapping from scenarios to changed locations and verification. The skill does not apply to unrelated work or replace existing brainstorming, planning, or code-quality skills.

## Install

PowerShell:

    Copy-Item -Recurse -Force ".\prd-business-understanding" "$env:USERPROFILE\.codex\skills"

Git Bash:

    cp -R ./prd-business-understanding "$HOME/.codex/skills/"

The skill entrypoint is ~/.codex/skills/prd-business-understanding/SKILL.md.

## Semantic evaluation

The evals/semantic-cases.json catalog covers mode selection, evidence provenance, factual-claim verification, conflicts, compatibility, related but independent PRDs, interface-document boundaries, and focused implementation explanations. Use a clean evaluation conversation and judge decisions by meaning, not fixed wording. See evals/README.md.

The catalog validator checks structure only. Passing it or Skill Creator's quick_validate.py does not demonstrate model behavior; behavioral evaluation requires running the cases with a model and reviewing its responses.
