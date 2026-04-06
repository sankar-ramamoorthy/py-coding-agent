# skills/bug_fix/skill.py

"""
Performs bug fixing from a Python error + file + line range.

Steps:
- Parse a Python error + file + line range.
- Read the file around the reported line.
- Propose a minimal fix diff.
- Write a minimal test that reproduces the failure.
- Run the test and show result.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from py_mono.skill.base import Skill, SkillContext


class BugFixSkill(Skill):
    def name(self) -> str:
        return "bug_fix"

    def description(self) -> str:
        return (
            "Fix a bug from a stack trace or error message.\n"
            "Use: /skill bug_fix <error> file:<path> [line:<num>]"
        )

    def run(self, request: str, context: SkillContext) -> str:
        # 1. Parse args
        error = self._extract_str(request, "error:")
        if not error:
            error = request

        file_target = self._extract_str(request, "file:")
        if not file_target:
            return (
                "Missing required argument.\n"
                "Usage: /skill bug_fix <error message> file:<path> [line:<num>]\n"
                "Example: /skill bug_fix 'KeyError: foo' file:src/foo.py line:42"
            )

        line = self._extract_int(request, "line:")
        if line is None:
            line = 1

        agent_tools = context.agent_tools

        # 2. Read file
        if "read_file" not in agent_tools:
            return "[BUG_FIX] Tool 'read_file' not found in agent_tools."

        read_file = agent_tools["read_file"]
        read_result = read_file.func({"path": file_target})

        if "Error" in read_result:
            return f"Failed to read {file_target}:\n{read_result}"

        content = read_result
        lines = content.splitlines()
        start = max(0, line - 5)
        end = min(len(lines), line + 5)
        context_lines = lines[start:end]

        # 3. Fix suggestion
        fix_suggestion = self._build_fix_suggestion(
            error_str=error,
            file_path=file_target,
            line_num=line,
            context_lines=context_lines,
        )

        # 4. Write test
        test_result = self._write_test_and_run(
            agent_tools=agent_tools,
            workspace_root=context.workspace_root,
            file_path=file_target,
            error_str=error,
        )

        # 5. Edit suggestion (if edit_file is present)
        edit_suggestion = self._build_edit_suggestion(
            agent_tools=agent_tools,
            file_path=file_target,
            content_lines=lines,
            line_num=line,
            error_str=error,
        )

        return (
            f"BugFixSkill: bug in {file_target} at line {line}.\n"
            "=== Code Context ===\n"
            f"{self._pretty_lines(start + 1, context_lines)}\n"
            "=== Fix Suggestion ===\n"
            f"{fix_suggestion}\n"
            "=== Edit Suggestion ===\n"
            f"{edit_suggestion.strip()}\n"
            "=== Test Outcome ===\n"
            f"{test_result.strip()}"
        )

    def _extract_str(self, text: str, key: str) -> Optional[str]:
        pattern = rf"{key}(?P<value>.*?)(?:\s+[a-z_]+:|$)"
        match = re.search(pattern, text.strip(), re.IGNORECASE)
        if match:
            val = match.group("value").strip()
            return val if val else None
        return None

    def _extract_int(self, text: str, key: str) -> Optional[int]:
        s = self._extract_str(text, key)
        if s:
            try:
                return int(s.split()[0])
            except (ValueError, IndexError):
                pass
        return None

    def _pretty_lines(self, start_line: int, lines: List[str]) -> str:
        parts = []
        for i, line in enumerate(lines, start_line):
            parts.append(f"{i:4d} | {line}")
        return "\n".join(parts)

    def _build_fix_suggestion(
        self,
        error_str: str,
        file_path: str,
        line_num: int,
        context_lines: List[str],
    ) -> str:
        if "KeyError" in error_str:
            return (
                "Detected KeyError.\n"
                "Consider:\n"
                "- Using d.get('key', default) instead of d['key'].\n"
                "- Adding a try/except KeyError.\n"
                "- Ensuring the key exists before accessing it.\n"
            )

        if "AttributeError" in error_str:
            return (
                "Detected AttributeError.\n"
                "Consider:\n"
                "- Using hasattr(obj, 'attr') or getattr(obj, 'attr', default).\n"
                "- Ensuring the object is initialized with the required attributes.\n"
            )

        if "IndexError" in error_str:
            return (
                "Detected IndexError.\n"
                "Consider:\n"
                "- Checking len(seq) before indexing.\n"
                "- Adding a range guard.\n"
            )

        return (
            "No obvious pattern detected. Please inspect the lines above.\n"
            + "\n".join(f"  {line}" for line in context_lines)
        )

    def _build_edit_suggestion(
        self,
        agent_tools: Dict[str, Any],
        file_path: str,
        content_lines: List[str],
        line_num: int,
        error_str: str,
    ) -> str:
        if "edit_file" not in agent_tools:
            return (
                "# edit_file tool not available; you must edit manually.\n"
            )

        idx = line_num - 1
        if 0 <= idx < len(content_lines):
            old_line = content_lines[idx]
        else:
            old_line = "(line out of range)"

        new_line = f"    # TODO: fix bug at line {line_num} ({error_str})"

        return (
            "edit_file suggestion (you can review and run manually):\n"
            "tool: edit_file\n"
            f"path: {file_path}\n"
            f"old_content: {old_line}\n"
            f"new_content: {new_line}\n"
        )

    def _write_test_and_run(
        self,
        agent_tools: Dict[str, Any],
        workspace_root: Path,
        file_path: str,
        error_str: str,
    ) -> str:
        rel_path = Path(file_path)
        if rel_path.suffix == ".py":
            parent = rel_path.parent
            stem = rel_path.stem
            test_rel = parent / f"test_{stem}.py"
        else:
            test_rel = Path("tests") / "test_bug_fix_stub.py"

        test_path = (workspace_root / test_rel).resolve()

        # Write test
        if "write_file" not in agent_tools:
            return "[BUG_FIX] Tool 'write_file' not found in agent_tools."

        write_file = agent_tools["write_file"]
        test_code = self._build_dummy_test(
            file_path=file_path,
            test_rel=test_rel.as_posix(),
            error_str=error_str,
        )

        w_result = write_file.func(
            {
                "path": str(test_path),
                "content": test_code,
            }
        )

        if "Error" in str(w_result):
            return f"Failed to write test:\n{w_result}"

        # Run test
        if "shell" not in agent_tools:
            return "[BUG_FIX] Tool 'shell' not found in agent_tools."

        shell = agent_tools["shell"]
        shell_cmd = f"pytest {test_rel.as_posix()}"

        s_result = shell.func(
            {
                "command": shell_cmd,
            }
        )

        return s_result.get("stdout", "") + s_result.get("stderr", "")

    def _build_dummy_test(self, file_path: str, test_rel: str, error_str: str) -> str:
        rel_module = Path(file_path).parent
        mod_name = Path(file_path).stem
        if rel_module == Path("."):
            imported = f"import {mod_name}"
        else:
            pkg = ".".join(rel_module.parts)
            imported = f"from {pkg} import {mod_name}"

        return f"""# AUTO-GENERATED test file by bug_fix skill
# The test is minimal and intended to be extended by the user.

import pytest

{imported}

def test_placeholder():
    \"\"\"Placeholder test; you must fill in real failure case.\"\"\"
    assert True  # change this to match your error
"""  # noqa
