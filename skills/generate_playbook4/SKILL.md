---
name: generate_playbook4
description: generate a Markdown playbook( aka skill.md). The playbook guides reasoning (not execution) and only creates a valid markdown .md file. The playbook has to provide structured guidance. The playbook will be provided the issue about which to reason by the user
status: approved
allowed_tools:
  - list_files
  - read_file
  - write_file
  - edit_file
  - get_current_datetime

---

# generate_playbook4

This skill takes a user-supplied issue and produces a concise, structured Markdown playbook (skill.md) that offers step-by-step reasoning guidance—no code execution, just human-readable instructions.

## Usage

````

/skill generate_playbook4

````

## Expected Output

A new or updated `skill.md` file in the workspace containing clear, ordered reasoning steps tailored to the issue.

## Constraints

- Only reads/writes files inside the workspace
- Does not run or install code
- No network access