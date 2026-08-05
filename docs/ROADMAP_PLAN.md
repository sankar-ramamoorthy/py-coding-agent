---
title: py-coding-agent Product Roadmap
type: canonical-doc
status: draft
project: py-coding-agent
authority: process
created: 2026-08-05
updated: 2026-08-05
canonical: false
related: [py-coding-agent_Lifecycle_Graph_OnePager]
---

# py-coding-agent Product Roadmap

## Source of truth

This document supersedes ad-hoc roadmap discussion from 2026-08-05 and is the place milestone
detail beyond `README.md`'s Milestone 5 lives from now on. `README.md`'s `### Roadmap` section
points here for anything past M5, rather than duplicating milestone detail in two places — the
same drift `README.md`/`README_Skills.md` had before it was fixed earlier this session.

This is a **planning document, not the issue tracker**. [[ISSUES]] (`docs/ISSUES.md`) remains
the authoritative live register of concretely-scoped, actionable work (`ISS-NNN`). This roadmap
groups and prioritizes at a higher level; most candidate items below are not yet filed as real
issues, and promoting one to `ISS-NNN` is a separate, later decision. See also
[[NEXT_ACTIONS]] (`docs/NEXT_ACTIONS.md`) for the current session-to-session action list, and
[[py-coding-agent_Lifecycle_Graph_OnePager]] for the underlying issue→plan→build→merge lifecycle
this repo already runs on.

**Status note:** everything below is `status: draft` — proposed sequencing from one long
planning session (2026-08-05), not yet reviewed or committed to.

---

## Milestone 6 — Reliability Foundation

**Why first:** two independent PM-style passes this session converged on the same conclusion —
the core generate → approve → run loop is still shedding new bugs (`ISS-009`, `ISS-011` both
found in one session), model selection is still unsettled, and there is currently **no CI or
pre-commit enforcement anywhere in this repo**. Nothing downstream (more skills, more providers,
a lifecycle graph) is worth building on top of a foundation that's still finding new failure
modes every session.

| Candidate | Status | Notes |
| --- | --- | --- |
| Minimal CI (`pytest` + `python -m compileall` on every PR) | Not yet filed | Motivated directly by `ISS-005` sitting untriaged since 2026-08-03 with zero automated enforcement — every regression check this session was a human manually running `pytest`. |
| `ISS-005` — root-cause pre-existing test failures | Open, not started | Prerequisite to CI being *green-required*, not just present — can't gate merges on a suite with known, undiagnosed red tests. See [[ISSUES]]. |
| `ISS-006` — declare `pyyaml` as a direct dependency | Open, not started | Small, mechanical. See [[ISSUES]]. |
| `ISS-010` — bare `/provider` falls through to the LLM | Open, not started | Small, well-scoped — usage-message fix in `py_mono/agent/agent.py`. See [[ISSUES]]. |
| `ISS-011` — `generate_skill` fence-stripping + prompt-placeholder-leak fixes | Open, not started | Two code fixes (`py_mono/skill/validator.py`, `py_mono/skill/prompts.py`) plus one non-code investigation (`ollama ps`, possible CPU-bound/unoffloaded inference). See [[ISSUES]]. |
| Model/task fitness check | Not yet filed | Warn before a heavy generation call if the configured model looks like a poor fit for structured output. The clearest "bug we hit → feature that prevents the next one" line of anything discussed this session — directly productizes the `ISS-009`/`ISS-011` lesson (thinking models reasoning verbosely/unreliably on template-filling tasks). |

---

## Milestone 7 — Skill Lifecycle Graph

