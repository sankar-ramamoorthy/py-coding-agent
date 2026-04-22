---
name: generate_playbook
description: Generate a new reasoning playbook Markdown file with YAML front-matter for PlaybookRegistry
trigger: /skill generate_playbook category:<name> | description:<text> | keywords:<csv> | dry_run:<true|false>
status: approved
allowed_tools:
    - list_files
    - read_file
    - write_file
    - edit_file
constraints:
    - Write-only. No code execution.
    - Output path must be playbooks/<category>/*.md only.
    - Must include valid YAML front-matter: name, description, keywords, triggers.
    - No network access.
---

# generate_playbook

Creates a Markdown playbook that guides reasoning, not execution. Playbooks are injected by PlaybookRegistry.

**When to use:**
- User wants to codify a repeated workflow: debugging, refactoring, testing, design.
- Existing playbooks don’t cover the use case.

**What this skill does:**
1. Takes category, description, keywords from user
2. Calls LLM once to generate structured Markdown with front-matter
3. Validates YAML + required sections
4. Writes to playbooks/<category>/<slug>.md
5. Returns diff for dry_run=true, writes file if false

**Constraints:**
- No executable code in output
- Path traversal blocked: must stay in playbooks/
- Filename slugified from description, max 50 chars