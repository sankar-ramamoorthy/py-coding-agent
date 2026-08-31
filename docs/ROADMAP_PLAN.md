---
title: py-coding-agent Product Roadmap
type: index
status: draft
project: py-coding-agent
authority: process
created: 2026-08-05
updated: 2026-08-05
canonical: false
related: [ISSUES, NEXT_ACTIONS, py-coding-agent_Lifecycle_Graph_OnePager]
---

# py-coding-agent Product Roadmap

## Purpose

This document supersedes ad-hoc roadmap discussion from 2026-08-05 and is where milestone
detail beyond `README.md`'s Milestone 5 lives from now on. `README.md`'s `### Roadmap` section
points here for anything past M5, rather than duplicating milestone detail in two places — the
same drift `README.md`/`README_Skills.md` had before it was fixed earlier this session.

**Status note:** everything below is `status: draft` — proposed sequencing from one long
planning session (2026-08-05), not yet reviewed or committed to.

## Authority Model

This roadmap groups and prioritizes at a milestone level. It is **not** the issue tracker —
most candidate items below are not yet filed as real issues, and promoting one to `ISS-NNN` is
a separate, later decision.

| Layer | Responsibility |
| --- | --- |
| `docs/ROADMAP_PLAN.md` (here) | Milestone sequencing, priority, and the reasoning behind it |
| [[ISSUES]] (`docs/ISSUES.md`) | Authoritative live register of concretely-scoped, actionable work (`ISS-NNN`) |
| [[NEXT_ACTIONS]] (`docs/NEXT_ACTIONS.md`) | Current session-to-session action list |
| `docs/adr/` | Standing architecture decisions that outlive any one feature |
| `specs/` | Spec Kit per-feature plans (spec → plan → tasks) |
| [[py-coding-agent_Lifecycle_Graph_OnePager]] | The underlying issue→plan→build→merge lifecycle this repo already runs on |

## Milestone Index

| Milestone | Status | Theme |
| --- | --- | --- |
| M6 | Done | Reliability foundation — CI, open-bug cleanup, model/task fitness check |
| M7 | Core complete, closeout partly complete | Skill lifecycle graph — Critique/Test stages, diff-on-regen, failure-driven evolution, durable reports |
| M8 | Draft, gated | Skill provenance & sharing — signed packages, gated on the audience question |
| Gated/deferred | Awaiting decision | Everything blocked on "personal tool vs. multi-user" |

---

## M6 — Reliability Foundation

**Status:** Done — all seven scope items shipped.

**Why first:** two independent PM-style passes this session converged on the same conclusion —
the core generate → approve → run loop is still shedding new bugs (`ISS-009`, `ISS-011` both
found in one session), model selection is still unsettled, and there is currently **no CI or
pre-commit enforcement anywhere in this repo**. Nothing downstream (more skills, more providers,
a lifecycle graph) is worth building on top of a foundation that's still finding new failure
modes every session.

**Scope** (work order — dependencies noted, see [[ISSUES]] for full detail on each):
1. **`ISS-005`** — **done.** Root-caused three independent failures (a skill bypassing the tool
   abstraction, a checkout-platform-fragile approval hash affecting 7 of 9 skills, and two
   `create_tool` message/contract mismatches). Unblocks CI (`ISS-012`) being *green-required*,
   not just present. See [[ISSUES]] and `specs/006-fix-pre-existing-test-failures/`.
2. **`ISS-006`** — **done.** Declared `pyyaml` as a direct dependency. See [[ISSUES]] and
   `specs/007-add-pyyaml-direct-dependency/`.
3. **`ISS-010`** — **done.** Bare `/provider` now shows usage instead of falling through to the
   LLM. See [[ISSUES]] and `specs/008-fix-bare-provider-command/`.
4. **`ISS-011`** — **done.** Fence-stripping fixed (`py_mono/skill/validator.py`) and the leaked
   prompt-placeholder line fixed (`py_mono/skill/prompts.py`). The non-code investigation
   confirmed the remote Ollama backend isn't GPU-offloading at all (`size_vram: 0`), explaining
   the near-parity throughput. See [[ISSUES]] and `specs/009-generate-skill-quality-issues/`.
