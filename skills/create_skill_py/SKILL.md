---
name: create_skill_py
description: Generate a skill.py from an existing SKILL.md using deterministic or LLM-assisted modes
trigger: /skill create_skill_py <skill-name> [--overwrite] [--llm] [--dry_run]
status: approved
execution_mode: hybrid
allowed_tools:
    - list_files
    - read_file
    - write_file
constraints:
    - workspace-only. Must stay in./skills/<skill-name>/
    - prevents-overwriting: true (unless --overwrite is provided)
    - Must validate generated code with validate_skill_py before writing
    - No network access except LLM provider call
---

# create_skill_py

Meta-skill that compiles `SKILL.md` spec → `skill.py` implementation.

## Usage
/skill create_skill_py <skill-name> [--overwrite] [--llm]


### Arguments
* `<skill-name>`: Directory name under `./skills/`. Must match `^[a-z0-9][a-z0-9-]*$`

### Flags
* `--overwrite`: Replace existing `skill.py`
* `--llm`: Force LLM mode even if YAML says `deterministic`
* `--dry_run`: Show generated code, don't write file

## Execution Modes
From SKILL.md YAML `execution_mode`:
* `deterministic`: Scaffold only. Fast, predictable.
* `llm`: Full LLM generation. Use for complex logic.
* `hybrid`: Scaffold + LLM enhancement. Default.

## Expected Logic
1. Resolve `./skills/<skill-name>/` and verify `SKILL.md` exists
2. Check `skill.py` exists. If yes, require `--overwrite`
3. Parse YAML front-matter: `name`, `description`, `allowed_tools`, `execution_mode`
4. Extract `## Expected Logic` section from Markdown body
5. Build deterministic scaffold with `Skill` subclass
6. Apply execution_mode: call LLM if `llm` or `hybrid`
7. Strip markdown fences, remove `<thinking>` blocks
8. Run `validate_skill_py`. Fail if invalid.
9. If `--dry_run`, return code preview. Else write `skill.py`

## Expected Output

### Success
✅ skill.py generated for 'bug_fix'
Location:./skills/bug_fix/skill.py
⚙️ Hybrid (scaffold + LLM)

### Dry run

[DRY RUN] Would create./skills/bug_fix/skill.py
=== Code Preview ===
from py_mono.skill.base import Skill, SkillContext
...

### Errors
❌ No SKILL.md found in./skills/bug_fix
❌ skill.py already exists. Use --overwrite to regenerate.
❌ Generated skill.py failed validation: Missing run() method
❌ Invalid YAML in SKILL.md: execution_mode must be deterministic|llm|hybrid