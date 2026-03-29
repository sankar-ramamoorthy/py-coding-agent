---
name: refactor_extract_function
description: Extract a block of code into a new helper function, preserving behavior and tests.
trigger: /skill refactor_extract_function file:<path> start:<line> end:<line> name:<new_func_name>
allowed_tools:
  - read_file
  - write_file
  - edit_file
  - shell
  - list_files
constraints:
  - No file deletion.
  - No new dependencies.
  - No changes to .env or key files.
  - Must preserve existing behavior (no behavioral change).
status: approved
---
# refactor_extract_function

A skill to refactor by extracting a block of code into a new helper function.

**When to use:**

- A function is too long and has clear logical blocks.
- You want to extract a repeatedly‑used block into a reusable helper.
- You want to preserve behavior and tests.

**What this skill does:**

1. Reads the file and the function body around the given line range.
2. Identifies the block to extract (simple heuristic).
3. Creates a new helper function with the same inputs/outputs.
4. Replaces the original block with a call to the helper.
5. Writes a minimal test that verifies behavior before and after.
6. Runs the test and shows the diff.

**Constraints:**

- No file deletion.
- No new dependencies.
- No changes to `.env` or key‑related files.
- Behavior must not change; only structure is refactored.
