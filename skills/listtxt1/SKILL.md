---
name: listtxt1
description: list all .txt files in directory specifid by user. skill shpuld take in oneoptional directory name parameter. defaulting t current directory. add print debug lines for tracing
status: approved
allowed_tools:
  - shell
  - list_files
constraints: read-only, workspace only
---

# listtxt1

Lists every .txt file in the directory you name (or the current directory if you skip the argument) and prints simple debug messages so you can trace what it’s doing.

## Usage

````

/skill listtxt1

````

## Expected Output

A line-by-line list of .txt filenames found in the chosen directory, preceded/followed by short debug prints showing the directory that was scanned.

## Constraints

- read-only, workspace only
- no network access
- only lists files, does not open or modify them