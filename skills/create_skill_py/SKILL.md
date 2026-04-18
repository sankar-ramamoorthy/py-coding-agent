
---

# 📄 `skills/create_skill_py/SKILL.md`

---
name: create_skill_py
description: Generate a skill.py from an existing SKILL.md using deterministic or LLM-assisted modes.
status: approved
execution_mode: hybrid
allowed_tools:
  - list_files
  - read_file
  - write_file
constraints:
  - workspace-only
  - prevents-overwriting: true (unless --overwrite is provided)
---

# create_skill_py

This meta-skill generates a `skill.py` file for an existing skill by reading its `SKILL.md`.

It functions as a compiler:

- `SKILL.md` → specification
- `skill.py` → executable implementation

---

## Usage

```bash
/skill create_skill_py <skill-name> [--overwrite] [--llm]
````

### Arguments

* `<skill-name>`
  Name of the skill directory inside `./skills/`

### Flags

* `--overwrite`
  Overwrite an existing `skill.py`

* `--llm`
  Force LLM enhancement regardless of `execution_mode`

---

## Execution Modes

Defined in YAML frontmatter:

* `deterministic` → generate scaffold only
* `llm` → full LLM-generated implementation
* `hybrid` → scaffold + LLM enhancement (default)

---

## Expected Logic

1. Resolve `./skills/<skill-name>/`
2. Ensure `SKILL.md` exists
3. If `skill.py` exists:

   * require `--overwrite`
4. Parse YAML:

   * name
   * description
   * allowed_tools
   * execution_mode
5. Extract `## Expected Logic` section
6. Generate deterministic scaffold
7. Apply execution mode:

   * deterministic → keep scaffold
   * llm → full LLM generation
   * hybrid → enhance scaffold with LLM
8. Validate generated code
9. Write `skill.py`

---

## Expected Output

### Deterministic

```
✅ skill.py generated for '<skill-name>'
Location: ./skills/<skill-name>/skill.py
🧱 Deterministic
```

### LLM

```
✅ skill.py generated for '<skill-name>'
Location: ./skills/<skill-name>/skill.py
🤖 LLM-generated
```

### Hybrid

```
✅ skill.py generated for '<skill-name>'
Location: ./skills/<skill-name>/skill.py
⚙️ Hybrid (scaffold + LLM)
```

### Errors

Missing SKILL.md:

```
❌ No SKILL.md found
```

Overwrite required:

```
❌ skill.py already exists
Use --overwrite to regenerate.
```

Validation failure:

```
❌ Generated skill.py failed validation:
<reason>
```


---