5. **`ISS-012`** — **done.** `.github/workflows/ci.yml` runs `pytest` + `python -m compileall`
   on every PR and on push to `main`. Validated locally against `ISS-005`'s fix before adding —
   green. Making it *required* (branch protection) is a separate, repo-owner-only step, not done
   here. See [[ISSUES]] and `specs/010-add-minimal-ci/`.
6. **`ISS-013`** — **done.** `py_mono/skill/telemetry.py` logs `skill`/`provider`/`model`/
   `duration_ms`/`success` to `telemetry/skill_runs.jsonl` on every `run_skill_safe` call.
   Originally scoped as an M7 shared dependency, pulled forward into M6 since `ISS-014` needs it
   and M6 ships first; M7 extends this same log rather than building a second one. See
   [[ISSUES]] and `specs/011-add-skill-run-telemetry/`.
7. **`ISS-014`** — **done.** `py_mono/skill/fitness.py`'s `check_model_fitness` warns when a
   (skill, provider, model) combination has recently failed at least half its runs (min. 3
   samples, most recent 5 considered), prepended to the result via `run_skill_safe`. The
   clearest "bug we hit → feature that prevents the next one" line of anything discussed this
   session — directly productizes the `ISS-009`/`ISS-011` lesson. See [[ISSUES]] and
   `specs/012-add-model-task-fitness-check/`.

