# docs\adr\ADR-013-Skill-Approval-and-Chaining.md
````markdown
# ADR-013: Skill Approval and Chaining Policy

Date: 2026-03-30

**Status:** `accepted`

**Implementation Notes: corrected 2026-08-03** — this ADR's stated policy ("proposed":
Execution Allowed? No) was correct, but `SkillRegistry.load()`/`reload_skill()` did not
actually enforce it: a proposed skill's `skill.py` executed at load time regardless of
status (the module was `exec_module`'d before any status check ran). This was a gap
between this ADR's intent and the implementation, not a policy change. Fixed in ISS-003
(`specs/004-fix-skill-tool-approval-gate/`): load-time execution is now gated on both
`status: approved` and a separate, tamper-evident approval-ledger record (a content hash
of `skill.py` recorded at approval time, checked against the file's current content) —
editing `skill.py` after approval invalidates it until explicitly re-approved. See that
spec for the full mechanism; this ADR's policy statements below remain accurate and
unchanged.

---

## Context

The agent supports dynamic skill generation and execution (ADR-010, ADR-011, ADR-012). To maintain safety and enforce human oversight:

- Skills can be scaffolded interactively using `/skill generate-skill`.  
- Skills may call other skills for multi-step workflows.  
- Approval of skills must be **human-controlled**.  
- Certain skills (trusted / dev-only) may bypass sandbox restrictions.  

Without clear rules, unapproved skills could execute, chain dangerously, or bypass safety constraints.

---

## Decision

1. **Skill Status Lifecycle**

| Status       | Meaning                                         | Execution Allowed? |
|-------------|-------------------------------------------------|-----------------|
| `proposed`  | Newly scaffolded or edited skill                | ❌ No            |
| `approved`  | Explicitly approved by human developer         | ✅ Yes           |
| `deprecated`| Obsolete or unsafe skill                        | ❌ No            |

- The `status` field in `SKILL.md` is the **primary enforcement mechanism**.  
- Only a **CLI or human developer** may toggle status.  
- Skills **cannot approve other skills**; the approval operation is never chainable.

2. **Chaining Rules**

- Skills may call other skills (`/skill <other>`) for modular workflows.  
- Chaining is **subject to status checks**:  
  - A skill may only invoke another skill if it is `approved`.  
  - Attempting to call `proposed` or `deprecated` skills results in immediate rejection.  

3. **Trusted vs Regular Skills**

- Trusted skills are explicitly flagged (internal, non-editable by users).  
- Trusted skills may bypass some sandbox constraints (e.g., scaffolding new skills, dry-run tools).  
- All other skills inherit sandbox rules: file writes restricted to `/workspace`, no access to system files, network or destructive actions require explicit approval or dry-run mode.

4. **Sandbox Enforcement**

- File writes outside `/workspace` are rejected.  
- Skills inherit these restrictions unless explicitly trusted.  
- Network, shell, or destructive actions must either be trusted or use `dry_run` mode.

---

## Diagram: Skill Approval and Chaining (Mermaid)

```mermaid
flowchart TD
    A[CLI / Human Approves Skill] --> B[SkillRegistry]
    B --> C{Skill Status?}
    C -->|Approved| D[Execution Allowed]
    C -->|Proposed/Deprecated| E[Reject Execution]
    D --> F{Skill Calls Another Skill?}
    F -->|Yes| C
    F -->|No| G[Finish Execution]
````

## Skill Approval and Chaining Policy

### Context

While the agent supports dynamic skill generation and execution, we need **strict rules around approval and chaining** to prevent unsafe or unintended skill execution. Key points:

- Skills can invoke other skills for modular workflows.  
- **No skill may approve another skill**; approval is a human-controlled operation.  
- Certain skills are **trusted** (e.g., dev-only scaffolding or internal admin) and can bypass sandbox restrictions; all others inherit strict constraints.  
- The CLI and SkillRegistry enforce execution rules; the agent must not allow unapproved skills to run automatically.

---

### Decision

1. **Skill Status Lifecycle**

| Status      | Meaning                                        | Execution Allowed? |
|------------|------------------------------------------------|-----------------|
| `proposed` | Newly scaffolded or edited skill               | ❌ No             |
| `approved` | Explicitly approved by human developer         | ✅ Yes            |
| `deprecated` | Skill is obsolete or unsafe                  | ❌ No             |

- The `status` field is the primary enforcement mechanism.  
- Only the **CLI or human developer** may toggle status.  
- Skills cannot auto-promote or approve other skills.

2. **Chaining Rules**

- Skills **may call other skills** (`/skill <other>`) to implement multi-step workflows.  
- Chaining is **subject to status checks**:  
  - A skill can only call another skill if it is `approved`.  
  - Calling a `proposed` or `deprecated` skill results in an immediate rejection.  
- The **approval skill itself is never chainable**.

3. **Trusted vs Regular Skills**

- Trusted skills are explicitly marked (internal flag, not editable by users).  
- Trusted skills may bypass some sandbox constraints (e.g., generating new skills, scaffolding, dry-run tools).  
- All other skills inherit the sandbox policy (`/workspace` only, no system paths).

4. **Sandbox Enforcement**

- File writes outside `/workspace` are rejected by default.  
- Skills inherit the same restrictions unless explicitly trusted.  
- Network, shell, or destructive actions require explicit approval or dry-run mode.

---

### ALternate ASCII Diagram: Skill Approval and Chaining

```text
+-----------------+
|  CLI / Human    |
|  Approves Skill |
+--------+--------+
         |
         v
   +-----+------+
   |  Skill     | 
   |  Registry  |
   +-----+------+
         |
         v
+---------------------+        +---------------------+
| Proposed / Approved  |------->| Can chain? Check    |
| / Deprecated Status  |         | target skill status|
+---------------------+         +---------------------+
         |                              |
         | ❌ Proposed/Deprecated       | ✅ Approved
         |                              |
         v                              v
   Reject execution                 Allow execution
---

## Consequences

**Pros**

* Clear separation of approval responsibilities between humans and the agent.
* Prevents accidental promotion or execution of unreviewed skills.
* Supports modular workflows with safe skill chaining.
* Trusted flags allow controlled bypasses for development tasks.

**Cons**

* Extra CLI discipline required to approve skills.
* Testing new skills may require dry-run mode until approval.
* Trusted flags must be carefully managed to avoid privilege abuse.

**Long-term Impact**

* Provides a secure, auditable workflow for skill development and deployment.
* Supports modular, multi-step skill workflows without compromising safety.
* Aligns with ADR-010, ADR-011, and ADR-012 principles: sandboxed execution, discoverability, and local Python execution.

---

## Related ADRs

* ADR-010: Agent Skills Layer
* ADR-011: Interactive Skill Scaffolding
* ADR-012: Skills vs Tools Clarification

```

---
