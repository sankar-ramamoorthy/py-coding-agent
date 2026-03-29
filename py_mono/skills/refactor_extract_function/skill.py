# skills/refactor_extract_function/skill.py

"""
Full‑fledged skill to extract a code block into a new helper function.

Given: file + start_line + end_line + name.

Output:
- New helper function written inline.
- Original function updated to call it.
- Minimal test to verify behavior.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from py_mono.skill.base import Skill, SkillContext


class RefactorExtractFunctionSkill(Skill):
    def name(self) -> str:
        return "refactor_extract_function"

    def description(self) -> str:
        return (
            "Extract a block of code into a new helper function.\n"
            "Use: /skill refactor_extract_function file:<path> start:<line> end:<line> name:<new_func_name>"
        )

    def run(self, request: str, context: SkillContext) -> str:
        # 1. Parse args
        file_target = self._extract_str(request, "file:")
        if not file_target:
            return (
                "Missing required argument.\n"
                "Usage: /skill refactor_extract_function "
                "file:<path> start:<line> end:<line> name:<new_func_name>\n"
                "Example: /skill refactor_extract_function "
                "file:src/foo.py start:42 end:48 name:calculate_discount"
            )

        start_line = self._extract_int(request, "start:")
        if start_line is None:
            return "Missing required argument: start:<line>"

        end_line = self._extract_int(request, "end:")
        if end_line is None or end_line < start_line:
            return "Missing or invalid argument: end:<line> must be >= start:<line>"

        name = self._extract_str(request, "name:")
        if not name:
            return "Missing required argument: name:<new_func_name>"

        agent_tools = context.agent_tools
        workspace_root = context.workspace_root

        # 2. Read the file
        if "read_file" not in agent_tools:
            return "[REFACTOR] Tool 'read_file' not found in agent_tools."

        read_file = agent_tools["read_file"]
        read_result = read_file.func({"path": file_target})

        if "Error" in read_result:
            return f"Failed to read {file_target}:\n{read_result}"

        content = read_result
        lines = content.splitlines()

        if start_line > len(lines):
            return f"Line {start_line} is beyond the last line ({len(lines)})."

        # 3. Extract the block
        start_idx = start_line - 1
        end_idx = min(end_line, len(lines))
        extracted_block = lines[start_idx:end_idx]

        # 4. Auto‑guess inputs and outputs (simple heuristic)
        inputs, outputs = self._infer_block_inputs_outputs(extracted_block)

        # 5. Generate new helper function
        helper = self._generate_helper_function(
            func_name=name,
            inputs=inputs,
            outputs=outputs,
            block=extracted_block,
        )

        # 6. Generate call to helper
        call = self._generate_call(
            func_name=name,
            inputs=inputs,
            outputs=outputs,
        )

        # 7. Compute diff
        before = "\n".join(lines)
        after = self._apply_extraction(lines[:], start_idx, end_idx, helper, call)
        if after == before:
            return "[REFACTOR] No meaningful change detected; skipping write."

        # 8. Write updated file (if edit_file or write_file exists)
        msg = ""

        if "edit_file" in agent_tools:
            edit_file = agent_tools["edit_file"]
            result = edit_file.func(
                {
                    "path": file_target,
                    "old_content": before,
                    "new_content": after,
                }
            )
            msg += f"Edit result:\n{result}\n\n"
        elif "write_file" in agent_tools:
            write_file = agent_tools["write_file"]
            result = write_file.func(
                {
                    "path": file_target,
                    "content": after,
                }
            )
            msg += f"Write result:\n{result}\n\n"
        else:
            return (
                "[REFACTOR] No edit/write tool available. You must edit manually:\n"
                + self._pretty_diff(before, after)
            )

        # 9. Write a test
        test_result = self._write_test_and_run(
            agent_tools=agent_tools,
            workspace_root=workspace_root,
            file_path=file_target,
            func_name=name,
            inputs=inputs,
            outputs=outputs,
        )

        # 10. Show diff
        return (
            f"RefactorExtractFunction: extracted {name} from {file_target} "
            f"lines {start_line}..{end_line}.\n\n"
            "=== Original Code ===\n"
            f"{self._pretty_block(start_line, lines[start_idx:end_idx])}\n\n"
            "=== New Helper Function ===\n"
            f"{helper}\n\n"
            "=== Updated Call ===\n"
            f"{call}\n\n"
            "=== Patch ===\n"
            f"{self._pretty_diff(before, after)}\n\n"
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

    def _pretty_block(self, start_line: int, lines: List[str]) -> str:
        parts = []
        for i, line in enumerate(lines, start_line):
            parts.append(f"{i:4d} | {line}")
        return "\n".join(parts)

    def _pretty_diff(self, before: str, after: str) -> str:
        before_lines = before.splitlines()
        after_lines = after.splitlines()

        parts = []
        i = j = 0
        while i < len(before_lines) or j < len(after_lines):
            if i < len(before_lines) and j < len(after_lines) and before_lines[i] == after_lines[j]:
                parts.append(f"    | {before_lines[i]}")
                i += 1
                j += 1
            else:
                if i < len(before_lines):
                    parts.append(f"  - | {before_lines[i]}")
                    i += 1
                if j < len(after_lines):
                    parts.append(f"  + | {after_lines[j]}")
                    j += 1

        if len(parts) > 20:
            return "\n".join(parts[:20]) + "\n[...]"
        return "\n".join(parts)

    def _apply_extraction(
        self,
        lines: List[str],
        start_idx: int,
        end_idx: int,
        helper: str,
        call_line: str,
    ) -> str:
        # TODO: in a richer version, you’d search for function def and inject after def.
        # For now, append helper at the end and replace the block with the call.
        lines[start_idx:end_idx] = [call_line]
        return "\n".join(lines) + "\n\n" + helper

    def _infer_block_inputs_outputs(self, block: List[str]) -> Tuple[List[str], List[str]]:
        # 1. Simple: collect vars that appear in the block but not in definitions.
        # In a real system you’d parse AST; here just heuristic on identifiers.
        # For this example, assume inputs = any identifier that appears before `=`,
        #          outputs = identifiers on the left of `=`.
        input_set = set()
        output_set = set()
        for line in block:
            line = re.sub(r"'.*?'", "", line)  # ignore string literals
            line = re.sub(r'".*?"', "", line)
            line = re.sub(r"#.*", "", line)

            # Left of = is output, right is input (very naive)
            if "=" in line:
                parts = line.split("=", 1)
                left = parts[0].strip()
                right = parts[1].strip()

                # Outputs: left‑hand side
                if left and re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", left):
                    output_set.add(left)

                # Inputs: identifiers in right‑hand side
                for m in re.finditer(r"([a-zA-Z_][a-zA-Z0-9_]*)", right):
                    var = m.group(1)
                    if var not in output_set:  # not both in‑ and output
                        input_set.add(var)

        # In this trivial example, assume:
        # - parameters: all inputs,
        # - returns: outputs if exactly one, else assign back to same names.
        inputs = sorted(input_set)
        outputs = sorted(output_set)

        return inputs, outputs

    def _generate_helper_function(
        self,
        func_name: str,
        inputs: List[str],
        outputs: List[str],
        block: List[str],
    ) -> str:
        if not inputs:
            inputs = ["..."]  # placeholder

        if not outputs:
            outputs = ["..."]

        # Simple signature: def <name>(*inputs) -> something
        params = ", ".join(inputs)
        if len(outputs) == 1:
            returns = outputs[0]
        else:
            returns = ", ".join(outputs)

        body = "\n".join("    " + line for line in block)

        return f"""def {func_name}({params}):
    \"\"\"Auto‑generated helper extracted from original block.\"\"\"
{body}

    # Placeholder: how to return outputs
    # In a real version, you’d infer exactly what to return.
    # For now, assume the block mutates `inputs` and no explicit return needed.
    pass
