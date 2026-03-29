
# skills/doc_sync/skill.py

"""
Skill to synchronize documentation with code.

Given: code file + docs file + update strategy.

Output: updated docstring or markdown + diff.
"""

from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

from py_mono.skill.base import Skill, SkillContext


class DocSyncSkill(Skill):
    def name(self) -> str:
        return "doc_sync"

    def description(self) -> str:
        return (
            "Synchronize documentation with code.\n"
            "Use: /skill doc_sync code:<path> docs:<path> [update_method:inplace|docstring]"
        )

    def run(self, request: str, context: SkillContext) -> str:
        # 1. Parse args
        code_target = self._extract_str(request, "code:")
        docs_target = self._extract_str(request, "docs:")
        if not code_target or not docs_target:
            return (
                "Missing required arguments.\n"
                "Usage: /skill doc_sync code:<path> docs:<path> [update_method:<inplace|docstring>]"
            )

        update_method = self._extract_str(request, "update_method:")
        if not update_method:
            update_method = "inplace"

        agent_tools = context.agent_tools

        # 2. Read code
        if "read_file" not in agent_tools:
            return "[DOC_SYNC] Tool 'read_file' not found in agent_tools."

        code_result = agent_tools["read_file"].func({"path": code_target})
        if "Error" in code_result:
            return f"Failed to read code {code_target}:\n{code_result}"

        code_content = code_result

        # 3. Read docs
        docs_result = agent_tools["read_file"].func({"path": docs_target})
        if "Error" in docs_result:
            return f"Failed to read docs {docs_target}:\n{docs_result}"

        docs_content = docs_result

        # 4. (In a real version, here you’d use LLM / AST to)
        #    - parse the code structure,
        #    - align parameter names, return types, and examples
        #    - rewrite the docs or docstrings accordingly.

        # For now, just show a diff and a suggestion to manual edit.
        # In a real agent, you’d generate:
        #   - updated_docs = ...
        #   - updated_docstrings = ...

        # 5. Example: write back updated docs if edit_file is available
        # TODO: insert real sync logic here.
        msg = (
            "doc_sync is a placeholder implementation.\n"
            f"Code file: {code_target}\n"
            f"Doc file: {docs_target}\n"
            f"Update strategy: {update_method}\n\n"
            "You can now plug in AST parsing or LLM-driven doc-update logic here.\n"
        )

        # Example of how to write back:
        # if "write_file" in agent_tools:
        #     result = agent_tools["write_file"].func(
        #         {"path": docs_target, "content": updated_docs}
        #     )
        #     msg += f"Write result: {result}\n"
        #
        # or if "edit_file" in agent_tools:
        #     result = agent_tools["edit_file"].func(
        #         {"path": docs_target, "old_content": docs_content, "new_content": updated_docs}
        #     )
        #     msg += f"Edit result: {result}\n"

        return msg + "\n(Doc-sync logic can be filled in based on your AST/LLM pattern.)"
