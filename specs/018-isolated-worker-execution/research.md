# Research: Isolated Worker Execution

## Decision: Use one subprocess per extension invocation

**Rationale**: It gives a real process boundary, avoids long-lived worker lifecycle complexity, and fits the current synchronous CLI workflow.

**Alternatives considered**: A persistent worker pool was rejected as premature. Container-per-call was rejected for this issue because the repo already runs inside Docker and the immediate missing boundary is agent-process isolation.

## Decision: Use JSON-line stdin/stdout RPC

**Rationale**: The existing tool interface is synchronous and keyword-based. JSON lines are easy to test and do not require new dependencies.

**Alternatives considered**: Sockets and gRPC were rejected because they add setup and dependency surface without current need.

## Decision: Load dynamic-tool metadata statically

**Rationale**: Importing dynamic-tool modules during load is the exact behavior this issue removes. The generated tool wrapper has a predictable `Tool(...)` assignment that can be extracted with AST/literal evaluation.

**Alternatives considered**: Continuing to import after static validation was rejected because it preserves the main-process side effect risk.
