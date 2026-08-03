# Feature Specification: Dual Ollama Backend Selection (Local + Remote GPU)

**Feature Branch**: `ollama-dual-backend`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Add explicit local/remote Ollama backend selection to py-coding-agent's LLM provider layer, with the remote (GPU-equipped) backend preferred by default and both backends' models switchable at runtime without code changes. Local inference is too slow for practical use; a GPU-equipped remote host is available but not always on, and the exact model on either backend is expected to change over time without needing a code change."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast inference by default, with automatic fallback (Priority: P1)

A user starts a normal session without specifying anything about backends. When the fast,
GPU-equipped remote machine is reachable, the session automatically uses it. When it isn't
(the remote machine is off, unreachable, or on a different network), the session
automatically and transparently uses the local machine instead — no manual step required
either way.

**Why this priority**: This is the entire point of the feature — most sessions should just
be fast by default without the user having to think about which backend is available today.

**Independent Test**: Can be fully tested by starting a session with the remote backend
reachable (confirms it's selected), then starting a session with the remote backend
deliberately made unreachable (confirms local is selected instead, with no manual action).

**Acceptance Scenarios**:

1. **Given** the remote backend is reachable, **When** a new session starts with no explicit
   backend chosen, **Then** the session uses the remote backend and its configured default model.
2. **Given** the remote backend is not reachable, **When** a new session starts with no
   explicit backend chosen, **Then** the session automatically uses the local backend and
   its configured default model, with no error shown to the user and no manual step required.

---

### User Story 2 - Explicit backend override (Priority: P2)

A user who knows exactly which backend they want (for example, testing something specific
to the local machine, or confirming the remote machine is behaving correctly) can force
either backend directly, bypassing the automatic default entirely.

**Why this priority**: Automatic selection (US1) covers the common case, but a user must be
able to override it deliberately when they have a specific reason to.

**Independent Test**: Can be fully tested by explicitly requesting the remote backend and
confirming it's used even when local would otherwise have been chosen, and vice versa; and
by explicitly requesting a backend that is unreachable and confirming a clear, direct error
is shown rather than a silent fallback to the other backend.

**Acceptance Scenarios**:

1. **Given** any reachability state, **When** a user explicitly selects the remote backend,
   **Then** the session uses the remote backend and its configured default model.
2. **Given** any reachability state, **When** a user explicitly selects the local backend,
   **Then** the session uses the local backend and its configured default model.
3. **Given** a user explicitly selects a backend that is unreachable, **When** the selection
   is attempted, **Then** the failure is surfaced directly and clearly — the system does
   NOT silently substitute the other backend.

---

### User Story 3 - Switch the model on either backend at runtime (Priority: P3)

A user wants to change which model a backend uses — for example, moving the remote backend
from its current default model to a different one they've since decided to use — without
any code change, redeployment, or restart of the underlying service.

**Why this priority**: Model choice on either machine is expected to change over time; this
must be a simple, repeatable action, not a reconfiguration exercise, but it's still secondary
to simply having both backends reachable at all (US1/US2).

**Independent Test**: Can be fully tested by selecting a backend together with a specific
model in one action, and confirming that exact model is what gets used, distinct from that
backend's configured default.

**Acceptance Scenarios**:

1. **Given** a backend has a configured default model, **When** a user selects that backend
   and specifies a different model in the same action, **Then** the specified model is used
   instead of the default, for that selection only.
2. **Given** a user has switched a backend's model, **When** they later select that backend
   again without specifying a model, **Then** the backend's original configured default
   model is used again (the override does not silently become the new persistent default).

---

### Edge Cases

- What happens when the remote backend becomes unreachable *during* an already-connected
  session (not at selection time)? Out of scope — this feature only checks reachability at
  the moment a backend is selected (session start or explicit switch), not continuously.
- What happens when a user selects an explicit backend that's unreachable? Surfaced as a
  direct, clear connection failure — never silently substituted with the other backend
  (distinguishes explicit selection from the automatic default's fallback behavior).
- What happens for a user who already has today's single-backend behavior explicitly
  configured? Nothing changes for them — their existing configuration continues to behave
  exactly as it did before this feature shipped.
- What happens if a requested model name isn't actually available on the chosen backend?
  Unchanged from today's existing behavior — this feature does not add new model-name
  validation beyond what already happens when a backend is contacted.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide an explicit way to select the remote backend.
- **FR-002**: The system MUST provide an explicit way to select the local backend.
- **FR-003**: The system MUST provide an automatic default selection that prefers the
  remote backend and falls back to the local backend when the remote backend is not reachable.
- **FR-004**: Explicit backend selections (FR-001, FR-002) MUST NOT silently fall back to
  the other backend on failure — the failure must be surfaced directly.
- **FR-005**: The model used on either backend MUST be overridable at the moment of
  selection, without requiring a code change or redeployment.
- **FR-006**: Each backend MUST have an independently configurable default model, used when
  no override is given at selection time.
- **FR-007**: Users who have explicitly configured today's single-backend behavior MUST see
  no change in behavior after this feature ships.
- **FR-008**: The system MUST NOT introduce new hardcoded credentials or addresses in
  application code — backend addresses and models MUST be configuration, not code.
- **FR-009**: The reachability determination used for automatic selection MUST be a single,
  short check performed only at selection time — it MUST NOT add noticeable delay to normal,
  already-connected operation.
- **FR-010**: All available backend selection options MUST remain discoverable through the
  system's existing mechanism for listing available choices.

### Key Entities

- **Backend**: a named Ollama endpoint (local or remote), with a network address and a
  default model.
- **Provider selection**: the backend and model actually in use for a given session or
  explicit switch — may differ from a backend's configured default when overridden.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: When the remote backend is reachable, 100% of new sessions with no explicit
  backend chosen use it automatically, with no user action required.
- **SC-002**: When the remote backend is not reachable, 100% of new sessions with no
  explicit backend chosen fall back to the local backend automatically, with no user action
  required and no error surfaced for the fallback itself.
- **SC-003**: A user can force either backend in a single action, regardless of the
  automatic default's outcome, in 100% of tested cases.
- **SC-004**: A user can change the model used on either backend in a single action, with
  the change taking effect immediately and reverting to that backend's own default the next
  time it's selected without an override.
- **SC-005**: Existing users with today's single-backend behavior explicitly configured see
  zero behavioral difference before and after this feature ships.
- **SC-006**: The one-time reachability check adds no perceptible delay to normal usage once
  a backend has already been selected for a session.

## Assumptions

- The remote backend's network reachability (e.g. via an already-configured VPN/mesh
  network) is a precondition this feature relies on, not something it sets up itself.
- "Reachable" is determined by a lightweight, one-time check at the moment of selection —
  not continuous monitoring throughout a session.
- Both backends run compatible, same-protocol Ollama servers — this feature is about
  choosing *which* Ollama instance to use, not switching to a different kind of backend
  entirely (that remains a separate, existing capability).
- If an explicitly-selected backend is unreachable, that is treated as an ordinary
  connection failure to report to the user, not a trigger for an automatic retry against
  the other backend.
