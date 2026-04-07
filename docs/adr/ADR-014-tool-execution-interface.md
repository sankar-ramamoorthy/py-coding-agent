---

# docs\adr\ADR-014-tool-execution-interface.md

---

````markdown
# ADR-014: Tool Execution Interface (`Tool.run`)

**Status:** Accepted  
**Date:** 2026-04-06  
**Milestone:** 5

---

## Context

Early versions of the agent treated tools as direct Python functions:

```python
tool.func(...)
````

This created several issues:

* No enforcement of argument structure
* Inconsistent usage across skills and generated code
* Tight coupling between agent and tool implementation
* LLM frequently generated incorrect calls:

  * positional arguments
  * dict-as-positional (`tool.func({...})`)
* Difficult to validate or intercept tool execution

Additionally, prompts and system code diverged, causing runtime errors.

---

## Decision

Introduce a strict execution interface:

```python
Tool.run(**kwargs)
```

### Rules

* All tool execution MUST go through `Tool.run(...)`
* Arguments MUST be passed as keyword arguments
* Direct access to `tool.func` is forbidden outside the Tool class
* `_func` is considered private implementation detail

### Final Tool Implementation

```python
class Tool:
    def run(self, **kwargs):
        return self._func(**kwargs)
```

---

## Rationale

### 1. Enforces Consistency

All tools follow the same invocation pattern:

```python
tool.run(path="file.txt")
```

---

### 2. Enables Validation Layer

Future capabilities:

* argument validation
* logging
* tracing
* retries
* permission checks

---

### 3. LLM Alignment

LLMs perform significantly better with:

```python
tool.run(command="ls")
```

vs:

```python
tool.func({...})
```

---

### 4. Abstraction Boundary

Separates:

| Layer    | Responsibility      |
| -------- | ------------------- |
| Agent    | orchestration       |
| Tool.run | interface + control |
| _func    | implementation      |

---

## Consequences

### Benefits

* Eliminates incorrect tool usage patterns
* Enables future middleware (logging, safety, retries)
* Improves LLM reliability
* Cleaner architecture boundary

---

### Trade-offs

* Slightly more abstraction vs direct function calls
* Requires updating existing tools and skills
* Requires prompt alignment

---

## Migration

### Before

```python
tool.func({"path": "file.txt"})
```

### After

```python
tool.run(path="file.txt")
```

---

## Enforcement

* Prompts explicitly require `tool.run(...)`
* Validator rejects `.func(...)`
* Skills updated to use `.run(...)`
* `_func` treated as private

---

## Related ADRs

* ADR-005: Multi-Provider LLM Support
* ADR-011: Interactive-Skill-Scaffolding
* ADR-012: Skills vs Tools Clarification
* ADR-013: Skill Approval and Chaining Policy


---

## Future Work

* Add argument schema validation using `parameters`
* Add execution middleware (logging, retries)
* Add permission enforcement per tool

````

---

