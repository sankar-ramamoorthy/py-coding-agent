---
name: doc_sync
description: Synchronize docstrings and README sections with current code signatures
trigger: /skill doc_sync code:<path> docs:<path> [target:function|class|module|readme] [dry_run:<true|false>]
status: approved
allowed_tools:
    - read_file
    - write_file
    - edit_file
    - list_files
constraints:
    - No file deletion.
    - No new dependencies.
    - No changes to.env or key files.
    - Prefer minimal edits. Human-reviewable diffs.
    - Must not rewrite entire files unless docs:<path> is empty.
---

# doc_sync

Keeps documentation synchronized with code after refactors or API changes.

**When to use:**
- Docstring params don’t match function signature
- README examples use old function names
- Added/removed parameters not reflected in docs

**What this skill does:**
1. Parse code with AST to extract actual functions/classes/params/returns
2. Parse docs to find existing docstrings or README sections
3. Use LLM to rewrite docs matching code reality
4. Show diff. Apply if dry_run:false
5. No tests to run, but validates Markdown/PEP-257 format

**Constraints:**
- Minimal diffs only. Won’t regenerate whole README.
- If docs:<path> doesn’t exist, creates it with basic structure.