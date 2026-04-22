
# README_Skills.md

```markdown
# Skills Layer Design
## Relation to project layout

- `py_mono/skill/` contains the skills framework (`Skill`, `SkillContext`, `SkillRegistry`).  
- `skills/` contains the concrete skill implementations (each in its own subdirectory with `SKILL.md` and `skill.py`).

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



## Skill Model Clarification (Execution vs Reasoning) 
# Dated 20260407. 
# My current Understanding.

### Important distinction

The term “skill” is overloaded across different agent systems.

In frameworks such as those described by Anthropic (Claude), a *skill* refers to a **prompt-based reasoning aid**:

* A Markdown document
* Interpreted dynamically by the LLM
* Used to guide *how the model thinks*

In contrast, in `py-coding-agent`, a *skill* refers to:

> A **deterministic, executable workflow implemented in Python and gated by approval**

This means:

* Our skills are **not prompt-driven behaviors**
* They are **reviewable, testable code units**
* They operate at the **execution layer**, not the reasoning layer

---

### Two-layer model (adopted)

To avoid confusion and improve capability, the system adopts a **dual-layer architecture**:

#### 1. Reasoning Layer (LLM-native)

* Format: Markdown (playbooks, heuristics, strategies)
* Interpreted by: the LLM
* Purpose: improve decision-making and problem-solving
* Examples:

  * Debugging strategies
  * Refactoring heuristics
  * Test-writing guidelines

These are **not gated** and **not executable**.

#### 2. Execution Layer (Skills)

* Format:

  * `SKILL.md` (spec)
  * `skill.py` (implementation)
* Interpreted by: the runtime system
* Purpose: perform concrete, deterministic actions
* Examples:

  * `bug_fix`
  * `refactor_extract_function`

These are:

* **Gated by approval**
* **Tool-using**
* **Deterministic**

---

### Terminology update

To reduce ambiguity:

| Old term | New term (preferred)     |
| -------- | ------------------------ |
| Skill    | Execution Skill          |
| SKILL.md | Execution Spec           |
| skill.py | Execution Implementation |

“Skill” may still be used informally, but in architecture discussions:

* “Execution Skill” = Python-backed workflow
* “Reasoning Skill” (or Playbook) = Markdown guidance

---

### Execution vs Reasoning responsibilities

| Responsibility                          | Layer           |
| --------------------------------------- | --------------- |
| Deciding what to do                     | Reasoning Layer |
| Deciding how to do it (algorithmically) | Reasoning Layer |
| Performing file edits, running tools    | Execution Layer |
| Producing deterministic outputs         | Execution Layer |

---

### Future direction: automatic skill selection

Currently, execution skills are invoked explicitly:

```
/skill bug_fix ...
```

Planned evolution:

* The LLM will:

  1. Analyze the request
  2. Select an appropriate execution skill
  3. Invoke it automatically

This introduces an **orchestration step** between reasoning and execution.

---

### Architectural summary

The system should be understood as:

1. **Reasoning Layer (LLM cognition)**
2. **Orchestration Layer (skill selection)**
3. **Execution Layer (approved Python skills)**

This separation aligns with modern agent architectures while preserving:

* Determinism
* Safety
* Reviewability

## ADR-016: Tool Usage Contract

All execution skills MUST follow ADR-016:

1. **No direct syscalls**: Never `import subprocess`, `os.system`, `open()` for writes, or `requests`
2. **Use agent_tools only**: All file/process/network I/O via `context.agent_tools["tool_name"].func({...})`
3. **Sandbox enforced**: `write_file` and `edit_file` validate paths stay under `workspace_root`

Violation = skill rejected by code review.

## Current Skill Inventory

Last updated: 2026-04-20

| Skill | Status | Mode | Dry-run | Description |
| --- | --- | --- | --- | --- |
| `bug_fix` | approved | hybrid | yes | Patch code from stack trace + pytest rollback |
| `refactor_extract_function` | approved | hybrid | yes | Extract block to helper + test |
| `doc_sync` | approved | hybrid | yes | Sync docstrings/README with AST |
| `generate_playbook` | approved | hybrid | yes | LLM-generate playbook .md with YAML |
| `create_skill_py` | approved | hybrid | yes | Compile SKILL.md → skill.py |
| `scaffold_project` | approved | deterministic | no | Bootstrap pyproject.toml + src/ |
| `generate_skill` | deprecated | llm | no | Use `create_skill_py` instead |
| `hello` | approved | deterministic | no | Test stub |

## Playbook vs Skill Cheat Sheet

|  | Playbook | Skill |
| --- | --- | --- |
| Location | `playbooks/<cat>/*.md` | `skills/<name>/` |
| File | Markdown only | `SKILL.md` + `skill.py` |
| Invocation | Automatic via keywords | Explicit `/skill <name>` |
| Writes files? | No | Yes, via tools |
| Needs approval? | No | Yes, `status: approved` |
| Example | `playbooks/testing/pytest_guide.md` | `skills/bug_fix/` |