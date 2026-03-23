# Architectural Diagram

## Agent Loop

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
                      │   (/clear, /bye)      │
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
                         │ (Groq/OpenAI/   │
                         │  Anthropic etc) │
                         │                 │
                         │ - Decide: text  │
                         │   response or   │
                         │   tool call     │
                         └────────┬────────┘
                                  │
                ┌─────────────────┴───────────────────┐
                │                                     │
       Tool call detected?                      Text response?
                │                                     │
        ┌───────▼────────┐                     ┌──────▼───────┐
        │   Execute Tool │                     │  Return Text │
        │ -------------- │                     │  to User     │
        │ - Use Tool.func│                     └─────────────┘
        │   (read/write/ │
        │    shell/etc.) │
        │ - Record result│
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
  │     │ to_wire_messages() → strips tool_call_id, fixes content: "" 
  │     └── POST /api/chat → localhost:11434
  │
  └── LiteLLMProvider
        │ to_wire_messages() → pass-through (OpenAI native)
        └── litellm.completion()
              │
              ├── groq/qwen/qwen3-32b
              ├── openai/gpt-4o
              ├── anthropic/claude-3-5-haiku
              └── ... any litellm provider
```

---

## Canonical Message Format (ADR-005)

```
# User message
{"role": "user", "content": "list files"}

# Assistant tool call (canonical)
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    {
      "id": "<uuid>",
      "type": "function",
      "function": {
        "name": "list_files",
        "arguments": "{}"      ← JSON string
      }
    }
  ]
}

# Tool result (canonical)
{
  "role": "tool",
  "tool_call_id": "<uuid>",
  "content": "plain string result"
}
```

---

## Dynamic Tool Lifecycle

```
LLM calls create_tool(name, code)
  │
  ▼
Tool file written to dynamic_tools/{name}.py
  │
  ▼
load_dynamic_tools() scans folder
  │
  ▼
isinstance(attr, Tool) check finds Tool objects
  │
  ▼
self.tools updated → tool available immediately
  │
  ▼
LLM can call new tool in same session
```

---

## Memory Structure

```
[
  {"role": "system",    "content": "<system prompt>"},   ← immutable
  {"role": "user",      "content": "<user query>"},
  {"role": "assistant", "tool_calls": [...]},             ← tool call
  {"role": "tool",      "content": "<result>"},           ← tool result
  {"role": "assistant", "content": "<final answer>"},     ← text response
  ...
]
```

Auto-pruned every N tool calls (default: 5), keeping last 20 messages.
System prompt is always preserved.

---

## Legend / Notes

- Special commands `/clear` and `/bye` are checked before LLM call
- `/clear` resets memory to system prompt only and resets all loop guards
- Loop guard fires if same tool called with same args twice — nudges LLM via `role: user` message
- All file operations go through `resolve_safe_path()` — sandbox enforced at every layer
- Dynamic tools volume mounted at `./dynamic_tools:/app/dynamic_tools` — no rebuild needed