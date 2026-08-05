---
title: py-coding-agent Lifecycle Graph — One-Pager
type: raw-note
status: draft
project: py-coding-agent
authority: process
created: 2026-08-05
updated: 2026-08-05
canonical: false
related: []
---

# py-coding-agent Lifecycle Graph — One-Pager

## Source context

Captured from a conversation prompted by a blog post ("Pipeline," Valor Engels) describing an
agentic-SDLC control system — Issue → Plan → Critique → Build → Test → Review → Docs → Merge,
modeled as a directed cyclic graph with typed failure edges and enforcement living outside the
model's own memory/context — and two AI critiques of that post. This note is scoped entirely to
`py-coding-agent` itself. No other project is referenced; this is not a cross-project comparison.

This is a raw capture, not yet reviewed or promoted — see
[[../../docs/promotion]] for what that process looks like.

## The implicit lifecycle graph

`py-coding-agent` already follows something close to this shape, expressed through documented
convention rather than an executable graph engine:

```
Idea
  → Issue registered (docs/ISSUES.md)
  → Spec Kit specify/plan/tasks (specs/<NNN>-<slug>/)
  → Plan review (plan-mode + AskUserQuestion clarification gates)
  → Implementation (topic branch)
  → Validation (pytest; SkillRegistry approval check for any skill work)
     ├── fail → Patch (corrective commit, same branch)
  → Review (PR)
     ├── blocker → Patch
  → Docs reconciliation (ADRs, SESSION_LOG.md, PROJECT_STATUS.md, NEXT_ACTIONS.md)
  → Merge (PR into main)
  → Continuity update (next session reads SESSION_LOG.md / CURRENT_FOCUS.md)
```

## Node types

Applying the four-node taxonomy from the Valor Engels post to this repo's actual stages:

| Node type | Examples in this repo |
| --- | --- |
| Human/governance | Issue authorship in `docs/ISSUES.md`; PR review and merge (merging is not available to Claude Code in this environment — see below) |
| Agentic reasoning | Spec Kit `/speckit-specify` / `/speckit-plan`; plan-mode design; code review commentary |
| Deterministic operation | `pytest`; `SkillRegistry.is_approved()` gate check; `write_file`/`edit_file` sandbox path validation |
| External system action | `git push`; `gh pr create`; `docker compose build` |

## Where enforcement already lives outside model memory

Two concrete, code-level examples already exist in this repo — not proposals:

- **Skills approval gate (ADR-010, ADR-016).** Each skill's `SKILL.md` carries
  `status: proposed` or `status: approved`. `SkillRegistry` checks this at runtime; a proposed
  skill cannot execute no matter what the LLM decides to do. The rule lives in code, not in a
  prompt the model has to remember to follow.
- **Sandbox path enforcement.** `write_file` and `edit_file` validate that target paths stay
  under `workspace_root` before writing, independent of the model's stated intent (see
  README.md's "Sandboxed Execution" section).

A third example was observed directly in this session rather than read from the codebase: `gh pr
merge` is blocked for Claude Code by the harness's own permission classifier — a merge gate
enforced at the harness level, not something the model is trusted to self-restrict on.

## Open questions / not yet settled

These are proposals to evaluate, not conclusions:

- **Who audits the enforcement itself?** A code-level gate (like the skills approval check) can
  silently rot — e.g., a bug that always returns `approved`. Any future automation here needs an
  answer for who/what checks the checker, not just more layers of gating.
- **Should `AGENTS.md`'s "Protected Areas" and "Agent Operating Constraints" sections move from
  documented convention to code-enforced checks**, the way the skills gate already has? Right
  now those sections rely on the model reading and following them each session — the same
  failure mode the skills gate was built to avoid.
- **Is it worth formalizing this graph as an executable state machine at all**, or does the
  current mix of documented convention (`AGENTS.md`) plus two hard code-level gates already give
  most of the benefit at much lower cost? No decision made here either way.

---

See [[../../docs/promotion]] for how this note would move to `knowledge/processed/` or
`knowledge/topics/` if it's reviewed and settled into something more durable.
