
# Architectural Diagram

_Last refreshed: 2026-08-05, against the actual code in `py_mono/agent/agent.py` and
`py_mono/llm/prompts.py` (not just the ADRs) — see the note under Agent Loop below for
what changed._

## Agent Loop: Structured Orchestration (ADR-017)

The LLM is prompted (`py_mono/llm/prompts.py:build_system_prompt`) to respond either as plain
text or as a structured `agent_action` JSON envelope, and the agent parses that envelope
(`Agent._handle_structured_action` in `py_mono/agent/agent.py`) rather than only reacting to a
user-typed `/skill` command. Both entry points into skill execution are real and both matter:

                     ┌─────────────────┐
                     │     User CLI     │
                     └────────┬────────┘
                              │
                  ┌───────────▼───────────┐
                  │       Agent Loop      │
                  │---------------------- │
                  │ - Append user input   │
                  │ - Check special cmds  │
                  │   /clear, /bye,       │
                  │   /provider, /skill   │
                  │ - Else: call LLM      │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │   LLM responds with   │
                  │  plain text  OR   {"_type":"agent_action", "action": "answer"|"use_skill", ...}
                  └───────────┬───────────┘
                              │
        ┌─────────────────────┼─────────────────────────┬─────────────────────┐
        │                     │                          │                     │
 user typed /skill    action=="use_skill"          action=="answer"      Tool call in a
   directly                (LLM chose it)          (LLM chose it)      plain-text turn
        │                     │                          │                     │
 ┌──────▼──────┐      ┌───────▼────────┐          ┌──────▼───────┐    ┌────────▼────────┐
 │SkillRegistry│◄─────┤ simulates      │          │ Return the   │    │  Execute Tool   │
 │-------------|      │ "/skill <name> │          │ answer/      │    │ --------------- │
 │- Parse args │      │  <arguments>"  │          │ response     │    │ - Resolve tool  │
 │- Load Skill │      └────────────────┘          │ text to User │    │ - Tool.run(...) │
 │- Inject     │                                   └──────────────┘    │ - Get result    │
 │  Playbooks  │                                                       └────────┬────────┘
 │- skill.run()│                                                                │
 │  with       │                                                                │
 │  SkillContext│                                                              │
 └──────┬──────┘                                                               │
        │                                                                      │
        └──────────────────────────────┬───────────────────────────────────────┘
                                        │
                               ┌────────▼─────────┐
                               │  Memory Update    │
                               │ - Append results  │
                               │ - Auto-prune       │
                               └────────┬──────────┘
                                        │
                                        ▼
                                 ┌──────────────┐
                                 │ Back to LLM  │ or User CLI
                                 └──────────────┘

**What changed from the previous version of this diagram:** the old version showed only the
user-typed `/skill` path and implied the LLM's only other option was free-form tool calls. In
practice `action: "use_skill"` lets the LLM invoke a skill on its own initiative — the ADR-017
"structured orchestration interface" is implemented, not just proposed, even though ADR-017's
own header still reads `Status: Proposed`. That header is stale; treat this diagram and the
code as the source of truth over the ADR status field until ADR-017 is explicitly updated.

---

## Skill Execution Layer (ADR-016)

User: /skill bug_fix KeyError file:auth.py line:42
   *(or the LLM's own `action: "use_skill"` choice, simulated as the same call)*
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
- Only `status: approved` skills may run — gated by a hash-verified ledger
  (`skills/.approvals.json`, ADR-010, ADR-013, fixed for a bypass in `ISS-003`)

---

## Playbook Injection

User: "how do I write tests for this module?"
           │
           ▼
Agent Loop: not a /skill command, no use_skill action chosen
           │
           ▼
PlaybookRegistry.search("test") → playbooks/testing/pytest_guide.md
   scored by: exact name match (100) + keyword-frontmatter overlap (10/word) + title match (5)
           │
           ▼
Inject playbook content into system prompt before LLM call
           │
           ▼
LLM.generate(messages=[system+playbook, user, ...])

**Rules:**
- Playbooks are Markdown only. No code execution.
- Must have YAML front-matter: `name`, `description`, `keywords`, `triggers`
- Injected based on keyword/frontmatter score, not explicit call
- Current playbooks: `playbooks/debugging/`, `playbooks/testing/`, `playbooks/software-design/`
  (ADR-018)

*Dormant, not wired in:* `py_mono/retrieval/keyword_ranker.py` implements a separate scoring
approach but nothing currently imports it — `PlaybookRegistry.search` above is the scorer
actually in the loop. Don't assume `retrieval/` is live without checking call sites first.

---

## Tool Abstraction Layer (ADR-014)

    Tool.run(**kwargs)
           │
           ▼
    underlying function (_func)

**Rules:**
- All tool execution MUST go through `Tool.run(...)` — never call `tool.func(...)` or `_func`
  directly (ADR-014 formalized this after LLMs frequently mis-called the old direct-function
  form with positional or dict-as-positional arguments)
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
  │     │ - think:false by default + num_predict/num_ctx safety net (ISS-009 fix)
  │     └── HTTP /api/chat
  │
  └── LiteLLMProvider
        │ to_wire_messages() → pass-through
        └── litellm.completion()

Runtime switching: `/provider <name> [model]` tight-binds a model to the session
(ADR-009), overriding env defaults without a restart.

---

## Key Design Rules (ADR-016)

1. **Skills are not scripts** — they are controlled workflows using `agent_tools`
2. **Tools are not functions** — they are sandboxed execution units via `.run()`
3. **LLM never touches filesystem** — only via tool calls or skill dispatch, whether it got
   there via a typed `/skill` command or its own `action: "use_skill"` choice
4. **Playbooks guide reasoning** — skills execute actions
5. **Everything is auditable** — all writes go through `write_file`/`edit_file` tools

---

## Planned: Skill Lifecycle Graph (Milestone 7 — not yet built)

`docs/ROADMAP_PLAN.md` proposes extending the existing two-node `proposed → approved` skill
gate into a full graph, adding stages this repo does not have yet:

```
Draft(SKILL.md) → Critique → Generate(skill.py) → Validate → Test(smoke run) ──┐
                                    ▲                                          │ fail (capped)
                                    └──────────────────────────────────────────┘
                                                                                 │ pass
                                                                                 ▼
                                                                             Propose → Approve → Run
```

Nothing above the current "Skill Execution Layer" section reflects this yet. See
`docs/ROADMAP_PLAN.md` (Milestone 7) for the full reasoning, including why `Critique` is scoped
to static spec/policy checks only and what `Test` is specifically meant to catch that `Critique`
can't.
