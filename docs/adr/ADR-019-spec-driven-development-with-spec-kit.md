# ADR-019: Spec-Driven Development with GitHub Spec Kit

## Status

Accepted

---

## Context

This repo is developed by both human contributors and AI coding assistants (Claude Code,
Codex CLI — see `AGENTS.md` / `CLAUDE.md`). Until now there was no structured, agent-facing
workflow for planning an individual feature before writing code: contributors went straight
from idea to implementation. `docs/adr/` exists, but it is reserved for standing architecture
decisions that outlive any single feature (per its own established use across ADR-001 through
ADR-018), not for feature-level planning artifacts.

Separately, ADR-018 ("Project Scaffold and Requirements-Driven Workflow") describes an
unrelated concern: a *product* feature where py-coding-agent itself offers requirements-driven
scaffolding to its own end-users. This ADR is not that — it concerns the workflow used by
contributors (human or AI) to develop py-coding-agent itself.

## Decision

Adopt [GitHub Spec Kit](https://github.com/github/spec-kit) (pinned to `v0.15.1`) as the
feature-planning layer for this repo's own development workflow.

Installed and scaffolded as follows:
- `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.15.1`
- `specify init --here --integration claude --script sh --force`
- `specify integration install codex`

This produced:
- `.specify/memory/constitution.md` — hand-authored to mirror AGENTS.md's Agent Operating
  Constraints, Protected Areas, Change Philosophy, and Testing Guidelines, so Spec Kit's own
  `/speckit-plan` and `/speckit-tasks` steps are grounded in this repo's existing conventions.
- `.specify/templates/`, `.specify/scripts/bash/` — vendored upstream assets, not hand-edited.
- `.claude/skills/speckit-*/SKILL.md` — Claude Code integration, invoked as `/speckit-<name>`.
- `.agents/skills/speckit-*/SKILL.md` — Codex CLI integration, invoked as `$speckit-<name>`.

Workflow: `/speckit-specify` → (optional `/speckit-clarify`) → `/speckit-plan` → (optional
`/speckit-checklist`) → `/speckit-tasks` → (optional `/speckit-analyze`) → `/speckit-implement`.
Artifacts land in `specs/<NNN>-<slug>/` (spec.md, plan.md, tasks.md), one directory per
feature.

`docs/adr/` and `specs/` coexist for different purposes: ADRs remain the record of standing
architecture decisions; Spec Kit specs are scoped, per-feature planning artifacts. `AGENTS.md`
was updated with a short "Feature Planning with Spec Kit" section pointing to this workflow.

## Alternatives Considered

- **Hand-author an in-house spec template under `docs/`.** Rejected — would require building
  and maintaining our own agent-invocable skill definitions for both Claude Code and Codex CLI
  from scratch, duplicating what Spec Kit already provides and tests upstream.
- **Write specs as plain Markdown docs, reviewed like ADRs, with no tooling.** Rejected — loses
  the main benefit of Spec Kit: a structured, invocable `/speckit-*` workflow that both AI
  assistants can drive directly, rather than a document format alone.

## Invariants

- `.specify/templates/` and `.specify/scripts/` are vendored; do not hand-edit — update via
  `specify integration upgrade` instead.
- `.specify/memory/constitution.md` MUST stay consistent with AGENTS.md's Agent Operating
  Constraints and Protected Areas; update both together when either changes.
- Spec Kit's `specs/` artifacts do not replace `docs/adr/` — a feature spec is not a substitute
  for recording a standing architecture decision, and vice versa.

## Relationship to Previous ADRs

- Unrelated to ADR-018, which is a *product* feature (py-coding-agent's own requirements-driven
  scaffolding workflow for its end-users), not a repo development-process decision.
- Does not modify or supersede any prior ADR's architectural decisions; this ADR only adds a
  planning workflow layered on top of existing practice.

## Consequences

### Positive

- Contributors (human or AI) get a consistent, discoverable path from feature idea to
  implementation, invocable directly from Claude Code and Codex CLI.
- `.specify/memory/constitution.md` gives Spec Kit's plan/tasks generation explicit visibility
  into this repo's existing constraints (sandboxing, `Tool.run` interface, no unapproved
  frameworks, etc.), reducing the risk of generated plans proposing changes AGENTS.md already
  forbids.
- No collision with the repo's own `skills/` framework (`py_mono/skill/base.py` only reads the
  top-level `skills/` directory) or with ADR-018's unrelated product feature.

### Negative

- Adds an external dependency (`specify-cli`, pinned to v0.15.1) that must be tracked for
  updates; upstream template/CLI layout has already changed between versions (e.g.
  `.claude/commands/*.md` → `.claude/skills/*/SKILL.md`), so paths/flags should be
  re-verified against `specify --help` when upgrading.
- Two parallel per-agent skill trees (`.claude/skills/`, `.agents/skills/`) must be kept in
  sync on upgrade (`specify integration upgrade`).
- `.specify/memory/constitution.md` and `AGENTS.md` now encode overlapping rules in two
  places with no automated consistency check — drift is possible if one is edited without the
  other.
- Contributors must now know to check two places — `specs/` for feature-level planning and
  `docs/adr/` for standing decisions — instead of one.

## Implementation Notes

Implemented 2026-08-03:
1. `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.15.1`
2. `specify init --here --integration claude --script sh --force`
3. `specify integration install codex`
4. Hand-authored `.specify/memory/constitution.md`
5. Added "Feature Planning with Spec Kit" section to `AGENTS.md`

## Follow-ups

- Consider a lint/CI check that flags when `AGENTS.md` and `.specify/memory/constitution.md`
  diverge.
- ADR-018's own "Follow-ups" section informally referred to a future "ADR-019: session startup
  sequence (auto-run `understand-workspace` on agent init)". That number is now used by this
  ADR instead; the session-startup-sequence decision, if written, should take ADR-020 or later.
