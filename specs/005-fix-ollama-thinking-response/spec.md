# Feature Specification: Fix Ollama thinking-model empty response

**Feature Branch**: `005-fix-ollama-thinking-response`

**Created**: 2026-08-05

**Status**: Draft

**Input**: User description: "Fix OllamaProvider so thinking-capable Ollama models (e.g. qwen3.5:4b) don't return empty content by exhausting their entire token budget on <think> reasoning before producing real output. Add explicit handling (think/num_predict/num_ctx) to py_mono/llm/ollama_provider.py so all skills and agent calls routed through Ollama get real output instead of a silent empty-response failure. See docs/ISSUES.md ISS-009 and kb-template/knowledge/raw/brainstorm-20260805-ollama-thinking-empty-response.md for the original bug report."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A thinking-capable local model returns usable output (Priority: P1)

A developer configures the agent to use a thinking-capable local model and runs any skill or
agent action that makes a single-shot generation call. Today this can silently fail because the
model spends its entire response budget on internal reasoning and never emits the actual answer.
The developer should get a usable answer instead.

**Why this priority**: This is the concretely reported, reproducing bug. Without this fix, a
thinking-capable local model is effectively unusable with this agent for structured generation
tasks.

**Independent Test**: Configure the agent to use a thinking-capable local model, run a
skill/action that makes a single-shot generation call with a prompt similar to the one that
previously failed, and confirm the call now returns usable content instead of an empty-response
failure.

**Acceptance Scenarios**:

1. **Given** a thinking-capable local model is configured and a prompt that previously produced
   an empty response due to the model exhausting its budget on internal reasoning, **When** the
   agent makes the generation call, **Then** the response contains usable content.
2. **Given** a non-thinking local model is configured, **When** the agent makes a generation
   call, **Then** behavior is unchanged from today (no regression for existing models).

---

### User Story 2 - Future issues of this kind are diagnosable without re-deriving root cause (Priority: P2)

An operator hits a related issue in the future (a different thinking model, or the same model
behaving unexpectedly again). They should be able to tell, from output the system already
produces, whether the model exhausting its reasoning budget is a factor — without repeating the
investigation that first uncovered this bug.

**Why this priority**: Real debugging effort went into tracing this to its root cause. The fix
should leave enough visibility behind that a similar issue doesn't cost the same effort again.

**Independent Test**: With existing debug output enabled, trigger a call to a thinking-capable
model and confirm it's possible to tell whether reasoning-budget exhaustion was a factor, without
adding new instrumentation on the spot.

**Acceptance Scenarios**:

1. **Given** debug output is enabled, **When** a call is made to a thinking-capable model,
   **Then** the existing output makes it possible to determine whether the model's reasoning
   was constrained on that call.

---

### User Story 3 - Reasoning can still be surfaced when genuinely wanted (Priority: P3)

An operator who wants to see a model's reasoning trace for a task where response latency and
token cost don't matter — not the common case for this agent's structured generation calls — can
still get it, rather than the fix removing that capability outright.

**Why this priority**: Lower priority than making the default case work. Most of this agent's
local-model calls are structured, single-shot generation where a visible reasoning trace isn't
needed today. This is about not foreclosing the capability, not about building new UX around it.

**Independent Test**: Explicitly request reasoning be surfaced for a call and confirm the system
honors that instead of always constraining it.

**Acceptance Scenarios**:

1. **Given** reasoning is explicitly requested for a call, **When** the agent makes that call,
   **Then** the system does not unconditionally suppress it.

---

### Edge Cases

- What happens when the local model/runtime doesn't support constraining reasoning at all (an
  older runtime, or a non-thinking model)? The call must not error — an unsupported setting
  should be a no-op as far as the caller is concerned.
- How does the system handle a thinking-capable model that still returns an empty response for a
  reason unrelated to reasoning-budget exhaustion (e.g. a genuine network failure)? The existing
  empty-response failure reporting must still trigger — this fix targets the specific
  reasoning-budget cause, not every possible cause of an empty response.
- What happens for other, non-local LLM providers this agent supports? Out of scope — they are
  not affected by this bug and must not be touched by this fix.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST prevent a thinking-capable local model from exhausting its entire
  response budget on internal reasoning before producing user-facing content, for the default
  (no special configuration) case.
- **FR-002**: The system MUST NOT change behavior for non-thinking local models (no regression).
- **FR-003**: The system MUST NOT suppress a genuine empty-response failure that has a cause
  other than reasoning-budget exhaustion — existing empty-response failure reporting must remain
  intact for those cases.
- **FR-004**: The fix MUST apply to the shared code path all local-model calls go through, not
  be duplicated per call site, since every skill and agent action that uses the local model
  provider shares it.
- **FR-005**: The system MUST leave enough information in existing debug output to determine,
  after the fact, whether a model's reasoning was constrained on a given call.
- **FR-006**: Automated test coverage MUST be added verifying the fix, exercising a simulated
  thinking-model empty-response case without requiring a real local model server.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Re-running the exact failing case that was captured when this bug was first
  reported no longer produces an empty-response failure caused by reasoning-budget exhaustion.
- **SC-002**: The existing automated test suite continues to pass unchanged for all unaffected
  providers and models (no regression).
- **SC-003**: A developer can determine, from a single existing debug-output capture, whether
  reasoning-budget exhaustion was a factor in an empty-response failure — without adding new
  instrumentation to investigate.
- **SC-004**: The change touches only the shared provider code path (no per-call-site
  duplication), confirmed by code review before merge.

## Assumptions

- The local-model runtime in current use supports constraining or disabling a model's internal
  reasoning via its existing request API, consistent with the diagnosis captured when this bug
  was first reported. If the specific runtime version in use doesn't support this, that must be
  verified during the planning phase against the actual running version.
- Constraining reasoning by default (rather than only raising the response budget) is an
  acceptable behavior change for this agent's use of local models, since those calls are for
  structured, single-shot generation tasks where a visible reasoning trace isn't needed today.
  This can be revisited if a future use case genuinely wants exposed reasoning (see User Story
  3).
- No new dependencies are required — this is a request/response handling change to an existing
  HTTP-based provider call already in the codebase.
- This fix targets only the local-model provider affected by this bug. Other LLM providers this
  agent supports are unaffected and explicitly out of scope.
