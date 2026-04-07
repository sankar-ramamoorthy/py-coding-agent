
# docs\adr\ADR-012-Skills-vs-Tools.md
```markdown
# ADR-012: Skills vs Tools Clarification

## Context

Within the agent, there are two mechanisms for LLM-enhanced functionality: **skills** and **dynamic tools**. While overlapping in purpose, they have distinct execution and discovery characteristics.

## Decision

- **Skills**:  
  - Abstract capabilities exposed to the LLM via `/skill` commands.  
  - Loaded dynamically via `SkillRegistry`.  
  - Can be scaffolded interactively using `/skill generate-skill`.  
  - Can include multiple helpers and optional tool references.  
  - Typically executed locally in Python, making them compatible with smaller LLMs.

- **Dynamic Tools**:  
  - Python modules dynamically created using `create_tool.py`.  
  - Registered manually with the agent tool registry or via `main.py`.  
  - Called via `/tool` commands.  
  - Provide low-level utility execution; often simpler than skills.  
  - Require registration to be discoverable.

## Consequences

- Clear separation between **high-level agent skills** and **utility tools**.  
- Developers can scaffold skills that internally call tools, creating modular workflows.  
- Both approaches are compatible with lightweight LLMs, but skills allow richer structured workflows.
```

---

