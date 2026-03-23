
---

# ADR 003: Pi-Mono Style Minimal Agent Loop

**Status:** Proposed
**Date:** 2026-03-21

## Context

Python coding agents often face a tradeoff between **complex reasoning orchestration** and **simplicity/reliability**.

Prior approaches attempted:

* Multi-step reasoning prompts.
* Forced tool-finalization phases.
* Elaborate system prompts with tool usage rules.

These approaches introduced:

* Fragile behavior when tools returned unexpected outputs.
* Overly complicated memory management.
* Frequent loops or repeated tool calls.

A simpler, more robust pattern is needed.

---

## Decision

Adopt the **Pi-Mono Style Minimal Loop**, characterized by:

1. **Single Loop Structure**

   * The agent maintains **one loop** per user query.
   * The LLM decides **if a tool should be called or if a final answer can be returned**.
   * No intermediate “final answer” prompts are enforced externally.

2. **Memory Management**

   * Memory tracks:

     * User messages
     * Assistant tool calls
     * Tool results
     * Assistant text outputs
   * Memory is **incrementally appended** to, preserving context for the LLM.
   * No reconstruction of artificial “final answer” contexts is required.

3. **Tool-Oriented Interaction**

   * All operations that require file, shell, or other system access must be delegated to tools.
   * Tool calls are explicitly recorded in memory.
   * Tool results are fed **back into the loop** for the LLM to decide next steps.

4. **LLM-Driven Decision Making**

   * The LLM decides:

     * Which tool to call and with what arguments
     * When to stop calling tools and produce a final answer
   * Agent enforces **loop safety** (prevent repeated identical calls).

5. **Safety and Sandboxing**

   * The agent enforces sandbox constraints (e.g., `/workspace`).
   * Tools must follow safe templates (resolve paths, return LLM-friendly outputs).
   * Repeated calls trigger a system message to nudge the LLM to use prior results.

6. **No Forced Finalization**

   * The agent does not externally coerce the LLM into producing a final answer.
   * Trusts the LLM’s internal reasoning.
   * Minimal intervention maintains pi-mono philosophy: **“the loop is minimal, the LLM drives action.”**

---

## Consequences

* **Robustness:** Reduced risk of broken multi-step orchestration.
* **Simplicity:** No complex tool-finalization logic or memory reconstruction.
* **Extensibility:** Dynamic tools can be added at runtime without changing loop structure.
* **Safety:** Sandbox enforcement remains intact.
* **User Interaction:** LLM can respond flexibly to user requests, creating tools or returning answers.

---

### Example Flow

```text id="pi-mono-flow"
User: "List files in /workspace"
  |
Agent appends user message to memory
  |
LLM decides: tool_call("list_files", {"path": "."})
  |
Agent executes tool → memory updated with tool result
  |
LLM sees tool result → decides next step
  ├─ tool_call(...) → agent executes again
  └─ text → final answer returned
```

**Notes:**

* Each tool execution is a **single step**.
* LLM sees prior tool results before each decision.
* Loop continues until LLM returns text (final answer) or max steps reached.

---

This ADR codifies the **pi-mono style minimal loop** philosophy: **simplicity, LLM-driven decision-making, and tool-focused execution.**

---

