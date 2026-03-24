# ADR-004: MCP Server Integration for Py-Coding-Agent

**Status:** Accepted (revised)
**Date:** 2026-03-23
**Milestone:** 2

---

## Context

As the Py-Coding-Agent grows, the standalone local agent is sufficient for single-user,
single-agent workflows. However, future features require:

- Offloading specialized tool execution to dedicated microservices
- Multi-agent coordination for complex tasks
- Dynamic tool discovery at runtime
- External API integrations (datetime, weather, search, etc.)

The original ADR-004 proposed a custom HTTP REST API (`/run_tool`, `/create_tool`, etc.).
After evaluating options and drawing on prior experience with both the official Anthropic
MCP SDK (stdio transport) and FastMCP (HTTP transport), the decision is to adopt
**FastMCP with HTTP transport** as the MCP layer.

---

## Decision

### 1. MCP Framework: FastMCP

Use **FastMCP** (`fastmcp` Python package) for all MCP servers.

Reasons:
- HTTP transport works naturally between Docker containers
- Simple `fastmcp.Client` for calling tools: `await client.call_tool(name, args)`
- Servers are debuggable via `curl` — no stdio piping complexity
- Pattern already proven in prior project (ollama-with-mcp)
- Each MCP server is an independent, replaceable microservice

Rejected alternatives:
- **Official Anthropic MCP SDK (stdio)**: stdio transport is complex between containers
- **Custom REST API**: reinvents the wheel, not standard MCP protocol

### 2. Transport: HTTP

Each MCP server runs HTTP transport on a fixed port:

```python
mcp.run(transport="http", host="0.0.0.0", port=<port>)
```

The agent calls MCP servers via Docker Compose service name:

```
http://<service-name>:<port>/mcp
```

### 3. MCP Server Structure

Each MCP server follows the pattern from ollama-with-mcp:

```
mcp_servers/<tool-name>/
├── Dockerfile
├── pyproject.toml
├── uv.lock
└── <tool_name>_mcp/
    ├── server.py     # FastMCP entrypoint, defines @mcp.tool functions
    └── tool.py       # Core business logic
```

### 4. Agent Integration

A new `py_mono/mcp/` module handles all MCP communication:

```
py_mono/mcp/
├── __init__.py
├── mcp_client.py     # Thin async FastMCP client wrapper
└── mcp_tool.py       # Tool wrapper — exposes MCP calls as agent Tools
```

The agent calls MCP servers through a standard `Tool` interface — the LLM
never knows it is talking to an MCP server vs a local tool.

```python
# Agent calls this like any other tool
mcp_datetime_tool = Tool(
    name="get_current_datetime",
    description="Get current UTC datetime from MCP server",
    func=call_datetime_mcp
)
```

### 5. MCP Client Pattern

```python
# py_mono/mcp/mcp_client.py

from fastmcp import Client

async def call_mcp_tool(url: str, tool_name: str, args: dict) -> str:
    async with Client(url) as client:
        result = await client.call_tool(tool_name, args)
        return result.structured_content or result.content
```

### 6. Docker Compose Integration

MCP servers run as separate containers on a shared Docker network:

```yaml
services:
  py-coding-agent:
    networks:
      - agent_network

  datetime-mcp:
    build: ./mcp_servers/datetime
    ports:
      - "50051:50051"
    networks:
      - agent_network

networks:
  agent_network:
```

### 7. MCP Server Port Registry

| MCP Server | Port | Tool | Status |
|---|---|---|---|
| `datetime-mcp` | 50051 | `get_current_datetime_tool` | Milestone 2 |
| `search-mcp` | 50052 | `search_web` | Future |
| `weather-mcp` | 50053 | `get_weather_tool` | Future |
| `geocoding-mcp` | 50054 | `geocode_tool` | Future |

### 8. First MCP Server: Datetime

The datetime MCP server is the first to be integrated:
- Already built and proven in prior project
- Simple — no external API dependencies
- Useful — agent currently has no access to current date/time
- Perfect proof-of-concept for the pattern

---

## Consequences

**Benefits:**
- Agent gains access to specialized external tools without bloating the agent container
- Each MCP server is independently deployable and replaceable
- HTTP transport is debuggable and Docker-native
- Pattern is reusable — new MCP servers follow the same template
- Foundation for multi-agent coordination in future milestones

**Trade-offs:**
- Adds network dependency between agent and MCP servers
- Agent requires async bridge since `agent.py` is synchronous
- MCP servers must be running for dependent tools to work
- More containers to manage in Docker Compose

---

## Async Bridge

The agent loop in `agent.py` is synchronous. FastMCP client calls are async.
A small bridge handles this:

```python
import asyncio

def call_datetime_mcp_sync() -> str:
    return asyncio.run(call_mcp_tool(DATETIME_URL, "get_current_datetime_tool", {}))
```

This keeps `agent.py` unchanged while allowing async MCP calls.

---

## Alternatives Considered

- **Official Anthropic MCP SDK (stdio)**: Rejected — stdio transport between containers
  requires complex piping, harder to debug
- **Custom REST API**: Rejected — reinvents MCP, not standard protocol
- **Local tools only**: Rejected — limits extensibility and multi-agent potential

---

## Related ADRs

- ADR-001: Safe Execution — sandbox rules still apply to MCP tool results
- ADR-003: Pi-Mono Minimal Loop — MCP tools exposed as standard Tools, loop unchanged
- ADR-005: Multi-Provider LLM — provider abstraction unaffected by MCP integration
- ADR-006: Provider Registry — future session manager may coordinate MCP servers

---

## Files to Create (when implemented)

| File | Purpose |
|---|---|
| `py_mono/mcp/__init__.py` | Module init |
| `py_mono/mcp/mcp_client.py` | Async FastMCP client wrapper |
| `py_mono/mcp/mcp_tool.py` | Sync bridge + Tool definitions |
| `mcp_servers/datetime/Dockerfile` | Datetime MCP container |
| `mcp_servers/datetime/pyproject.toml` | Datetime MCP dependencies |
| `mcp_servers/datetime/datetime_mcp/server.py` | FastMCP server entrypoint |
| `mcp_servers/datetime/datetime_mcp/tool.py` | Datetime business logic |

## Files to Modify (when implemented)

| File | Change |
|---|---|
| `docker-compose.yml` | Add datetime-mcp service and agent_network |
| `py_mono/main.py` | Register MCP tools alongside built-in tools |
| `pyproject.toml` | Add `fastmcp` dependency |
| `README.md` | Document MCP server setup and usage |