
***


### ✅ MS5‑IS6 – `docs/skills/README.md`

Create:

```text
docs/skills/README.md
```

and use this as a living document that explains:

- How to define a skill,  
- The interaction pattern between `SKILL.md`, `skill.py`, and `run(...)`,  
- Examples from `bug_fix` and `refactor_extract_function`.

Here’s a concrete starter:

```markdown
# Skills Layer – Developer Guide

This directory contains all **agent skills** for `py-coding-agent`.  
Skills are reusable workflows that the agent can call via `/skill <name> ...`.

## Overview

Each skill lives under:

```text
skills/<skill_name>/
    SKILL.md        ← human‑readable spec and config
    skill.py        ← optional Python implementation (Skill subclass)
```

The skills are discovered and registered by `SkillRegistry` at startup.

## Skill Approval Model (ADR‑010)

All skills are defined via `SKILL.md` front‑matter like:

```yaml
***
name: bug_fix
description: Fix a bug from a stack trace or error message.
status: proposed  # or "approved"
***
```

- `status: proposed` → skill is **known but not executable**.  
- `status: approved` → agent may run it via `/skill ...`.

You review and flip `status` in Git (or locally) to gate execution.

## Example: bug_fix

Skill path:

```text
skills/bug_fix/
    SKILL.md
    skill.py
```

Usage:

```text
/skill bug_fix "KeyError: 'foo'" file:src/foo.py line:42
```

Behavior:
- Reads the file around the line.  
- Proposes a minimal fix.  
- Writes a test.  
- Runs `pytest` and shows outcome.

## Example: refactor_extract_function

Skill path:

```text
skills/refactor_extract_function/
    SKILL.md
    skill.py
```

Usage:

```text
/skill refactor_extract_function file:src/foo.py start:42 end:48 name:calculate_discount
```

Behavior:
- Extracts the block into a helper function.  
- Updates the original function to call it.  
- Writes a test.  
- Shows the diff.

## How to Add a New Skill

1. Create the directory:

   ```bash
   mkdir skills/<skill_name>
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
     - edit_file
     # ...
   status: proposed
   ---
   ```

3. Add `skill.py` subclassing `Skill`:

   ```python
   from py_mono.skill.base import Skill, SkillContext

   class <SkillName>Skill(Skill):
       def name(self) -> str: ...
       def description(self) -> str: ...
       def run(self, request: str, context: SkillContext) -> str: ...
   ```

4. Set `status: approved` once you’re ready to run it.

## Safeguards and Constraints

Skills are executed inside a sandboxed workspace and are constrained by:

- No file deletion.  
- No new dependencies.  
- No changes to `.env` or key files.  
- Approval gate (`status: approved`).
```

***
