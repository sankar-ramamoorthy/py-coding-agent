# Feature Specification: `generate_skill` output-quality fixes

**Feature Branch**: `fix-generate-skill-quality-issues`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Fix ISS-011 — three findings from dogfooding `generate_skill`
against a coding-tuned model: (1) markdown-fence stripping isn't safe for asymmetric or
preamble-prefixed fences, (2) a leaked, unmarked template placeholder line in the SKILL.md
prompt got echoed verbatim into generated output, (3) possible CPU-bound/unoffloaded inference
on the remote GPU backend. See `docs/ISSUES.md` ISS-011."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fenced LLM output parses regardless of how the model fences it (Priority: P1)

An operator generates a skill with a model that doesn't fence its output symmetrically (only a
trailing fence, or explanatory preamble before the fence). The generated code should still parse
and validate correctly instead of failing with a syntax error caused by a leftover fence marker.

**Why this priority**: This is a latent correctness bug — the previous implementation only
handled the one fencing shape (leading-fence, optional matching trailing fence) it happened to
be tested against; two other realistic shapes silently broke `ast.parse()`.

**Independent Test**: Feed fence-stripping a trailing-only fence and a preamble-plus-fence input
and confirm both return clean, parseable code.

**Acceptance Scenarios**:

1. **Given** LLM output with a leading and matching trailing fence, **When** stripped, **Then**
   the result is unchanged from before this fix (no regression).
2. **Given** LLM output with only a trailing fence and no leading fence, **When** stripped,
   **Then** the trailing fence is removed and the remaining code is returned.
3. **Given** LLM output with explanatory text before a fenced block, **When** stripped, **Then**
   only the fenced block's content is returned.
4. **Given** LLM output with no fence at all, **When** stripped, **Then** it is returned
   unchanged.

---

### User Story 2 - Generated `SKILL.md` never contains leaked template instructions (Priority: P1)

An operator generates a new skill's `SKILL.md`. The generated file should contain only real
content the operator would recognize as describing their skill — never a leftover instruction
line from the prompt template itself.

**Why this priority**: Confirmed reproduced in a real generation run — a real prompt-template
line intended as an instruction to the model ("list each constraint as a bullet point") was
phrased identically to genuine content and got echoed verbatim into the generated `SKILL.md`.

**Independent Test**: Generate `build_skill_md_prompt()`'s output and confirm every fillable
section is unambiguously marked as an instruction to replace, not phrased as literal content.

**Acceptance Scenarios**:

1. **Given** the SKILL.md prompt template, **When** inspected, **Then** every fillable section
   (paragraph description, expected output, constraints) is marked with an explicit
   `[INSTRUCTION — ...]` marker distinguishing it from literal content.
2. **Given** the prompt's closing rules, **When** inspected, **Then** they explicitly tell the
   model never to copy an instruction marker into its output.

---

### User Story 3 - Understand whether the remote backend is actually GPU-accelerating inference (Priority: P2)

An operator wants to know whether the previously-observed near-parity prompt/generation
throughput on the "remote GPU" Ollama backend indicates a real infrastructure problem, so future
sessions don't have to re-derive this.

**Why this priority**: Lower than the two code fixes (P1) since this investigation, by its own
nature, cannot be resolved with a code change in this repository — it's about the state of an
external Ollama server this repo talks to, not this repo's own logic.

**Independent Test**: Query the remote Ollama backend's `/api/ps` endpoint after loading a model
and inspect the `size_vram` field.

**Acceptance Scenarios**:

1. **Given** the remote Ollama backend has a model loaded, **When** `/api/ps` is queried,
   **Then** the `size_vram` field reveals whether any of the model is actually offloaded to GPU
   memory.

### Edge Cases

- Does the fence-stripping fix change behavior for the common, already-working case (symmetric
  fence)? No — covered by an explicit regression test (FR-004).
- Does marking prompt sections as `[INSTRUCTION — ...]` risk a model echoing the marker itself
  instead of real content? Addressed directly by an explicit closing rule telling the model not
  to copy instruction markers, matching this prompt's existing pattern of an explicit "Rules"
  section reinforcing format requirements.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `_strip_markdown_fences` MUST correctly strip a fenced code block regardless of
  whether the fence is symmetric (leading + trailing), leading-only, trailing-only, or preceded
  by preamble text.
- **FR-002**: `_strip_markdown_fences` MUST return input unchanged when no fence is present.
- **FR-003**: `build_skill_md_prompt()`'s fillable template sections MUST be unambiguously
  marked as instructions, not phrased as literal example content.
- **FR-004**: Automated regression tests MUST cover the previously-broken fence shapes
  (trailing-only, preamble-prefixed) in addition to the already-working shapes.
- **FR-005**: The CPU-bound/unoffloaded-inference investigation MUST be documented with concrete
  evidence (not a code change), since it concerns an external server's configuration, not this
  repository's logic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All four fence shapes (symmetric, leading-only, trailing-only, preamble-prefixed)
  produce parseable output, verified by automated tests.
- **SC-002**: The old ambiguous constraint-instruction line no longer appears anywhere in the
  SKILL.md prompt template, verified by an automated test.
- **SC-003**: A concrete, reproducible finding (not a guess) is recorded for the remote-backend
  GPU-offload question, usable by a future session without re-deriving it.

## Assumptions

- The CPU-bound/unoffloaded-inference investigation is scoped to what's observable from this
  repo's network access to the remote Ollama host's API (`/api/ps`, `/api/generate` timing
  fields) — diagnosing *why* GPU offload isn't happening (driver issue, host configuration, no
  GPU present) would require direct access to that host's own system, out of scope here.
