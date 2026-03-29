
# README_Skills.md

```markdown
# Skills Layer Design
## Relation to project layout

- `py_mono/skill/` contains the skills framework (`Skill`, `SkillContext`, `SkillRegistry`).  
- `py_mono/skills/` contains the concrete skill implementations (each in its own subdirectory with `SKILL.md` and `skill.py`).

## Overall role

The skills layer in `py‑coding‑agent` provides reusable, structured workflows that can be invoked via the CLI using `/skill <name> ...`. Each skill is:

- **Explicitly defined**: both in a human‑readable spec (`SKILL.md`) and in executable code (`skill.py`).  
- **Gated by approval**: a skill is only executable when its `status` is set to `approved` in `SKILL.md`.

This design intentionally differs from many other coding‑agent systems, where skills are often defined purely as prompt‑based instructions in Markdown.

---

## Core concepts

A skill comprises:

- A specification in `skills/<skill_name>/SKILL.md`.
- Optionally, an implementation in `skills/<skill_name>/skill.py`.

The specification must include at least:

- `name` — the unique identifier used in `/skill ...`.  
- `description` — a one‑line summary.  
- `trigger` — example invocation format.  
- `status` — `proposed` or `approved`.  
- `allowed_tools` and `constraints` — to define what the skill may do.

If present, `skill.py` must define a subclass of `Skill` that implements `name()`, `description()`, and `run(request, context)` using the tools in the agent’s sandbox.

---

## Execution model

When a user types:

```text
/skill bug_fix ...
```

the agent:

1. Parses the request and extracts the skill name and arguments.  
2. Resolves the `SkillRegistry` mapping from `skill_name` to skill.  
3. Checks `SkillRegistry.is_approved(skill_name)`; if not approved, the command is rejected.  
4. If approved, instantiates `SkillContext` (workspace root, agent tools, session), then calls `skill.run(request, context)`.

The result is a human‑readable string that may include:

- Code context,  
- a proposed fix or refactoring,  
- a generated test,  
- and/or a diff.

---

## Difference from Claude‑style skills

In many other coding‑agent systems (such as Claude‑style agents using `skill.md` or `SKILL.md`), a skill is:

- A **Markdown‑only specification**: the skill’s behavior is entirely described in natural‑language instructions.  
- The LLM reads `SKILL.md` and “figures out how to act” by following the steps written in the file.

In contrast, in `py‑coding‑agent`:

- `SKILL.md` serves as **the declarative spec** (name, description, status, constraints, etc.),  
- `skill.py` serves as **the executable implementation** (explicit Python logic, tool calls, and tests).

This is a **major design difference**: skills are not LLM‑interpreted Markdown workflows; they are code‑defined behaviors driven by a spec.

---

## Why this design choice matters

This model:

- Provides **deterministic behavior**: once `skill.py` is written, the skill behaves the same way every time, not ad hoc based on LLM whim.  
- Supports **review and auditing**: the Python code can be inspected and tested like any library function, and the `status: approved` gate mirrors a PR‑style code review.  
- Separates concerns:
  - `SKILL.md` documents intent and constraints,  
  - `skill.py` implements the logic safely inside the sandbox.

Later, an LLM can be used to **orchestrate** which skills to call, but the core work is done by the skill’s code, not by the LLM interpreting Markdown.

| Aspect                | Claude‑style skills                                      |  py‑coding‑agent skills                                 |
| --------------------- | -------------------------------------------------------- | ----------------------------------------------------------- |
| Skill definition      | Markdown‑driven (SKILL.md / natural‑language steps)      | Markdown spec (SKILL.md) plus executable code (skill.py).   |
| Where logic lives     | The LLM “reads the markdown and figures out how to act.” | We write explicit Python (run(...), tool calls, tests).    |
| Runtime precision     | Flexible, LLM‑interpreted.                               | Deterministic, code‑defined behavior.                       |
| Safety / review model | Often controlled by UI / toggles.                        | Explicit approval gate in YAML (status: proposed/approved). |
---

## Safety and approval model (ADR‑010)

All skills follow the same approval pattern:

- Skills are created with `status: proposed` by default.  
- A human (or CI / review process) updates `status: approved` in `SKILL.md` only when the implementation is reviewed and considered safe.  
- `SkillRegistry` enforces this at runtime; `SkillRegistry.get_executable(...)` returns `None` for non‑approved skills.

This is analogous to:

- A PR‑review gate in a codebase: “spec and implementation must be reviewed before execution is allowed.”

---

## First‑class example skills

Current reference skills that illustrate this pattern:

- `bug_fix`:
  - Spec: `skills/bug_fix/SKILL.md`.  
  - Implementation: `skills/bug_fix/skill.py`.  
  - Behavior: parses an error message, file, and line range; proposes a fix; writes a test; runs `pytest`.

- `refactor_extract_function`:
  - Spec: `skills/refactor_extract_function/SKILL.md`.  
  - Implementation: `skills/refactor_extract_function/skill.py`.  
  - Behavior: extracts a block of code into a helper function; updates the caller; writes a test.

These demonstrate that:

- The **spec** (`SKILL.md`) defines what the skill is and under what conditions it can run,  
- The **implementation** (`skill.py`) defines exactly how it operates, using the agent’s tools and constraints.

---

## How to create a new skill

1. Create the directory:

   ```text
   skills/<skill_name>/
   ```

2. Add `SKILL.md` with front‑matter:

   ```yaml
   ---
   name: <skill_name>
   description: Brief description.
   trigger: /skill <skill_name> ...
   allowed_tools:
     - read_file
     - write_file
     - ...
   constraints:
     - List of safety rules.
   status: proposed
   ---
   ```

3. Add `skill.py`:

   ```python
   from py_mono.skill.base import Skill, SkillContext

   class <SkillName>Skill(Skill):
       def name(self) -> str:
           ...

       def description(self) -> str:
           ...

       def run(self, request: str, context: SkillContext) -> str:
           # Implement using agent_tools from context
           ...
   ```

4. When the skill is reviewed and deemed safe:

   - Change `status: proposed` → `status: approved` in `SKILL.md`.  
   - The agent can then execute it via `/skill <skill_name> ...`.
```


