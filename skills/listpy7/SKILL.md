---
name: listpy7
description: list all python programs in "."
status: approved
allowed_tools: [shell]
constraints: [read-only, workspace only, no network]
---

# listpy7

Lists all Python source files (`.py`) in the current workspace directory using shell command filtering.

## Usage

```
/skill listpy7
```

## Expected Output

A newline-separated list of `.py` file paths in the current directory and subdirectories.

## Constraints

- Requires shell command execution 
- Only shows files with `.py` extension
- Limited to the current workspace scope