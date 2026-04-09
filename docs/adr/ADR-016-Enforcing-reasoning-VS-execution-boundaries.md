---

# 📄 ADR-016: Enforcement of Reasoning vs Execution Boundaries

## Status

Proposed

---

## Context

ADR-015 introduced a dual-layer architecture separating:

* Reasoning (Playbooks, LLM-driven)
* Execution (Skills, deterministic and gated)
* Orchestration (selection of skills)

While this defines the intended structure, it does not yet enforce:

* Where logic is allowed to live
* How side effects are controlled
* How the LLM interacts with execution capabilities

Without explicit constraints, the system risks architectural drift:

* Embedding execution logic in playbooks
* Using skills for reasoning instead of execution
* Bypassing approval mechanisms through direct tool usage

---

## Decision

We formalize **strict boundaries and invariants** between layers.

### 1. Execution Boundary (Hard Constraint)

All side effects MUST occur through approved execution skills.

This includes:

* File reads/writes
* Running tests or commands
* Modifying code
* Any interaction with the workspace or external tools

The LLM MUST NOT directly perform tool actions.

---

### 2. Playbook Constraints (Reasoning Only)

Playbooks:

* MUST contain only reasoning guidance
* MUST NOT include executable instructions or tool calls
* MUST NOT assume direct access to the filesystem or runtime

They may include:

* Strategies
* Heuristics
* Step-by-step reasoning patterns
* Suggested skills

---

### 3. Skill Responsibilities (Execution Only)

Execution skills:

* MUST implement concrete, bounded workflows
* MUST NOT perform open-ended reasoning
* MUST NOT decide *whether* they should be used

They:

* Accept structured input
* Perform deterministic or semi-deterministic operations
* Return structured or human-readable results

---

### 4. Orchestration Responsibility

The orchestration layer is the **only component** responsible for:

* Deciding whether to use a skill
* Selecting which skill to invoke
* Passing arguments to skills

This decision may be:

* LLM-driven
* Rule-based
* Hybrid

---

### 5. Approval Enforcement

The existing approval model remains mandatory:

* Only skills with `status: approved` may execute
* Orchestration MUST respect this constraint
* No bypass mechanisms are allowed

---

## Invariants

The following must always hold:

1. The LLM cannot directly mutate the workspace
2. All side effects go through approved skills
3. Playbooks do not execute
4. Skills do not decide when they are used
5. Orchestration mediates all execution

---

## Anti-Patterns (Explicitly Disallowed)

The following are considered violations of the architecture:

* Embedding tool usage instructions inside playbooks
* Writing skills that perform high-level reasoning or decision-making
* Allowing the LLM to call tools directly
* Executing unapproved skills
* Treating playbooks as executable workflows

---

## Consequences

### Positive

* Strong safety guarantees
* Clear separation of concerns
* Easier testing and auditing
* Prevents architectural drift
* Enables reliable automation and orchestration

### Negative

* Increased rigidity in system design
* Requires explicit orchestration logic
* May slow rapid prototyping

---

## Relationship to ADR-015

This ADR **does not replace ADR-015**.

* ADR-015 defines the architecture
* ADR-016 enforces the rules of that architecture

Together they define both:

* Structure (what exists)
* Constraints (how it must behave)

---

## Follow-ups

* Implement guardrails in the agent loop to prevent direct tool access
* Ensure all tool interfaces are only exposed via `SkillContext`
* Add validation tests for skill approval enforcement
* Introduce structured outputs for orchestration decisions
* Optionally add linting or checks for playbook content

---

## Future Considerations

* Typed skill inputs/outputs (schema validation)
* Skill composition (multi-step execution chains)
* Playbook retrieval improvements (embeddings, ranking)
* Observability (logging reasoning vs execution separately)

---

💬 **Why this ADR matters**

ADR-015 gave you a *clean model*.
ADR-016 makes sure your system doesn’t slowly collapse back into:

> “LLM does everything + skills are optional”

This is the one that keeps your architecture **honest over time**.

---
