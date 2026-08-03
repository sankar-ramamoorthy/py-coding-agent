# Feature Specification: Fix Workspace Sandbox Escape

**Feature Branch**: `fix-workspace-sandbox`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Fix the workspace sandbox so a path outside the designated workspace is always rejected, regardless of naming coincidence, ../ traversal, or symlinks. Add an explicit, empty-by-default allowlist for granting access to specific additional directories on purpose. Make shell command execution an explicit, trusted opt-in rather than a silent default, with a timeout and an honest description of its limits, without changing where an enabled shell command can reach. Ensure the development container's source mount doesn't grant write access beyond the directories that actually need it at runtime."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A path outside the workspace is always rejected (Priority: P1)

Whenever anything tries to access a path outside the designated workspace, it is rejected —
regardless of whether the outside path's name happens to look similar to the workspace's own
name, whether it's reached by ordinary `../` traversal, or whether it's reached indirectly
through a symlink that points outside the workspace.

**Why this priority**: This is the core of the sandbox guarantee. Everything else in this
feature (the allowlist, the shell toggle, the mount change) either builds on this guarantee
or is a separate, secondary layer — this story alone is what makes "the workspace is the
boundary" actually true rather than assumed.

**Independent Test**: Attempt access to a path outside the workspace whose name textually
resembles the workspace's own name — confirm rejection. Attempt `../` traversal — confirm
rejection. Attempt access through a symlink placed inside the workspace pointing outside it
— confirm rejection. Attempt access to a path genuinely inside the workspace — confirm it
still succeeds, unchanged.

**Acceptance Scenarios**:

1. **Given** a directory outside the workspace whose name textually starts with the
   workspace's own path (e.g. a sibling directory), **When** access to it is attempted,
   **Then** it is rejected.
2. **Given** an attempt to reach a location outside the workspace via `../`-style relative
   traversal, **When** the access is attempted, **Then** it is rejected.
3. **Given** a symlink located inside the workspace that points to a location outside it,
   **When** access through that symlink is attempted, **Then** it is rejected.
4. **Given** a path genuinely inside the workspace, **When** access is attempted, **Then**
   it succeeds exactly as before.

---

### User Story 2 - Deliberately grant access to specific additional directories (Priority: P2)

An operator can explicitly configure a small set of additional directories, beyond the
workspace, that are also considered accessible — on purpose, as a deliberate decision, not
as an accidental side effect of a bug. By default, no additional directories are configured,
so nothing beyond the workspace is reachable until an operator adds one.

**Why this priority**: Depends on User Story 1's containment logic existing first (the
allowlist is checked using the same real-location logic, just against more than one root).
Secondary to the core fix because it's an opt-in extension, not something every deployment
needs to use.

**Independent Test**: With no additional directories configured, confirm behavior is
identical to workspace-only access (nothing new is reachable). Configure one additional
directory, confirm a path inside it is now accepted even though it's outside the workspace,
while a path outside both the workspace and the configured directory is still rejected.

**Acceptance Scenarios**:

1. **Given** no additional directories are configured, **When** a path outside the workspace
   is accessed, **Then** it is rejected exactly as in User Story 1 — no behavior change.
2. **Given** one additional directory has been explicitly configured, **When** a path inside
   that directory is accessed, **Then** it is accepted, even though it's outside the
   workspace itself.
3. **Given** one additional directory has been explicitly configured, **When** a path
   outside both the workspace and that configured directory is accessed, **Then** it is
   still rejected.

---

### User Story 3 - Shell command execution is an explicit, trusted opt-in (Priority: P3)

A normal session, started with no special configuration, does not expose shell command
execution as an available capability. An operator can deliberately enable it through
explicit configuration — that is the only way it becomes available. Once enabled, a command
that would otherwise run forever is terminated after a bounded time, and whatever describes
the capability to the assistant makes clear it is not a content sandbox — it filters a small
set of known-risky patterns, nothing more. Enabling the capability does not, by itself,
change where an enabled shell command can reach; that remains exactly as broad as it is
today.

**Why this priority**: Independent of User Stories 1 and 2 (it doesn't touch path
containment logic at all — shell execution was never confined to the workspace to begin
with). Ordered after them because the core containment fix is the more fundamental gap;
this story closes a second, structurally different exposure (an unbounded, always-on
capability, not a path-check bug).

**Independent Test**: Start a session with no special configuration — confirm shell command
execution is not available. Explicitly enable it through configuration — confirm it becomes
available. With it enabled, run a command that would otherwise not terminate — confirm it is
stopped after a bounded time rather than hanging indefinitely.

**Acceptance Scenarios**:

1. **Given** a session started with no special configuration, **When** the available
   capabilities are examined, **Then** shell command execution is not among them.
2. **Given** an operator has explicitly enabled shell command execution through
   configuration, **When** a session starts, **Then** shell command execution is available.
3. **Given** shell command execution is enabled, **When** a command that would otherwise run
   indefinitely is issued, **Then** it is terminated after a bounded time instead of hanging
   the session forever.
4. **Given** shell command execution is enabled, **When** its description is examined,
   **Then** it accurately states it is a best-effort filter, not a content sandbox.

---

### User Story 4 - The development container's source mount is no broader than necessary (Priority: P4)

The development container no longer grants write access to the full project source merely
by running it — only the specific subdirectories the running system actually needs to
write to at runtime remain writable. The rest of the mounted source is readable but not
writable from inside the container.

