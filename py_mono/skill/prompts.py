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
# Helpers
# ---------------------------------------------------------------------------

def _escape_for_fstring(s: str) -> str:
    """Escape braces and quotes for safe insertion in f-strings"""
    if not s:
        return ""
    return s.replace("{", "{{").replace("}", "}}").replace('"', '\\"')

def _format_tool_signatures(available_tools: Dict[str, str]) -> str:
    lines = []
    for name, desc in available_tools.items():
        if "command" in desc.lower():
            example = f'{name}(command="...")'
        elif "path" in desc.lower():
            example = f'{name}(path="...")'
        else:
            example = f"{name}()"
        lines.append(f"  - {example}")
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_skill_md_prompt(
    skill_name: str,
    description: str,
    available_tools: Dict[str, str],  # tool_name → tool_description
) -> str:
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

[INSTRUCTION — replace this bracketed line with one paragraph explaining what this skill does.
Do not include this instruction, the brackets, or the word "INSTRUCTION" in your output.]

## Usage

````

/skill {skill_name}

````

## Expected Output

[INSTRUCTION — replace this bracketed line with a brief description of what the user will see.
Do not include this instruction, the brackets, or the word "INSTRUCTION" in your output.]

## Constraints

[INSTRUCTION — replace this bracketed line with 1-3 real constraints, each its own bullet point,
e.g. "- Read-only, no writes to disk." Do not include this instruction, the brackets, or the
word "INSTRUCTION" in your output.]

Rules:
- status MUST be "proposed" — never "approved"
- allowed_tools must only contain tools from the available tools list above
- Keep it concise and human-readable
- Every [INSTRUCTION — ...] bracketed line above is a placeholder for YOU to replace with real
  content — never copy an [INSTRUCTION — ...] line itself into the output
"""



def build_skill_py_prompt(
    skill_name: str,
    description: str,
    skill_md_content: str,
    available_tools: Dict[str, str],
    retry_reason: str = "",
    prev_code: str = "",
) -> str:
    tool_lines = _format_tool_signatures(available_tools)

    class_name = "".join(w.capitalize() for w in skill_name.split("-")) + "Skill"

    retry_block = ""
    if retry_reason:
        retry_reason_escaped = _escape_for_fstring(retry_reason)
        prev_code_escaped = _escape_for_fstring(prev_code)
        retry_block = f"""
IMPORTANT — YOUR PREVIOUS ATTEMPT FAILED VALIDATION:
{retry_reason_escaped}

Fix ALL issues.

Previous attempt:
{prev_code_escaped}
"""

    return f"""You are generating a skill.py file for a Python coding agent skill.

Output ONLY valid Python code.
NO markdown.
NO explanation.
NO extra text.
The file MUST start with imports.

--------------------------------
REQUIRED IMPORT BLOCK (EXACT)
--------------------------------
from py_mono.skill.base import Skill, SkillContext
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

--------------------------------
SKILL DEFINITION
--------------------------------
Skill name: {skill_name}
Class name: {class_name}
Description: {description}

The class MUST:
- Be named exactly: {class_name}
- Subclass: Skill
- Implement: name(), description(), run()

name() MUST return EXACTLY:
"{skill_name}"

--------------------------------
SKILL.md (SOURCE OF TRUTH)
--------------------------------
{skill_md_content}

--------------------------------
AVAILABLE TOOLS
--------------------------------
{tool_lines}

--------------------------------
TOOL USAGE RULES (STRICT)
--------------------------------
- ALWAYS use: context.agent_tools.get("tool_name")
- ALWAYS call: tool.run(**kwargs)
- NEVER use tool.func(...)
- NEVER pass positional args

CORRECT:
    tool.run(command="ls -la")

WRONG:
    tool.run("ls -la")
    tool.run({{"command": "ls -la"}})

--------------------------------
WORKSPACE USAGE
--------------------------------
workspace = context.workspace_root
files = list(workspace.rglob("*.py"))
content = (workspace / "file.txt").read_text()

--------------------------------
SAFETY RULES (HARD FAIL)
--------------------------------
- NO os.system
- NO subprocess
- NO exec / eval
- NO __import__
- NO network calls
- NO absolute paths outside workspace

--------------------------------
ALLOWED IMPORTS
--------------------------------
- pathlib, typing, json, re, csv
- datetime, collections, itertools, functools
- logging

--------------------------------
FORBIDDEN IMPORTS
--------------------------------
- os (except os.path)
- subprocess
- requests / httpx / urllib
- socket
- abc

--------------------------------
REQUIREMENTS
--------------------------------
- MUST catch exceptions
- MUST return string from run()
- MUST be deterministic
- MUST be concise

--------------------------------
OUTPUT FORMAT (STRICT)
--------------------------------
- Start with imports
- Then class definition
- NO extra text before or after
- NO markdown fences

--------------------------------
EXAMPLE STRUCTURE (FOLLOW THIS)
--------------------------------
class {class_name}(Skill):

    def name(self) -> str:
        return "{skill_name}"

    def description(self) -> str:
        return "{description}"

    def run(self, request: str, context: SkillContext) -> str:
        try:
            # implementation
            return "result"
        except Exception as e:
            return f"[{skill_name}] Error: {{e}}"

{retry_block}
"""