**Milestone 6 complete** — all seven scope items above are done, each with its own PR
(`ISS-005` #96, `ISS-006` #97, `ISS-010` #98, `ISS-011` #99, `ISS-012` #100, `ISS-013` #101,
`ISS-014` #102) and full SDD trail in `specs/006-` through `specs/012-`.

---

## M7 — Skill Lifecycle Graph

**Status:** Core complete — `ISS-015`, `ISS-016`, and `ISS-017` done. `ISS-018`
persistence/reporting is complete on branch `iss-018-lifecycle-reports`; M7 closeout still needs
`ISS-019` CLI/UX review polish.

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
Draft(SKILL.md) → Critique → Generate(skill.py) → Validate → Test(smoke run) ──┐
                                    ▲                                          │ fail (capped)
                                    └──────────────────────────────────────────┘
                                                                                 │ pass
                                                                                 ▼
                                                                             Propose → Approve → Run
```

**Scope:**
- **Critique** — static: does the spec violate ADR-016 tool constraints? Duplicate an existing
  skill? Reuses `validate_skill_md`, doesn't invent a new checker.
  - **Scope, stated explicitly:** this catches spec/policy violations — what's *written* — not
    content quality. It would not have caught `ISS-011`'s leaked prompt-placeholder line,
    because that was the model treating template instruction text as content to preserve, not a
    spec conflict. Don't credit this stage later as "the thing that prevents another ISS-011" —
    it wouldn't have. Catching that class of bug is what **Test** (below) is for.
- **Validate** — reuses the existing `validate_skill_py` (AST + forbidden-pattern checks),
  unchanged. Confirms the generated code is *safe*, not that it *works*.
- **Test** — new. After Validate passes, run the generated skill once against a synthetic
  trivial input before Propose, and surface pass/fail alongside the diff at Approve time.
  - This is the missing stage relative to the SDLC-graph pattern this is modeled on (which has
    Test as distinct from Build): without it, the graph goes straight from
    static-safety-validated code to human approval, with nothing checking the skill actually
    runs.
  - Also the stage that would have a shot at catching content-level bugs like `ISS-011`'s,
    which Critique's static checks structurally cannot.
- **Fail-loop cap** — already half-exists: `generate_skill` already retries once
  (`MAX_RETRIES = 1`) on validation failure. The extension is making that cap and the loop
  explicit and reusable across stages (now including Test), not inventing retry logic from
  scratch.
- **Approve** — the existing hash-ledger gate (`ISS-003`'s fix), unchanged. This graph doesn't
  touch the trust boundary, it just gives the stages before it more structure.
- **Diff-on-regeneration** — when a skill is regenerated, show a diff against the
  last-*approved* version, not just the raw new output. Cheap: `skills/.approvals.json` already
  records the approved hash, and the file's git history already exists — this is largely a
  `git diff` against that recorded commit.
- **Failure-driven evolution, never self-authorizing** — a skill that errors in production can
  have the agent propose a revised `SKILL.md`/`skill.py` using the failure as context, but it
  re-enters `proposed` state. It does not silently patch itself. Same state machine as
  first-creation, entered from a different edge.
- **Shared dependency: lightweight telemetry** — both M6's fitness check and this milestone's
  failure-driven evolution need the same flat per-run log (`skill`, `provider`, `model`,
  `duration`, `success`). M6 ships first and already can't build its fitness check without
  this, so the minimal version is built there (see M6 Scope above). This milestone extends that
  same log rather than building a second one.

**Closeout order before M8:**
1. `ISS-018` — **done.** Persist and report skill lifecycle state: durable candidate/lifecycle
   metadata, inspectable Markdown and JSON reports, baseline/diff/test/failure-context records;
   lightweight only, no dashboard unless explicitly requested.
2. `ISS-019` — polish CLI UX for lifecycle review: `/skill help`, `/skill list`, generation
   output, candidate review, diff display, and `/approve` messaging.
3. Revisit `ISS-008` as the M8 prerequisite.
4. Start M8 after the closeout and prerequisite decisions are resolved.

---

## M8 — Skill Provenance & Sharing

**Status:** Draft, explicitly gated (see Gated / Deferred below)

The *expensive* half of what got called the "killer feature" this session — deliberately
separated from M7's cheap half.

**Scope:**
- Shareable, signed skill packages: full provenance chain (generating model + prompt + approver
  + test results), exportable/importable across installs.
- **Gated** on the audience question below. Signed packages solve a multi-party trust problem —
  verifying a package from someone else wasn't tampered with — that doesn't exist yet for a
  single-operator tool. Don't build trust/signing infrastructure ahead of having a second party
  to trust.

---

## Gated / Deferred — Awaiting an Audience Decision

Grouped together because they share one open question, not because they're equally distant.

> **The open question, stated plainly:** is py-coding-agent a personal tool, or something meant
> for other people to install and use? Nothing below should get real investment until this has
> an answer.

| Item | Note |
| --- | --- |
| `ISS-008` — full isolated-worker execution for skills/dynamic tools | Also a **prerequisite** for M8 specifically, not just "eventually" — can't credibly ship "revocable, inspectable capabilities" as a trust story while execution is still a hash-ledger + static check, not real isolation. See [[ISSUES]]. |
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

## What's Already Sellable (pre-M4)

Worth naming even though it isn't a milestone — this is the honest answer to "what's actually
pitchable today":

1. **Live multi-provider switching, mid-session, no restart** (`/provider <name> [model]`) — most
   comparable tools commit you to one provider config at a time.
2. **The approval gate on generated skills** — `proposed → approved → runnable`, with the spec
   (`SKILL.md`) reviewable independently of the implementation. This project's most
   differentiated asset: a governance story (capabilities a human signs off on), not just a
   capability story (an agent that writes and runs code).
3. **Skills as durable, versioned artifacts** — once approved, a skill isn't regenerated every
   session; it's an accumulated, reviewed capability. Compounding, not one-shot.

## Known Gaps vs. Comparable Tools

Cursor, Aider, Continue, OpenHands, SWE-agent. Named plainly, not to be fixed reflexively — most
are legitimately gated on the audience question above:

- No editor/IDE integration.
- No repo-wide context (embeddings/RAG over the codebase).
- No git-native diff-review workflow for code changes (only for skills, per M7).
- No sandboxed/isolated execution (`ISS-008`).
- No test-driven iteration loop (agent verifying its own work against tests before requesting
  approval) — M7's new **Test** stage (smoke-run before Propose) is a first, narrow step
  toward this, not the full thing: one synthetic trivial case, not real test-driven iteration.
- No cost/token observability (folds into M6/M7's shared telemetry item above).