**Why this priority**: Independent of the other three stories (it's a deployment/runtime
configuration change, not application logic) — ordered last because it closes a
container-level exposure that's separate from, and less immediately reachable than, the
application-level path-check and shell-toggle fixes above.

**Independent Test**: From inside the running container, confirm the subdirectories that
need write access at runtime (the workspace, dynamic tools, and skills locations) are still
writable, and confirm an attempt to write to the mounted source outside those specific
subdirectories now fails.

**Acceptance Scenarios**:

1. **Given** the running container, **When** something writes to the workspace, dynamic
   tools, or skills locations, **Then** the write succeeds exactly as before.
2. **Given** the running container, **When** something attempts to write to the mounted
   project source outside those specific locations, **Then** the write fails.

---

### Edge Cases

- What happens when a path exactly equal to the workspace root itself (no subpath) is
  accessed? It is accepted — the workspace root is inside the workspace by definition.
- What happens when an operator configures an additional allowed directory that isn't
  actually reachable from where the system runs (e.g. not mounted into a container)? The
  directory is permitted by the access check, but any actual read/write still fails for
  ordinary "path doesn't exist" reasons — this feature governs whether a location is
  *permitted*, not whether it's physically *reachable*.
- What happens to a shell command's reach once shell execution is enabled? Unchanged from
  today — enabling the capability is solely about whether it's available, not about
  narrowing or widening what an available shell command can do.
- What happens to existing sessions that already explicitly rely on today's single,
  always-available shell behavior? Out of scope for automatic migration — an operator who
  wants shell available again after this change enables it explicitly, once, via
  configuration.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST reject access to any path outside the workspace based on its
  actual, real filesystem location — not on textual comparison with the workspace's own path.
- **FR-002**: The system MUST reject access reached via `../`-style relative traversal that
  resolves outside the workspace.
- **FR-003**: The system MUST reject access reached through a symlink located inside the
  workspace that resolves to a location outside it.
- **FR-004**: The system MUST continue to accept access to paths genuinely inside the
  workspace, unchanged.
- **FR-005**: The system MUST support an explicit, operator-configured list of additional
  directories that are also considered accessible, checked using the same real-location
  logic as the workspace itself.
- **FR-006**: This additional-directories list MUST be empty by default, so no behavior
  changes for anyone who doesn't configure it.
- **FR-007**: A normal session MUST NOT expose shell command execution unless an operator
  has explicitly enabled it through configuration.
- **FR-008**: Explicit configuration MUST be the only way shell command execution becomes
  available — no other condition may enable it.
- **FR-009**: When shell command execution is enabled, a command that runs indefinitely
  MUST be terminated after a bounded time rather than allowed to hang the session forever.
- **FR-010**: When shell command execution is enabled, its description MUST accurately state
  that it is a best-effort filter, not a content sandbox, so its limits aren't overstated.
- **FR-011**: Enabling shell command execution MUST NOT itself change where an enabled shell
  command can reach — only whether the capability is available at all.
- **FR-012**: The development container MUST NOT grant write access, via its source mount,
  to anything outside the specific subdirectories the running system needs to write to at
  runtime (workspace, dynamic tools, skills).
- **FR-013**: The system MUST NOT introduce hardcoded credentials or paths in application
  code as part of this fix — the workspace root, the additional-directories list, and the
  shell-enablement toggle all remain configuration, not code.

### Key Entities

- **Workspace boundary**: the designated root directory that access is confined to by
  default.
- **Additional allowed directory**: an operator-configured location, beyond the workspace,
  explicitly granted the same accessibility as the workspace itself.
- **Shell command execution**: an optional, explicitly-enabled capability to run arbitrary
  commands; its availability is gated, but its reach is not additionally restricted by this
  feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of tested attempts to access a path outside the workspace are rejected,
  including the naming-coincidence, traversal, and symlink cases, while genuine in-workspace
  access continues to succeed in 100% of tested cases.
- **SC-002**: With no additional directories configured, behavior is identical to
  workspace-only access in 100% of tested cases; with one configured, a path inside it is
  accepted while a path outside both remains rejected, in 100% of tested cases.
- **SC-003**: A session started with no special configuration exposes zero shell command
  execution capability; enabling it through configuration is the only path to availability,
  confirmed in 100% of tested cases.
- **SC-004**: An indefinitely-running command, once shell execution is enabled, is
  terminated within a bounded, predictable time rather than hanging the session.
- **SC-005**: The specific runtime-writable subdirectories remain writable in 100% of tested
  cases; a write attempt to the mounted source outside those subdirectories fails in 100% of
  tested cases.

## Assumptions

- "The workspace" refers to the existing, already-designated sandbox root directory this
  system uses today — this feature corrects how containment against that root is checked,
  it does not relocate or redefine the root itself.
- The additional-allowed-directories mechanism governs permission, not physical
  reachability — an operator is responsible for ensuring a configured directory is actually
  accessible from where the system runs.
- Shell command execution's underlying reach (what it can read, write, or run once
  available) is unchanged by this feature — only its default availability changes.
- Full containment of shell command *content* (as opposed to gating its availability) is
  explicitly out of scope — that would require a fundamentally different execution
  environment, tracked as separate, future work if pursued.
- Skills and dynamic tools executing code before approval is a distinct, already-tracked
  concern, out of scope here.