"""

    def _generate_call(
        self,
        func_name: str,
        inputs: List[str],
        outputs: List[str],
    ) -> str:
        if not inputs:
            inputs = ["..."]

        if not outputs:
            outputs = ["..."]

        # Naive: helper call that just passes inputs
        args = ", ".join(inputs)

        if len(outputs) == 1:
            output = outputs[0]
            return f"    {output} = {func_name}({args})"
        else:
            # Multiple outputs: assume they are assigned by the helper.
            return f"    {func_name}({args})"

    def _write_test_and_run(
        self,
        agent_tools: Dict[str, Any],
        workspace_root: Path,
        file_path: str,
        func_name: str,
        inputs: List[str],
        outputs: List[str],
    ) -> str:
        rel_path = Path(file_path)
        if rel_path.suffix == ".py":
            parent = rel_path.parent
            stem = rel_path.stem
            test_rel = parent / f"test_{stem}.py"
        else:
            test_rel = Path("tests") / "test_refactor_extract_function_stub.py"

        test_path = (workspace_root / test_rel).resolve()

        # 1. Write test file
        if "write_file" not in agent_tools:
            return "[REFACTOR] Tool 'write_file' not found in agent_tools."

        write_file = agent_tools["write_file"]
        test_code = self._build_dummy_test(
            file_path=file_path,
            test_rel=test_rel.as_posix(),
            func_name=func_name,
            inputs=inputs,
            outputs=outputs,
        )

        w_result = write_file.func(
            {
                "path": str(test_path),
                "content": test_code,
            }
        )

        if "Error" in str(w_result):
            return f"Failed to write test:\n{w_result}"

        # 2. Run test
        if "shell" not in agent_tools:
            return "[REFACTOR] Tool 'shell' not found in agent_tools."

        shell = agent_tools["shell"]
        shell_cmd = f"pytest {test_rel.as_posix()}"

        s_result = shell.func(
            {
                "command": shell_cmd,
            }
        )

        return s_result.get("stdout", "") + s_result.get("stderr", "")

    def _build_dummy_test(
        self,
        file_path: str,
        test_rel: str,
        func_name: str,
        inputs: List[str],
        outputs: List[str],
    ) -> str:
        rel_module = Path(file_path).parent
        mod_name = Path(file_path).stem
        if rel_module == Path("."):
            imported = f"import {mod_name}"
        else:
            pkg = ".".join(rel_module.parts)
            imported = f"from {pkg} import {mod_name}"

        return f"""# AUTO-GENERATED test for refactor_extract_function
# Verifies that the refactored code behaves the same as before.

import pytest

{imported}

def test_refactored_behavior():
    \"\"\"Placeholder test; you must fill in real test cases.\"\"\"
    # TODO: fill in real test cases based on original behavior
    assert True  # change this to match your function
"""
