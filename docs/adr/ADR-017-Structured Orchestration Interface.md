
# docs\adr\ADR-017-Structured Orchestration Interface.md
---

# 📄 ADR-017: Structured Orchestration Interface (LLM ↔ Skills)

## Status

Proposed

---

## Context

ADR-015 introduced a multi-layer architecture:

* Reasoning Layer (Playbooks)
* Orchestration Layer
* Execution Layer (Skills)

ADR-016 established strict boundaries:

* Only skills may perform side effects
* The LLM cannot directly use tools
* Orchestration mediates execution

However, the current system still relies on:

* Unstructured natural language responses
* Manual `/skill ...` invocation
* Implicit intent detection

This creates ambiguity:

* The system cannot reliably determine when a skill should be used
* Skill invocation is not machine-readable
* Automation and composition are limited

---

## Decision

We introduce a **structured orchestration interface** between the LLM and the runtime.

The LLM must return **structured outputs** that explicitly indicate:

* Whether to use a skill
* Which skill to use
* What inputs to provide

---

## Response Schema

All LLM responses must conform to the following JSON structure:

```json
{
  "action": "answer" | "use_skill",
  "skill": "<skill_name | null>",
  "arguments": "<string or structured input>",
  "reason": "<brief explanation>"
}
```

### Field definitions

* `action`

  * `"answer"` → respond directly to the user
  * `"use_skill"` → invoke an execution skill

* `skill`

  * Required if `action = "use_skill"`
  * Must match a registered skill name

* `arguments`

  * Input passed to the skill
  * Initially a string; may evolve into structured JSON

* `reason`

  * Short explanation of why this action was chosen
  * Used for logging and debugging

---

## Orchestration Flow

1. User submits request
2. Playbooks are retrieved and injected into the prompt
3. LLM generates a structured response
4. Runtime parses the response

### If `action = "answer"`

* Return the response directly to the user

### If `action = "use_skill"`

* Validate skill exists
* Check skill approval status
* If approved:

  * Execute skill with provided arguments
  * Return result to user
* If not approved:

  * Reject execution and return error

---

## Validation Rules

The runtime MUST enforce:

* Valid JSON output
* `action` must be one of the allowed values
* `skill` must exist in `SkillRegistry`
* Skill must be `approved`
* Arguments must be present when required

Invalid responses must trigger:

* A retry (optional), or
* A fallback to safe failure

---

## Design Principles

### 1. Explicit over implicit

Skill usage must be explicitly declared, not inferred.

---

### 2. LLM decides *intent*, not execution

* LLM selects the action
* Runtime executes it safely

---

### 3. Loose coupling

* The LLM does not call skills directly
* The runtime does not perform reasoning

---

### 4. Evolvability

The schema is intentionally minimal and may evolve to include:

* Typed arguments (JSON schema)
* Multiple actions (batch execution)
* Tool chaining

---

## Example

### Input

```text
Fix the failing test in test_math.py
```

### LLM Output

```json
{
  "action": "use_skill",
  "skill": "bug_fix",
  "arguments": "test_math.py failing test details...",
  "reason": "Bug fixing requires code modification and testing"
}
```

---

## Consequences

### Positive

* Reliable skill invocation
* Enables automation and chaining
* Clear separation of reasoning and execution
* Easier debugging and observability
* Foundation for advanced orchestration

### Negative

* Requires strict prompt engineering
* Adds parsing and validation complexity
* LLM errors must be handled explicitly

---

## Relationship to Previous ADRs

* ADR-015 defines the layered architecture
* ADR-016 enforces boundaries and invariants
* ADR-017 defines the **communication protocol** between layers

Together they form:

* Structure
* Constraints
* Interaction model

---

## Follow-ups

* Implement response parser and validator
* Add retry logic for malformed outputs
* Introduce logging for `reason` field
* Extend `arguments` to structured JSON
* Add support for multi-step orchestration

---

## Future Considerations

* Multi-skill workflows (task graphs)
* Tool/skill composition
* Stateful planning across multiple steps
* Confidence scoring for decisions
* Human-in-the-loop approval for risky actions

---

💬 **Why this is a big deal**


With this ADR, your system becomes:

> “LLM declares intent, runtime enforces execution”

That’s the transition from a **chatbot with tools** → **actual agent system**

---
