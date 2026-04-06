
A first‑class `doc_sync` skill does:

- Given a code file (or pattern) and docs/markdown,  
- Read both,  
- Update doc comments or README sections to match the current code,  
- Write back the updated docs.

You can implement it very similarly to `bug_fix` and `refactor_extract_function`:

#### 1. `skills/doc_sync/SKILL.md`

```markdown
---
name: doc_sync
description: Synchronize doc comments and user‑facing docs with current code.
trigger: /skill doc_sync code:<path> docs:<path> [update_method:inplace|docstring]
allowed_tools:
  - read_file
  - write_file
  - edit_file
  - list_files
constraints:
  - No file deletion.
  - No new dependencies.
  - No changes to .env or key files.
  - Prefer minimal edits (no complete rewrites).
status: proposed
---
# doc_sync

A skill to keep documentation synchronized with code.

**When to use:**

- Docstrings no longer match the actual code.  
- `README.md` or guides refer to APIs that have changed.


**What this skill does:**

- Reads the code file (function, class, or entire module).  
- Reads the corresponding doc file or markdown.  
- Aligns high‑level descriptions and parameter lists with reality.  
- Writes back the updated doc (or docstring) file.  

**Constraints:**

- No file deletion.  
- No new dependencies.  
- No changes to `.env` or key files.  
- Changes should be minimal and human‑reviewable.
```

***

