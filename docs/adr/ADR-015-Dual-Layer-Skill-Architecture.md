Great—this is exactly the right moment to formalize things before the design ossifies. I’ll do three things for you in this message:

1. **Give you a clean README update** (drop-in ready)
2. **Propose an ADR (new + what to revisit)**
3. **Refactor your terminology + architecture (practical, not theoretical)**

Then you can send your codebase and we’ll align it concretely.

---

# 1️⃣ README update (drop-in section)

You don’t need to rewrite everything—add this as a new section:

## Skill Model Clarification (Execution vs Reasoning)

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

```text
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

---

# 2️⃣ ADR recommendation

You should **create a new ADR**, not just mutate existing ones.

## 📄 New ADR: “ADR-0XX: Dual-Layer Skill Architecture”

# ADR-0XX: Dual-Layer Skill Architecture

## Status

Proposed

## Context

The current system defines “skills” as executable Python workflows gated by approval.

However, modern agent systems distinguish between:

* Reasoning guidance (prompt-based, LLM-interpreted)
* Execution workflows (code-driven, deterministic)

The current design lacks an explicit reasoning layer, leading to:

* Overloading of the term “skill”
* No structured way to guide LLM decision-making
* Manual invocation via `/skill ...`

## Decision

We adopt a three-layer model:

1. Reasoning Layer

   * Markdown-based playbooks
   * Retrieved dynamically
   * Not gated
   * Used only by the LLM

2. Orchestration Layer

   * Responsible for selecting execution skills
   * May be LLM-driven or rule-based
   * Replaces manual `/skill` invocation over time

3. Execution Layer (existing system)

   * Python-based skills
   * Gated via `status: approved`
   * Deterministic and testable

## Consequences

### Positive

* Clear separation of concerns
* Improved reasoning quality
* Enables automatic skill selection
* Aligns with industry agent patterns

### Negative

* Increased architectural complexity
* Requires retrieval/indexing system for playbooks
* Requires orchestration logic

## Follow-ups

* Introduce `playbooks/` directory
* Implement retrieval mechanism (embedding or keyword-based)
* Add skill selection interface (LLM or heuristic)
* Gradually deprecate `/skill` as primary interface

---

## 🔍 What to check in your existing ADRs

Look for anything that:

### Might need updating:

* ADR-010 (you referenced it)

  * It likely assumes **skills = full behavior**
  * Needs clarification: skills = execution only

### Search your ADRs for:

* “skill defines behavior”
* “LLM uses SKILL.md to act”
* “skills encapsulate reasoning”

👉 Those are now **incorrect or incomplete**

---

# 3️⃣ Renaming + architecture (practical)

## 🔁 Rename (minimal disruption)

Don’t rename files yet—rename concepts:

* `Skill` class → keep as-is (internal)
* In docs/UI:

  * “Skill” → **Execution Skill**
* Add new concept:

  * **Playbook** (better than “Reasoning Skill” IMO)

---

## 🧱 Add new structure

```
playbooks/
  debugging/
    DEBUGGING.md
  testing/
    TEST_WRITING.md
  refactoring/
    EXTRACT_FUNCTION.md
```
## Implementation
Create `playbooks/` directory:

playbooks/
  debugging/DEBUGGING.md
  testing/TEST_WRITING.md
  refactoring/EXTRACT_FUNCTION.md

LLM may reference these for reasoning; they are not executable.
---

## 🧠 Orchestration (first simple version)

Before going full LLM autonomy, do this:

### Step 1: skill suggestion layer

LLM returns:

```json
{
  "intent": "fix_bug",
  "suggested_skill": "bug_fix"
}
```

### Step 2: runtime executes if approved

---

## 🚀 Later evolution

* Replace `/skill` with:

  ```
  user → LLM → skill selection → execution
  ```

---

| Layer            | Location                        | Note                                                                          |
| ---------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| Execution Skills | `skills/`                       | Existing system; no code rename needed, just documentation terminology update |
| Playbooks        | `playbooks/`                    | New; add retrieval logic later (keyword or embeddings)                        |
| Orchestration    | `py_mono/agent/orchestrator.py` | Minimal wrapper now; LLM-driven later                                         |


