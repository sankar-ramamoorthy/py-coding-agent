---
name: generate_playbook
description: Generate a new reasoning playbook (Markdown) using the LLM
status: approved
allowed_tools:
  - list_files
  - read_file
  - write_file
  - edit_file
constraints: write-only, playbooks directory only, no code execution
---

# generate_playbook

Creates a Markdown playbook that guides reasoning (not execution).

## Usage

/skill generate_playbook <category> | <description>

Example:
/skill generate_playbook testing | Guide for writing pytest test suites

## Expected Output

A new Markdown file under playbooks/<category>/ with structured guidance.

## Constraints

- Must not generate executable code
- Must write only inside playbooks/
- Output must be valid Markdown