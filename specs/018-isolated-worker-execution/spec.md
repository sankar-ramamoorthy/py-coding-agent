# Feature Specification: Isolated Worker Execution

**Feature Branch**: `iss-008-isolated-worker-execution`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "ISS-008: full isolated-worker execution for skills/dynamic tools. Execute approved extensions in an isolated worker with narrow tool RPC. This is the M8 prerequisite and should replace the current hash-ledger/static-check-only execution story."

## User Scenarios & Testing

### User Story 1 - Approved Skills Do Not Execute In Agent Process (Priority: P1)

An approved skill is discoverable and runnable without importing or executing its module code in the main agent process.

**Why this priority**: This closes the remaining trust gap from generated skill module imports.

**Independent Test**: Load an approved skill that writes a marker at module import time and verify the marker is not written during registry load, then run the skill and verify execution happens only through the worker path.

**Acceptance Scenarios**:

1. **Given** an approved skill with matching ledger, **When** the registry loads, **Then** no module-level skill code runs in the agent process.
2. **Given** that approved skill is invoked, **When** it runs successfully, **Then** the result returns through the worker boundary.

---

### User Story 2 - Skills Use Narrow Tool RPC (Priority: P2)

A worker-executed skill can call only explicitly allowed agent tools through `Tool.run(**kwargs)`.

**Why this priority**: Worker isolation must still allow useful skill behavior without granting direct process access to the agent runtime.

**Independent Test**: Run a worker skill that calls an allowed tool and verify the parent executes the tool and returns the result; run a worker skill that calls a disallowed tool and verify it is blocked.

**Acceptance Scenarios**:

1. **Given** a skill is allowed to use `list_files`, **When** it calls that tool, **Then** the parent executes the tool and sends the result back to the worker.
2. **Given** a skill is not allowed to use `read_file`, **When** it requests that tool, **Then** the parent rejects the RPC call.

---

### User Story 3 - Dynamic Tools Execute In A Worker (Priority: P3)

When dynamic tools are enabled, loading them does not import generated tool modules in the agent process and running them executes in a worker process.

**Why this priority**: Dynamic tools are also generated extensions and share the same pre-M8 trust problem.

**Independent Test**: Load a dynamic tool file with module-level side effects and verify loading only extracts metadata; run the tool and verify the side effect is isolated to worker execution.

**Acceptance Scenarios**:

1. **Given** dynamic tools are enabled, **When** tools are loaded, **Then** metadata is extracted without executing module code in the agent process.
2. **Given** a loaded dynamic tool is invoked, **When** it runs, **Then** execution happens in a worker process and returns the tool result.

### Edge Cases

- Worker crashes return a clear execution error and telemetry records the failed skill run.
- Worker timeouts terminate the worker and return a clear execution error.
- Tool RPC requests for unknown or disallowed tools are rejected by the parent.
- Existing approval ledger checks still decide whether a skill may be runnable.

## Requirements

### Functional Requirements

- **FR-001**: Approved skill registry loading MUST NOT import or execute skill module code in the agent process.
- **FR-002**: Approved runnable skills MUST execute in a subprocess worker when invoked through `run_skill_safe`.
- **FR-003**: Skill worker tool access MUST use a JSON-line RPC protocol handled by the parent process.
- **FR-004**: The parent process MUST enforce existing `allowed_tools` policy for worker tool RPC calls.
- **FR-005**: Worker execution MUST return clear errors for worker crashes, malformed worker messages, disallowed tools, and timeouts.
- **FR-006**: Dynamic tool loading MUST avoid importing generated dynamic-tool modules in the agent process.
- **FR-007**: Dynamic tools MUST execute in a subprocess worker when their `Tool.run(**kwargs)` method is called.
- **FR-008**: Static validation and approval-ledger checks MUST remain in place.
- **FR-009**: Existing built-in tools and in-memory test skills MAY continue to execute in process because they are not generated extension modules.

### Key Entities

- **Skill Proxy**: Main-process metadata object for an approved skill file.
- **Worker Process**: Subprocess that imports and executes one approved extension module.
- **Tool RPC Request**: JSON-line request from worker to parent for one allowed tool call.
- **Dynamic Tool Proxy**: Main-process metadata object for a generated dynamic tool file.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Registry load tests prove approved skill module-level side effects do not run in the agent process.
- **SC-002**: Worker tests prove allowed tool RPC succeeds and disallowed tool RPC is rejected.
- **SC-003**: Dynamic-tool tests prove loading does not execute module-level side effects and invocation returns expected output.
- **SC-004**: Full test suite and compile validation remain green.

## Assumptions

- A per-invocation subprocess is sufficient isolation for this milestone.
- Container/process hardening beyond subprocess boundaries is future work unless explicitly requested.
- JSON-line stdin/stdout RPC is sufficient for the current synchronous `Tool.run(**kwargs)` interface.
