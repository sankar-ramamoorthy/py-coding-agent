`docs/architectural-diagram.md`

```markdown
# Architectural Diagram

## Agent Loop

```

```
                     ┌─────────────────┐
                     │     User CLI     │
                     └────────┬────────┘
                              │
                  ┌───────────▼───────────┐
                  │       Agent Loop      │
                  │---------------------- │
                  │ - Append user input   │
                  │ - Check special cmds  │
                  │   (/clear, /bye, etc) │
                  │ - Send messages to    │
                  │   LLM + tool list     │
                  └───────────┬───────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   LLM Provider  │
                     │ --------------- │
                     │ OllamaProvider  │
                     │ LiteLLMProvider │
                     │                 │
                     │ - Decide: text  │
                     │   or tool call  │
                     └────────┬────────┘
                              │
            ┌─────────────────┴───────────────────┐
            │                                     │
   Tool call detected?                      Text response?
            │                                     │
    ┌───────▼────────┐                     ┌──────▼───────┐
    │   Execute Tool │                     │  Return Text │
    │ -------------- │                     │  to User     │
    │ - Resolve tool │                     └─────────────┘
    │   from registry│
    │ - Parse args   │
    │   (JSON → dict)│
    │ - Execute via  │
    │   Tool.run(...)│
    │   (kwargs only)│
    │ - Capture      │
    │   result/error │
    └───────┬────────┘
            │
 Auto-prune memory after N tool calls?
            │
    ┌───────▼────────┐
    │  Prune Memory  │
    │  (keep last N) │
    └───────┬────────┘
            │
  Memory updated in agent loop
            │
            ▼
       ┌─────────────┐
       │ Back to LLM │
       └─────────────┘
            │
            ▼
     Final answer returned
            │
            ▼
         User CLI
```

```

---

## Tool Abstraction Layer

```

```
    Tool.run(**kwargs)
           │
           ▼
    underlying function (_func)
```

```

**Rules:**
- All tool execution MUST go through `Tool.run(...)`
- Arguments are passed as keyword arguments only
- Direct access to `_func` is forbidden outside the Tool class

---

## LLM Provider Abstraction (ADR-005)

```

agent.py
│
│  canonical OpenAI-style messages
│
▼
LLMProvider (base.py)
│
├── OllamaProvider
│     │ to_wire_messages()
│     │ - content: None → ""
│     │ - strips tool_call_id
│     └── HTTP /api/chat
│
└── LiteLLMProvider
│ to_wire_messages() → pass-through
└── litellm.completion()

```

---

## MCP Integration (ADR-004)

```

agent (sync)
│
└── mcp_tool.py
│ asyncio bridge
▼
mcp_client.py (async)
▼
MCP Server (FastMCP)
▼
Tool result → agent loop

```

---

## Canonical Message Format (ADR-005)

```

# Assistant tool call

{
"role": "assistant",
"content": null,
"tool_calls": [
{
"id": "<uuid>",
"type": "function",
"function": {
"name": "tool_name",
"arguments": {"key": "value"}
}
}
]
}

# Tool result

{
"role": "tool",
"tool_call_id": "<uuid>",
"content": "string result"
}

```

**Flow:**
```

arguments (JSON) → parsed → Tool.run(**kwargs)

```

---

## Dynamic Tool Lifecycle

```

LLM generates tool code
│
▼
File written to dynamic_tools/
│
▼
load_dynamic_tools()
│
▼
isinstance(attr, Tool)
│
▼
Registered in agent.tools
│
▼
Executable via Tool.run(...)

```

---

## Memory Structure

```

[
{"role": "system", "content": "..."},
{"role": "user", "content": "..."},
{"role": "assistant", "tool_calls": [...]},
{"role": "tool", "content": "..."},
{"role": "assistant", "content": "..."}
]

```

- Auto-pruned every N tool calls
- System prompt always preserved

---

## Key Design Rules

- Tools are **not raw functions** — they are controlled execution units
- `.run()` is the **only public execution interface**
- LLM never interacts with `.func`
- Agent remains provider-agnostic
- All file access is sandboxed via workspace root
```

