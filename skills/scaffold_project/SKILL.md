---
name: scaffold_project
description: Create multi-file Python project from workspace/requirements.md. Enforces requirements.md gate per ADR-018.
allowed_tools: [write_file, shell, read_file,list_file]
status: approved
constraints:
    - Must read workspace/requirements.md first
    - Fail if requirements.md missing
    - Use only tool.run(**kwargs), never os.system or subprocess
---

# scaffold-project skill

Creates project structure based on `workspace/requirements.md`.

## Behavior

1. Check `workspace/requirements.md` exists. If not: return "Missing requirements.md. Run software-design workflow first." and stop.
2. Parse requirements.md for: Files, Dependencies, Tests
3. Create files using write_file tool
4. Run `uv add` for dependencies via shell tool
5. If tests requested, create tests/ and run pytest
6. Return summary of created files

## Safety

Uses only approved tools via SafeAgentTools. No direct filesystem or subprocess access.