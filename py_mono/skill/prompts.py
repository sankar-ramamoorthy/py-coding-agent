# py_mono/skill/prompts.py
"""
LLM prompt builders for skill generation.

Used by generate-skill to produce SKILL.md and skill.py via LLM calls.

Two prompts:
    build_skill_md_prompt()  — generates SKILL.md content
    build_skill_py_prompt()  — generates skill.py content

See ADR-011 for design details.
"""

from typing import Dict, Any


# ---------------------------------------------------------------------------
# Example skill — injected into skill.py prompt as a reference implementation
# ---------------------------------------------------------------------------

EXAMPLE_SKILL = '''from py_mono.skill.base import Skill, SkillContext

class ListFilesSkill(Skill):

    def name(self) -> str:
        return "list-files-example"

    def description(self) -> str:
        return "List all files in the workspace"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            workspace = context.workspace_root
            files = sorted(workspace.rglob("*"))
            if not files:
                return "No files found in workspace."
            lines = [f"Files in {workspace}:\\n"]
            for f in files:
                if f.is_file():
                    rel = f.relative_to(workspace)
                    lines.append(f"  {rel}")
            lines.append(f"\\nTotal: {len([f for f in files if f.is_file()])} file(s)")
            return "\\n".join(lines)
        except Exception as e:
            return f"[list-files-example] Error: {e}"
'''


# ---------------------------------------------------------------------------
# Skill base class signature — injected into skill.py prompt
# ---------------------------------------------------------------------------

SKILL_BASE_SIGNATURE = '''from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict

class SkillContext:
    workspace_root: Path          # sandboxed workspace — use for all file ops
    agent_tools: Dict[str, Any]   # tool_name → Tool (call via tool.func(**args))
    session_manager: Any          # active LLM provider session

class Skill(ABC):
    @abstractmethod
    def name(self) -> str:
        """Return the unique skill name matching the folder name."""
        ...

    @abstractmethod
    def description(self) -> str:
        """Return a one-line description."""
        ...

    @abstractmethod
    def run(self, request: str, context: SkillContext) -> str:
        """Execute the skill. Always return a string."""
        ...
'''


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------
def _format_tool_signatures(available_tools: Dict[str, str]) -> str:
    lines = []
    for name, desc in available_tools.items():
        # naive inference (good enough for now)
        if "list" in desc.lower():
            returns = "list"
        else:
            returns = "string"

        # basic param inference (you can improve later)
        if "command" in desc.lower():
            params = "command: string"
        elif "path" in desc.lower():
            params = "path: string"
        else:
            params = ""

        signature = f"{name}({params}) -> {returns}" if params else f"{name}() -> {returns}"
        lines.append(f"  - {signature}")

    return "\n".join(lines)

def build_skill_md_prompt(
    skill_name: str,
    description: str,
    available_tools: Dict[str, str],  # tool_name → tool_description
) -> str:
    """
    Build the prompt for generating SKILL.md content.

    Args:
        skill_name       : the skill folder name (e.g. 'list-python-files')
        description      : user-provided description
        available_tools  : dict of tool_name → description

    Returns:
        str: full prompt text
    """
    tool_lines = "\n".join(
        f"  - {name}: {desc}" for name, desc in available_tools.items()
    )

    return f"""You are generating a SKILL.md file for a Python coding agent skill.

Output ONLY the raw SKILL.md content.
Do NOT include markdown code fences (no ``` or ```python).
Do NOT include any explanation or preamble.

Skill name: {skill_name}
Description: {description}

Available tools the skill may use:
{tool_lines}

Generate a SKILL.md using EXACTLY this format:

---
name: {skill_name}
description: {description}
status: proposed
allowed_tools: [comma-separated list of tools this skill needs, from the available tools above]
constraints: [brief human-readable constraints, e.g. "read-only, workspace only, no network"]
---

# {skill_name}

One paragraph explaining what this skill does.

## Usage

```
/skill {skill_name}
```

## Expected Output

Brief description of what the user will see.

## Constraints

- List each constraint as a bullet point.

Rules:
- status MUST be "proposed" — never "approved"
- allowed_tools must only contain tools from the available tools list above
- Keep it concise and human-readable
"""


def build_skill_py_prompt(
    skill_name: str,
    description: str,
    skill_md_content: str,
    available_tools: Dict[str, str],
    retry_reason: str = "",
) -> str:
    """
    Build the prompt for generating skill.py content.

    Args:
        skill_name       : the skill folder name (e.g. 'list-python-files')
        description      : user-provided description
        skill_md_content : the generated SKILL.md (so LLM knows allowed_tools)
        available_tools  : dict of tool_name → description
        retry_reason     : if non-empty, previous attempt failed — include reason

    Returns:
        str: full prompt text
    """
    tool_lines = _format_tool_signatures(available_tools)

    retry_block = ""
    if retry_reason:
        retry_block = f"""
IMPORTANT — YOUR PREVIOUS ATTEMPT FAILED VALIDATION:
{retry_reason}

Fix ALL of these issues in your new attempt.
"""

    return f"""You are generating a skill.py file for a Python coding agent skill.

Output ONLY valid Python code.
Do NOT include markdown code fences (no ``` or ```python.).
Do NOT include any explanation or preamble.
Do NOT include any text before or after the Python code.
Python code should start with import and end with return.
{retry_block}
Skill name: {skill_name}
Description: {description}

SKILL.md (defines what this skill is allowed to do):
{skill_md_content}

BASE CLASS SIGNATURES (you must subclass Skill exactly):
{SKILL_BASE_SIGNATURE}

AVAILABLE TOOLS (retrieve via context.agent_tools, execute via tool.run(...))::

{tool_lines}

IMPORTANT:
- ALWAYS retrieve tools using context.agent_tools.get(...)
- ALWAYS execute tools using tool.run(...)
- NEVER use tool.func(...)

HOW TO CALL A TOOL:
    tool = context.agent_tools.get("shell")
    if not tool:
        return "Error: shell tool not available"

    result = tool.run({{ "command": "ls -la" }})

HOW TO USE WORKSPACE:
    workspace = context.workspace_root  # Path object
    files = list(workspace.rglob("*.py"))
    content = (workspace / "myfile.txt").read_text()

SAFETY RULES — violations will cause HARD FAIL:
- NEVER use os.system()
- NEVER use subprocess directly (use shell tool via context.agent_tools)
- NEVER use exec() or eval()
- NEVER use __import__()
- NEVER open files with absolute paths outside workspace
- NEVER make network calls directly (use MCP tools if available)
- ALWAYS catch exceptions and return error strings
- ALWAYS return a string from run()

ALLOWED IMPORTS:
- py_mono.skill.base (Skill, SkillContext)
- pathlib, typing, json, re, csv, os.path (read-only)
- datetime, collections, itertools, functools
- Any tool from context.agent_tools

FORBIDDEN IMPORTS:
- os (except os.path)
- subprocess
- requests, httpx, urllib (no direct network)
- socket

WORKING EXAMPLE SKILL (follow this pattern):
{EXAMPLE_SKILL}

Now generate skill.py for skill named '{skill_name}'.
Description: {description}
The class name should be: {''.join(w.capitalize() for w in skill_name.split('-'))}Skill
The name() method must return exactly: "{skill_name}"

CRITICAL:
Your response will be parsed programmatically.
Do NOT include <thinking> <think> or any hidden reasoning.
Any output outside the requested format will be discarded.
MUST import py_mono.skill.base (Skill, SkillContext)
Do NOT wrap your response in ``` or ```python.
Your output must be raw Python code only.
If you include code fences, your output will be rejected.
"""