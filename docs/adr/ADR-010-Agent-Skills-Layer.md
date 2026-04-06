
# docs\adr\ADR-010-Agent-Skills-Layer.md 

```markdown
# ADR-010: Agent Skills Layer

Date: 2026‑03‑28

**Status:** `accepted` 

## What does this ADR do.
- Explains **what a skill is**,  
- Says **how it’s stored** (`skills/` + `SKILL.md`),  
- Describes **how it’s invoked** (`/skill ...`),  
- Defines **constraints, review, and safety**,  
- Outlines the **base classes** and where they live.


## Context

The agent currently has a generic tool‑calling loop and a set of built‑in tools. To support complex, multi‑step workflows (e.g., bug fixing, refactoring, documentation sync, domain‑specific tasks like LinkedIn‑job‑scraping), we want a **skills layer** that:

- Encapsulates recurring patterns as named skills.  
- Keeps the agent’s core loop small and focused.  
- Allows humans to inspect, review, and version skills as code.

Skills should be:

- Discoverable at runtime,  
- Safe to execute within the existing sandbox,  
- Reviewable before being used.

--- Update 2026/03/29 

## Decision

Introduce an **agent skills layer** with the following characteristics:

## Context

The agent requires a structured abstraction layer for encapsulating discrete capabilities beyond basic LLM reasoning. Previously, the focus was on static skills discovered from `skills/`. We now introduce an integrated mechanism to scaffold new skills dynamically within the repository, enabling a developer workflow without standalone scripts.

## Decision

- Maintain the **Skill abstraction** as the primary interface for LLM-invoked capabilities.  
- Skills are loaded dynamically from `skills/` using the SkillRegistry.  
- New skills can be **scaffolded interactively** using the `/skill generate-skill` internal dev skill.  
  - Generates `SKILL.md` + `skill.py` with optional helpers and tool references.  
  - Defaults to `status: proposed` to prevent production execution until approved.  
- Skills remain **discoverable via the agent CLI** and `/skill help`.  
- The agent continues to support execution of skills on **less capable open-source LLMs**, as skill logic executes locally in Python rather than relying solely on LLM reasoning.

## Consequences

- Developers can rapidly prototype new skills directly within the repo.  
- Skills and dynamic tools can coexist: tools are registered manually or via `create_tool`, while skills can scaffold tools internally if needed.  
- The SkillRegistry ensures consistent discovery and invocation patterns.  
- Skills are compatible with smaller LLMs since execution is local.  
- Adds a clear workflow for dev-only experimental skills without impacting production behavior.
---
### 1. What a skill is

A **skill** is a reusable, description‑driven pattern for a class of tasks. It consists of:

- A **spec** (in `SKILL.md`) that defines purpose, constraints, and allowed tools.  
- Optional **code** (`skill.py`) that orchestrates tools and logic.  
- A **name** (e.g., `bug_fix`, `refactor_extract_function`, `doc_sync`) that the agent can match against user intent.

Skills are not magical AI things; they are **structured recipes** that the agent can:

- Discover,  
- Parse,  
- Call,  
- Improve,  
- Propose,  
… all under human‑controlled rules.

---

### 2. How skills are stored

- Skills live in a top‑level directory:

  ```text
  skills/
      <skill_name>/
          SKILL.md
          skill.py  # optional
  ```

- `SKILL.md` is a Markdown file with optional front‑matter (e.g., YAML) that captures:

  - `name`  
  - `description`  
  - `trigger` (e.g., `/skill <name> ...`)  
  - `allowed_tools` (e.g., `read_file`, `write_file`, `shell`, `create_tool`)  
  - `constraints` (e.g., “no network access”, “no file deletion”)

- `skill.py` is a Python module that implements a `Skill` subclass.

This layout is:

- Easy to inspect,  
- Version‑controlled,  
- Composable per skill.

---

### 3. How skills are invoked

- The agent exposes a CLI surface:

  - `/skill list` → show all available skills and short descriptions.  
  - `/skill <name> ...` → invoke the named skill with args.  
  - `/skill help <name>` → show that skill’s `SKILL.md` summary.

- Inside the agent loop:

  - When a user message starts with `/skill`, the agent routes it to the `SkillRegistry`.  
  - The registry finds the matching skill, instantiates it, and calls its `run(...)` method with:

    - `request` (the full `/skill ...` text),  
    - `SkillContext` (workspace, session, etc.),  
    - `agent_tools` (dict of tool names → `Tool` objects).

- The skill can then:

  - Call tools,  
  - Read/write files,  
  - Make shell calls,  
  … but only within the constraints defined in `SKILL.md`.

---

### 4. Constraints, review model, and safety rules

#### Constraints

Each skill declares:

- **Allowed tools** (e.g., `read_file`, `write_file`, `shell`; not `delete_file`).  
- **Allowed side effects** (e.g., “can edit files in `/workspace` but not delete them”).  
- **Resource limits** (e.g., “max 100 lines changed per file” in rough, human‑readable terms).

Skills that violate constraints are rejected or down‑scoped.

#### Review model

Skills have a **review lifecycle**:

- **Proposed only** (default for new skills): Skill exists as a `SKILL.md` + optional `skill.py`, but the agent must not execute it without explicit human approval.  
- **Approved** (explicitly tagged): Skill can be executed.  
- **Deprecated** (marked in `SKILL.md`): Skill should not be used; new skills should replace it.

Approval is initially done via:

- A `status` field in `SKILL.md` (e.g., `status: proposed` or `status: approved`).  
- Optionally, a code review / PR gate for new skills.

#### Safety rules

- All skills respect the existing sandbox (`/workspace`, no `../..`, no system files).  
- Skills that trigger network calls must:

  - Be explicit about it,  
  - Have a `dry_run` / `--simulate` mode where possible.

- The agent can be configured to:

  - Only allow pre‑approved skills,  
  - Or require approval per‑skill for risky operations.

---

### 5. Base classes

Introduce a minimal base class hierarchy:

- `SkillContext(workspace_root: str, session_manager: SessionManager, ...)` → shared context for all skills.  
- `Skill`
  - `.name()` → returns skill name.  
  - `.description()` → returns short description.  
  - `.can_handle(request: str, context: SkillContext) -> bool` → asks if this skill can handle the request.  
  - `.run(request: str, context: SkillContext, agent_tools: Dict[str, Any]) -> str` → runs the skill, returns a human‑readable result.  
- `SkillRegistry`
  - Discovers skills from the `skills/` directory.  
  - Maintains a mapping `name → Skill`.  
  - Optionally validates constraints against a global policy.

These classes live in:

```text
py_mono/
    skill/
        base.py       # Skill, SkillContext, SkillRegistry
        registry.py   # optional extra logic
    skills/
        bug_fix/
            SKILL.md
            skill.py
        refactor_extract_function/
            SKILL.md
            skill.py
        doc_sync/
            SKILL.md
            skill.py
```

---

## Consequences

### Pros

- Clear, reusable patterns for common agent‑assisted tasks.  
- Skills are version‑controlled and inspectable as code.  
- Safety and constraints are explicit and declarative.  
- The agent can:

  - Propose new skills,  
  - Improve existing skills,  
  - Or even partially generate them, under human review.

### Cons

- Adds a small amount of infrastructure (`py_mono/skill/`).  
- Skills add another layer between user intent and execution; need good UX (`/skill list`, `/skill help`).  
- If not reviewed, skills can accidentally encode unsafe patterns.

### Long‑term impact

- Enables domain‑specific skill packs (e.g., web‑scraping, testing, refactoring, LinkedIn‑job‑search).  
- Supports **self‑improving patterns**, where the agent observes frequent workflows and suggests new skills.  
- Keeps the core agent loop small; complexity lives in the skills layer.

---

## Related ADRs

- ADR‑004: MCP Server Integration (skills can call MCP tools).  
- ADR‑005: Multi‑provider LLM Abstraction (skills can route to different providers).  
- ADR‑006: Session, Key, and Provider Management (skills use the active provider).  
- ADR‑009: Tight‑binding model selection (skills can choose models via provider / model hints).
```

***


