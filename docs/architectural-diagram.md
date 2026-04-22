
# Architectural Diagram

## Agent Loop with Skills + Playbooks

                     ┌─────────────────┐
                     │     User CLI     │
                     └────────┬────────┘
                              │
                  ┌───────────▼───────────┐
                  │       Agent Loop      │
                  │---------------------- │
                  │ - Append user input   │
                  │ - Check special cmds  │
                  │   /clear, /bye, /skill│
                  │ - If /skill: dispatch │
                  │   to SkillRegistry    │
                  │ - Else: LLM + tools   │
                  └───────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   /skill detected?      Tool call?           Text response?
        │                     │                     │
 ┌──────▼──────┐      ┌───────▼────────┐     ┌──────▼───────┐
 │SkillRegistry│      │  Execute Tool  │     │ Return Text  │
 │-------------|      │ -------------- │     │  to User     │
 │- Parse args │      │ - Resolve tool │     └──────────────┘
 │- Load Skill │      │ - Tool.run()   │
 │- Inject     │      │ - Get result   │
 │  Playbooks  │      └───────┬────────┘
 │- skill.run()│              │
 │  with       │              │
 │  SkillContext│             │
 └──────┬──────┘              │
        │                     │
        └──────────┬──────────┘
                   │
          ┌────────▼─────────┐
          │  Memory Update   │
          │ - Append results │
          │ - Auto-prune     │
          └────────┬─────────┘
                   │
                   ▼
            ┌──────────────┐
            │ Back to LLM  │ or User CLI
            └──────────────┘

---

## Skill Execution Layer (ADR-016)

User: /skill bug_fix KeyError file:auth.py line:42
           │
           ▼
SkillRegistry.dispatch("bug_fix", args)
           │
           ▼
BugFixSkill.run(request, context)
           │
           ├─► context.agent_tools["read_file"].func({...})  # ADR-016: use tools
           ├─► context.agent_tools["edit_file"].func({...})  # never subprocess
           └─► context.agent_tools["shell"].func({"command": "pytest"})
           │
           ▼
Return string → Agent → User CLI

**Rules:**
- Skills NEVER call `subprocess`, `os.system`, `open()` directly
- All file/process actions go through `context.agent_tools`
- Skills are sandboxed to `workspace_root`
- `SkillContext` provides: `agent_tools`, `workspace_root`, `session_manager`

---

## Playbook Injection

User: "how do I write tests for this module?"
           │
           ▼
Agent Loop: not a /skill command
           │
           ▼
PlaybookRegistry.search("test") → matches playbooks/testing/pytest_guide.md
           │
           ▼
Inject playbook content into system prompt before LLM call
           │
           ▼
LLM.generate(messages=[system+playbook, user, ...])

**Rules:**
- Playbooks are Markdown only. No code execution.
- Must have YAML front-matter: `name`, `description`, `keywords`, `triggers`
- Injected based on keyword match, not explicit call

---

## Tool Abstraction Layer

    Tool.run(**kwargs)
           │
           ▼
    underlying function (_func)

**Rules:**
- All tool execution MUST go through `Tool.run(...)`
- Arguments are passed as keyword arguments only
- Direct access to `_func` is forbidden outside the Tool class

---

## LLM Provider Abstraction (ADR-005)

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

---

## Key Design Rules (ADR-016)

1. **Skills are not scripts** — they are controlled workflows using `agent_tools`
2. **Tools are not functions** — they are sandboxed execution units via `.run()`
3. **LLM never touches filesystem** — only via tool calls or skill dispatch
4. **Playbooks guide reasoning** — skills execute actions
5. **Everything is auditable** — all writes go through `write_file`/`edit_file` tools
