# docs\adr\ADR-018-project-scaffold-and-requirements-workflow.md
# ADR-018: Project Scaffold and Requirements-Driven Workflow

## Status

Proposed

---

## Context

The agent was originally designed around tool-based reasoning and workspace sandboxing.
It has the following tools already implemented and working:

- `read_file`, `write_file`, `edit_file` — file I/O within workspace
- `shell` — execute commands within workspace
- `list_files` — enumerate workspace contents
- `install_dependency` — install Python packages via uv
- `create_tool` — dynamically create new tools at runtime

The skills layer (ADR-010) adds approved, deterministic workflows on top of these tools.
The dual-layer architecture (ADR-015) adds playbooks for LLM reasoning guidance.

However, the primary user expectation when using a "Python coding agent" — namely, that
you can describe a program and the agent will build it — is not currently supported as a
first-class workflow.

The gap is not in tooling (write_file already exists) but in:

1. No structured way for users to express requirements
2. No playbook guiding the LLM to ask clarifying questions before writing files
3. No skill that orchestrates the full "build me a project" flow
4. No workspace context available to the agent at session start

---

## Decision

We introduce four components to enable requirements-driven project creation:

### 1. `requirements.md` convention

A file at `workspace/requirements.md` serves as the persistent requirements document.
The agent reads this at the start of each session (via `understand-workspace` skill).
The user may edit it directly or ask the agent to update it interactively.

Format:

```markdown
# Project Requirements

## Goal
One paragraph describing what this project should do.

## Inputs / Outputs
- Input: ...
- Output: ...

## Technical Constraints
- Python 3.11+
- No external APIs
- ...

## Open Questions
- [ ] Should this be a CLI or a web app?
```

### 2. `software-design` playbook

A Markdown playbook injected into the LLM context when a user asks to build something.
Guides the LLM to:
- Ask clarifying questions before writing any files
- Confirm the design with the user
- Write to `requirements.md` before scaffolding
- Use `scaffold-project` skill for file creation

Location: `playbooks/software-design/SOFTWARE-DESIGN.md`

### 3. `understand-workspace` skill

Runs on demand (or automatically at session start).
Uses existing `list_files` and `read_file` tools to:
- Enumerate workspace structure
- Read `requirements.md` if present
- Read `plan.md` if present
- Write a summary to `workspace/context.md`
- Return a human-readable summary to the user

This gives the LLM grounding before any task.

### 4. `scaffold-project` skill

Takes a requirements description (from `workspace/requirements.md` or inline input).
Uses the LLM to generate a file manifest as JSON, then writes each file using the
existing `write_file` tool.

Flow:
1. Read `workspace/requirements.md`
2. LLM generates file manifest: `[{path, content}, ...]`
3. User confirms or adjusts
4. Skill writes each file via `write_file`
5. Skill runs `pytest` via `shell` if tests were generated
6. Returns summary of files created and test results

---

## Invariants

- `scaffold-project` MUST use `write_file` tool, never write files directly
- `understand-workspace` MUST be read-only
- `software-design` playbook MUST NOT contain executable instructions
- All file writes MUST stay within `workspace/`

---

## Workflow (end-to-end)

```
User: "Build me a Flask REST API with SQLite, users + posts, basic auth"

Agent: [software-design playbook injected]
       "Before I start writing, let me ask a few things:
        1. REST or GraphQL?
        2. JWT or session-based auth?
        3. Should I include a test suite?
        4. Python 3.11+?"

User: "REST, JWT, yes tests, Python 3.11"

Agent: [writes workspace/requirements.md]
       "Here's what I'll build: [summary]
        Shall I proceed?"

User: "yes"

Agent: [structured output] → use_skill: scaffold-project
       [generates manifest, writes files, runs pytest]
       "Created 12 files. 8 tests passing."
```

---

## Relationship to Previous ADRs

- ADR-010: Skills approval model — `scaffold-project` and `understand-workspace` follow it
- ADR-015: Dual-layer architecture — `software-design` is a playbook (reasoning), skills are execution
- ADR-016: Boundary enforcement — `scaffold-project` uses `write_file` tool, not direct file access
- ADR-017: Structured orchestration — agent uses `use_skill` action to invoke `scaffold-project`

---

## Consequences

### Positive

- Closes the primary user expectation gap ("build me a program")
- Uses only existing tools — no new tool infrastructure needed
- Follows established patterns (skill + playbook + approval gate)
- `requirements.md` gives the agent persistent context across sessions
- `understand-workspace` makes every session smarter

### Negative

- LLM-generated file manifests may have errors; requires validation
- Multi-file generation is slow on local models
- `scaffold-project` needs careful prompt engineering to produce usable code

---

## Implementation Order

1. `playbooks/software-design/SOFTWARE-DESIGN.md` — pure markdown, no code risk
2. `understand-workspace` skill — read-only, low risk
3. `scaffold-project` skill — start with single-file generation, expand to multi-file

---

## Follow-ups

- Add `generate-playbook` skill (mirrors `generate-skill` pattern)
- Add `update-requirements` skill (guided requirements gathering conversation)
- Consider `workspace/context.md` as a standard output of `understand-workspace`
- ADR-019: session startup sequence (auto-run `understand-workspace` on agent init)