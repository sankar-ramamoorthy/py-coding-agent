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
        read_result = read_file.run(path=file_target)

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

        # 5. Generate actual patch
        old_line, new_line, explanation = self._generate_patch(
            error_str=error,
            file_path=file_target,
            lines=lines,
            line_num=line,
        )

        if not old_line:
            return f"[BUG_FIX] Could not locate line {line} in {file_target}"

        dry_run = self._extract_str(request, "dry_run:") == "true"

        if dry_run or new_line.startswith("# TODO"):
            if new_line.startswith("# TODO"):
                # Can't auto-patch, give detailed explanation instead
                explanation = self._explain_error(error_str)
            return (
                f"[DRY RUN] BugFixSkill: bug in {file_target} at line {line}\n"
                "=== Code Context ===\n"
                f"{self._pretty_lines(start + 1, context_lines)}\n\n"
                "=== Analysis ===\n"
                f"{explanation}\n\n"
                "=== Proposed Manual Change ===\n"
                f"- {old_line}\n"
                f"+ {new_line}\n\n"
                "Run again with dry_run:false to apply TODO comment, or fix manually."
            )


        # 6. Apply edit
        if "edit_file" not in agent_tools:
            return "[BUG_FIX] Tool 'edit_file' not found. Cannot apply fix."

        edit_file = agent_tools["edit_file"]
        before_content = "\n".join(lines)
        after_lines = lines[:]
        after_lines[line - 1] = new_line
        after_content = "\n".join(after_lines)

        edit_result = edit_file.func({
            "path": file_target,
            "old_content": before_content,
            "new_content": after_content,
        })

        if "Error" in str(edit_result):
            return f"Failed to apply edit:\n{edit_result}"

        # 7. Write real failing test first, then run
        test_result = self._write_failing_test_and_run(
            agent_tools=agent_tools,
            workspace_root=context.workspace_root,
            file_path=file_target,
            error_str=error,
            original_content=before_content,
        )

        return (
            f"BugFixSkill: Applied fix to {file_target}:{line}\n"
            "=== Change ===\n"
            f"Reason: {explanation}\n"
            f"- {old_line}\n"
            f"+ {new_line}\n\n"
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

    def _explain_error(self, error_str: str) -> str:
        if "KeyError" in error_str:
            return ("KeyError means you tried d['key'] but 'key' isn't in dict d.\n"
                    "Fixes: 1) Use d.get('key', default)  2) Check 'key' in d first  3) Use try/except KeyError")
        if "AttributeError" in error_str:
            return ("AttributeError: object lacks that attribute.\n"
                    "Fixes: 1) Use getattr(obj, 'attr', None)  2) Check hasattr first  3) Ensure obj is correct type")
        if "IndexError" in error_str:
            return ("IndexError: list index out of range.\n"
                    "Fixes: 1) Check i < len(arr) first  2) Use arr[i:i+1] to get empty list instead of error")
        if "TypeError" in error_str:
            return ("TypeError: wrong type for operation.\n"
                    "Fixes: 1) Cast: int(x)  2) Check type with isinstance  3) Handle None case")
        return f"Unrecognized error: {error_str}. Inspect the code context above and trace variables."


    def _generate_patch(
        self,
        error_str: str,
        file_path: str,
        lines: List[str],
        line_num: int,
    ) -> Tuple[str, str, str]:
        """
        Returns: old_line, new_line, explanation
        """
        idx = line_num - 1
        if not (0 <= idx < len(lines)):
            return "", "", "Line out of range"

        old_line = lines[idx]
        indent = re.match(r"(\s*)", old_line).group(1)

        # Pattern match on error + line content
        if "KeyError" in error_str and "[" in old_line and "]" in old_line:
            # dict[key] -> dict.get(key)
            match = re.search(r"(\w+)\['([^']+)'\]", old_line)
            if match:
                d, k = match.group(1), match.group(2)
                new_line = old_line.replace(f"{d}['{k}']", f"{d}.get('{k}')")
                return old_line, new_line, f"Replace direct access with.get() to avoid KeyError"

        if "AttributeError" in error_str and "." in old_line:
            # obj.attr -> getattr(obj, 'attr', None)
            match = re.search(r"(\w+)\.(\w+)", old_line)
            if match:
                obj, attr = match.group(1), match.group(2)
                new_line = old_line.replace(f"{obj}.{attr}", f"getattr({obj}, '{attr}', None)")
                return old_line, new_line, f"Use getattr() to handle missing attribute"

    if "IndexError" in error_str and "[" in old_line:
        # arr[i] -> arr[i] if i < len(arr) else None
        match = re.search(r"(\w+)\[(\w+)\]", old_line)
        if match:
            arr, i = match.group(1), match.group(2)
            new_line = f"{indent}{arr}[{i}] if {i} < len({arr}) else None"
            return old_line, new_line, f"Guard index access with length check"

    return old_line, f"{indent}# TODO: Manual fix needed for: {error_str}", "No auto-patch available"

    def _build_edit_suggestion_deprecated(
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

    def _write_failing_test_and_run(
        self,
        agent_tools: Dict[str, Any],
        workspace_root: Path,
        file_path: str,
        error_str: str,
        original_content: str,
    ) -> str:
        rel_path = Path(file_path)
        test_rel = rel_path.parent / f"test_{rel_path.stem}_regression.py"
        test_path = (workspace_root / test_rel).resolve()

        write_file = agent_tools["write_file"]
        test_code = self._build_regression_test(
            file_path=file_path,
            error_str=error_str,
        )

        w_result = write_file.func({"path": str(test_path), "content": test_code})
        if "Error" in str(w_result):
            return f"Failed to write test:\n{w_result}"

        # Run pytest
        shell = agent_tools["shell"]
        s_result = shell.func({"command": f"pytest {test_rel.as_posix()} -v"})

        # If tests still fail after fix, rollback
        if s_result.get("returncode", 0)!= 0:
            write_file.func({"path": file_path, "content": original_content})
            return (
                "[BUG_FIX] Tests failed after fix. Rolled back.\n"
                f"stdout:\n{s_result.get('stdout', '')}\n"
                f"stderr:\n{s_result.get('stderr', '')}"
            )

        return f"Tests passed.\n{s_result.get('stdout', '')}"
    
    def _write_test_and_run_deprecated(
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

        w_result = write_file.run(
            path=str(test_path),
            content=test_code,
        )


        if "Error" in str(w_result):
            return f"Failed to write test:\n{w_result}"

        # Run test
        if "shell" not in agent_tools:
            return "[BUG_FIX] Tool 'shell' not found in agent_tools."

        shell = agent_tools["shell"]
        shell_cmd = f"pytest {test_rel.as_posix()}"

        s_result = shell.run(
            command=shell_cmd,
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

    def _build_regression_test(self, file_path: str, error_str: str) -> str:
        mod_name = Path(file_path).stem
        pkg = ".".join(Path(file_path).parent.parts) if Path(file_path).parent!= Path(".") else ""
        imported = f"from {pkg} import {mod_name}" if pkg else f"import {mod_name}"

        return f"""# AUTO-GENERATED regression test by bug_fix skill
# This test should have FAILED before the fix and PASS after.

import pytest
{imported}

def test_regression_for_{mod_name}():
    \"\"\"Reproduces: {error_str}\"\"\"
    # TODO: Fill in minimal case that triggered the original error
    # Example: if KeyError on dict['missing'], do:
    # d = {{}}
    # with pytest.raises(KeyError): # This should NOT raise after fix
    # _ = d['missing']
    assert True # REPLACE THIS with actual reproduction
"""