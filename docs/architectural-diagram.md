                         ┌─────────────────┐
                         │     User CLI     │
                         └────────┬────────┘
                                  │
                      ┌───────────▼───────────┐
                      │       Agent Loop      │
                      │----------------------│
                      │ - Append user input   │
                      │ - Check special cmds │
                      │   (/clear, /bye)     │
                      │ - Send messages to   │
                      │   LLM + tool list    │
                      └───────────┬───────────┘
                                  │
                                  ▼
                         ┌─────────────────┐
                         │       LLM       │
                         │----------------│
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
        │----------------│                     │  to User     │
        │ - Use Tool.func │                     └─────────────┘
        │   (read/write/  │
        │    shell/etc.) │
        │ - Record result │
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

Legend / Notes:

Special commands /clear and /bye are checked before LLM call.
/clear resets memory (except system prompt).
/bye ends session immediately.

Auto-pruning happens after every N tool calls (default 5).

Memory structure:
system (immutable)
user messages
assistant/tool messages

Dynamic tools:
LLM can call create_tool
Agent saves new tool in dynamic_tools/
Agent reloads tools immediately
Loop continues with expanded capabilities             