**What this merges:** three ideas that came up separately this session —
"diff skills on regeneration," "let a failed skill propose its own fix," and the new request to
apply Spec-Driven Development *as a product feature* (what an end user gets when creating a
skill, not just how this repo's own maintainers work) — turned out to be the same underlying
state machine, viewed from three angles. One milestone, not three.

### What already exists (the seed)

`generate_skill`/`create_skill_py` already split a **spec** (`SKILL.md`) from an
**implementation** (`skill.py`), gated by `status: proposed` → `/approve` →
hash-ledger-verified `status: approved` (`SkillRegistry`, ADR-010, ADR-013,
`skills/.approvals.json`). This *is* a two-node instance of spec-driven development — and it's
already product-facing, something the end user does, not just something this repo's
maintainers do internally via `specs/`. It just isn't named or extended yet.

### Proposed extension

Modeled on the "SDLC as a directed cyclic graph" pattern surfaced this session (a pure decision
function separated from a static graph definition separated from persisted state, plus loop
guards against oscillation, plus enforcement living in mechanical checks rather than model
judgment) — which is the same philosophy as the existing hash-ledger approval gate, just
extended across more stages instead of one:

```
Draft(SKILL.md) → Critique → Generate(skill.py) → Validate ──┐
                                    ▲                         │ fail (capped)
                                    └─────────────────────────┘
                                                                │ pass
                                                                ▼
                                                            Propose → Approve → Run
```

- **Critique** — static: does the spec violate ADR-016 tool constraints? Duplicate an existing
  skill? Reuses `validate_skill_md`, doesn't invent a new checker.
- **Validate** — reuses the existing `validate_skill_py` (AST + forbidden-pattern checks),
  unchanged.
- **The fail-loop cap already half-exists**: `generate_skill` already retries once
  (`MAX_RETRIES = 1`) on validation failure. The extension is making that cap and the loop
  explicit and reusable across stages, not inventing retry logic from scratch.
- **Approve** — the existing hash-ledger gate (`ISS-003`'s fix), unchanged. This graph doesn't
  touch the trust boundary, it just gives the stages before it more structure.

### Diff-on-regeneration

When a skill is regenerated, show a diff against the last-*approved* version, not just the raw
new output. Cheap: `skills/.approvals.json` already records the approved hash, and the file's
git history already exists — this is largely a `git diff` against that recorded commit.

### Failure-driven evolution, never self-authorizing

A skill that errors in production can have the agent propose a revised `SKILL.md`/`skill.py`
using the failure as context — but it re-enters `proposed` state. It does not silently patch
itself. Same state machine as first-creation, entered from a different edge.

### Shared dependency: lightweight telemetry

Both M6's fitness check and this milestone's failure-driven evolution need the same thing — a
flat per-run log (`skill`, `provider`, `model`, `duration`, `success`). Build it once, here, not
twice in two different sessions.

---

## Milestone 8 — Skill Provenance & Sharing

The *expensive* half of what got called the "killer feature" this session — deliberately
separated from Milestone 7's cheap half, and explicitly gated.

- Shareable, signed skill packages: full provenance chain (generating model + prompt + approver
  + test results), exportable/importable across installs.
- **Explicitly gated** on the audience question below. Signed packages solve a multi-party trust
  problem — verifying a package from someone else wasn't tampered with — that doesn't exist yet
  for a single-operator tool. Don't build trust/signing infrastructure ahead of having a second
  party to trust.

---

## Gated / deferred — awaiting an audience decision

Grouped together because they share one open question, not because they're equally distant.

> **The open question, stated plainly:** is py-coding-agent a personal tool, or something meant
> for other people to install and use? Nothing below should get real investment until this has
> an answer.

| Item | Note |
| --- | --- |
| `ISS-008` — full isolated-worker execution for skills/dynamic tools | Also a **prerequisite** for Milestone 8 specifically, not just "eventually" — can't credibly ship "revocable, inspectable capabilities" as a trust story while execution is still a hash-ledger + static check, not real isolation. See [[ISSUES]]. |
| Milestone 4 (Polish: docs, full workflow testing, packaging) | The actual next milestone if the answer is "yes, other people should use this." Has sat unstarted in `README.md` since M5 shipped ahead of it. |
| Multi-agent orchestration (planner/coder/tester) | Actively deprioritized this session — adds surface area on top of a core loop that's still shedding bugs. |
| Memory indexing for tools | Genuinely future — matters once skill/tool count makes discovery hard, which it doesn't yet. |
| Additional MCP servers | Genuinely future — only one exists (`datetime`); stress-test the pattern once for real before adding more. |
| Smarter task decomposition | Genuinely future, still vague — kept separate from provider routing (below), which has real evidence behind it. |

**One item pulled *out* of "vague future work" with real evidence behind it now:** ADR-008
(smart provider routing by task type) isn't speculative anymore — this session directly
demonstrated `qwen3.5:4b` failing at structured generation and `qwen2.5-coder:7b-instruct-q5_K_M`
succeeding at the identical task. That's a measured result, not a guess. It's not filed as
`ISS-NNN` yet, but it's a stronger candidate for near-term work than the rest of this table.

---

## What's already sellable (pre-M4)

Worth naming even though it isn't a milestone — this is the honest answer to "what's actually
pitchable today":

1. **Live multi-provider switching, mid-session, no restart** (`/provider <name> [model]`) — most
   comparable tools commit you to one provider config at a time.
2. **The approval gate on generated skills** — `proposed → approved → runnable`, with the spec
   (`SKILL.md`) reviewable independently of the implementation. This is this project's most
   differentiated asset: a governance story (capabilities a human signs off on), not just a
   capability story (an agent that writes and runs code).
3. **Skills as durable, versioned artifacts** — once approved, a skill isn't regenerated every
   session; it's an accumulated, reviewed capability. Compounding, not one-shot.

## Known gaps vs. comparable tools (Cursor, Aider, Continue, OpenHands, SWE-agent)

Named plainly, not to be fixed reflexively — most are legitimately gated on the audience
question above:

- No editor/IDE integration.
- No repo-wide context (embeddings/RAG over the codebase).
- No git-native diff-review workflow for code changes (only for skills, per Milestone 7).
- No sandboxed/isolated execution (`ISS-008`).
- No test-driven iteration loop (agent verifying its own work against tests before requesting
  approval).
- No cost/token observability (folds into Milestone 7's shared telemetry item above).
