
# docs\adr\ADR-011-Interactive-Skill-Scaffolding.MD

```markdown
# ADR-011: Interactive Skill Scaffolding

## Context

Creating new skills manually can be error-prone and inconsistent. There is a need for an **interactive in-repo skill generator** that scaffolds fully structured skill skeletons, including helpers, optional tool calls, and pre-filled JSON outputs.

## Decision

- Introduce `/skill generate-skill` as a **dev-only skill**:  
  - Prompts for skill name, description, helper methods, and optional tool references.  
  - Generates `SKILL.md` and `skill.py` in `skills/`.  
  - Includes structured helpers like `parse_request` and `perform_task` by default.  
  - Provides placeholders for tool integration.  
  - Marks new skills as `status: proposed` until developer approval.  
- Fully integrated with the SkillRegistry for **CLI discoverability**.  
- Supports **production-ready skeletons** compatible with any LLM size, including lightweight open-source models, because execution is local.  
- Avoids standalone scripts; all generation occurs within the agent repo.

## Consequences

- Developers can scaffold consistent, structured skills rapidly.  
- Reduces errors in skill implementation.  
- Maintains separation of experimental and production skills.  
- Encourages best practices for input parsing, workflow structuring, and optional tool integration.
```

---

