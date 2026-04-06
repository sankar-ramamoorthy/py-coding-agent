---
name: bug_fix
description: Fix a bug from a stack trace or error message.
trigger: /skill bug_fix <error> file:<path> [line:<num>]
allowed_tools:
  - read_file
  - write_file
  - shell
  - edit_file
  - list_files
constraints:
  - No file deletion.
  - No new dependencies.
  - No editing of .env or key files without explicit approval.
status: approved
---
# bug_fix

A skill to fix a bug from a stack trace or error message.

**When to use:**

- The user provides a stack trace or error message and identifies a file and (optional) line.
- The user wants a minimally invasive fix that preserves existing behavior.
