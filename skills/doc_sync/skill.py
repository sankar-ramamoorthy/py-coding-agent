"""
doc_sync — Synchronize documentation with code using AST + LLM.

Given: code file + docs file + target scope.
Output: updated docstrings/README + diff. Dry-run supported.

ADR-016 compliant: uses read_file, write_file, edit_file only.
"""

import ast
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from py_mono.skill.base import Skill, SkillContext

logger = logging.getLogger(__name__)

class DocSyncSkill(Skill):
    def name(self) -> str:
        return "doc_sync"

    def description(self) -> str:
        return "Synchronize docstrings and README sections with current code signatures"

    def run(self, request: str, context: SkillContext) -> str:
        # 1. Parse args
        code_path = self._extract_str(request, "code:")
        docs_path = self._extract_str(request, "docs:")
        if not code_path or not docs_path:
            return (
                "Missing required arguments.\n"
                "Usage: /skill doc_sync code:<path> docs:<path> [target:<function|class|module|readme>] [dry_run:<true|false>]\n"
                "Example: /skill doc_sync code:src/auth.py docs:src/auth.py target:module dry_run:true"
            )

        target = self._extract_str(request, "target:") or "module"
        dry_run = self._extract_str(request, "dry_run:") == "true"

        agent_tools = context.agent_tools

        # 2. Read code + extract AST metadata
        read_file = agent_tools.get("read_file")
        if not read_file:
            return "[DOC_SYNC] Tool 'read_file' not found."

        code_content = read_file.func({"path": code_path})
        if "Error" in code_content:
            return f"Failed to read code {code_path}:\n{code_content}"

        code_meta = self._extract_code_metadata(code_content, target)
        if not code_meta:
            return f"[DOC_SYNC] No {target} found in {code_path}"

        # 3. Read docs
        docs_content = read_file.func({"path": docs_path})
        docs_existed = "Error" not in docs_content
        if not docs_existed:
            docs_content = "" # New file

        # 4. Generate updated docs via LLM
        updated_docs = self._call_llm_for_sync(
            context=context,
            code_meta=code_meta,
            docs_content=docs_content,
            target=target,
            docs_path=docs_path,
        )
        if not updated_docs:
            return "❌ LLM failed to generate updated docs."

        # 5. Diff
        if updated_docs == docs_content:
            return "[DOC_SYNC] No changes needed. Docs already in sync."

        diff = self._pretty_diff(docs_content, updated_docs, docs_path)

        if dry_run:
            return (
                f"[DRY RUN] doc_sync for {code_path} -> {docs_path}\n\n"
                "=== Diff Preview ===\n"
                f"{diff}\n\n"
                "Run again with dry_run:false to apply."
            )

        # 6. Write/edit
        if docs_existed and "edit_file" in agent_tools:
            result = agent_tools["edit_file"].func({
                "path": docs_path,
                "old_content": docs_content,
                "new_content": updated_docs,
            })
        elif "write_file" in agent_tools:
            result = agent_tools["write_file"].func({
                "path": docs_path,
                "content": updated_docs,
            })
        else:
            return "[DOC_SYNC] No write_file or edit_file tool available."

        if "Error" in str(result):
            return f"Failed to write docs:\n{result}"

        return (
            f"✅ doc_sync applied to {docs_path}\n"
            f"Target: {target} from {code_path}\n\n"
            "=== Changes ===\n"
            f"{diff}"
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_str(self, text: str, key: str) -> Optional[str]:
        pattern = rf"{key}(?P<value>.*?)(?:\s+\w+:|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group("value").strip() if match else None

    def _extract_code_metadata(self, code: str, target: str) -> Dict[str, Any]:
        """Use AST to pull functions/classes/params from code."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {}

        meta = {"functions": [], "classes": []}

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and target in ("function", "module"):
                args = [a.arg for a in node.args.args]
                returns = ast.unparse(node.returns) if node.returns else "None"
                docstring = ast.get_docstring(node) or ""
                meta["functions"].append({
                    "name": node.name,
                    "args": args,
                    "returns": returns,
                    "docstring": docstring,
                    "lineno": node.lineno,
                })
            if isinstance(node, ast.ClassDef) and target in ("class", "module"):
                docstring = ast.get_docstring(node) or ""
                meta["classes"].append({
                    "name": node.name,
                    "docstring": docstring,
                    "lineno": node.lineno,
                })

        return meta if (meta["functions"] or meta["classes"]) else {}

    def _call_llm_for_sync(
        self,
        context: SkillContext,
        code_meta: Dict[str, Any],
        docs_content: str,
        target: str,
        docs_path: str,
    ) -> Optional[str]:
        provider = context.session_manager.get_active_provider()

        is_readme = "readme" in docs_path.lower() or target == "readme"
        code_summary = self._summarize_meta(code_meta)

        if is_readme:
            prompt = f"""Update this README to match the current code API. Minimal diff only.

Current Code API:
{code_summary}

Existing README:
{docs_content}

Rules:
1. Update function signatures, param lists, examples to match code
2. Keep existing sections/headers. Don't rewrite whole file.
3. Use Markdown. No explanations, only the updated file content.
"""
        else:
            prompt = f"""Update docstrings in this Python file to match actual code. PEP-257 format.

Current Code:
{code_summary}

Existing File:
{docs_content}

Rules:
1. For each function/class, ensure docstring lists all params with types
2. Add Returns section if function returns non-None
3. Keep existing description text, only fix params/returns
4. Minimal edits. Preserve indentation.
5. Output the complete updated file content.
"""

        try:
            response = provider.generate(
                messages=[{"role": "user", "content": prompt}],
                tools=None,
            )
            return response.get("text", "").strip() or None
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _summarize_meta(self, meta: Dict[str, Any]) -> str:
        lines = []
        for fn in meta["functions"]:
            args = ", ".join(fn["args"])
            lines.append(f"def {fn['name']}({args}) -> {fn['returns']}")
        for cls in meta["classes"]:
            lines.append(f"class {cls['name']}:")
        return "\n".join(lines)

    def _pretty_diff(self, before: str, after: str, path: str) -> str:
        before_lines = before.splitlines()
        after_lines = after.splitlines()
        parts = [f"--- {path}", f"+++ {path}"]

        i = j = 0
        while i < len(before_lines) or j < len(after_lines):
            if i < len(before_lines) and j < len(after_lines) and before_lines[i] == after_lines[j]:
                i += 1
                j += 1
            else:
                if i < len(before_lines):
                    parts.append(f"- {before_lines[i]}")
                    i += 1
                if j < len(after_lines):
                    parts.append(f"+ {after_lines[j]}")
                    j += 1

        if len(parts) > 52: # 2 header + 50 diff lines
            return "\n".join(parts[:52]) + "\n... [diff truncated]"
        return "\n".join(parts)