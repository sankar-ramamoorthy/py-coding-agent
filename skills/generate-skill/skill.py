# skills/generate-skill/skill.py
"""
generate-skill — LLM-powered skill generator.

Generates a complete, working skill (SKILL.md + skill.py) from a
name and description using two LLM calls:

  Call 1: Generate SKILL.md
  Call 2: Generate skill.py (with retry on validation failure)

Validation is applied before saving. See ADR-011 and ADR-013.

Usage:
    /skill generate-skill <skill-name> | <description>

Example:
    /skill generate-skill list-python-files | List all Python files in workspace
"""

import json, re
import logging,time
from pathlib import Path
from typing import Optional

from py_mono.skill.base import Skill, SkillContext, SKILLS_DIR
from py_mono.skill.prompts import build_skill_md_prompt, build_skill_py_prompt
from py_mono.skill.validator import validate_skill_md, validate_skill_py

logger = logging.getLogger(__name__)

MAX_RETRIES = 1  # one retry on skill.py validation failure


class GenerateSkill(Skill):

    def name(self) -> str:
        return "generate-skill"

    def description(self) -> str:
        return "Generate a new skill (SKILL.md + skill.py) using the LLM"

    def run(self, request: str, context: SkillContext) -> str:
        """
        Parse request, call LLM twice, validate, save.

        Args:
            request : full command e.g. '/skill generate-skill list-python-files | description'
            context : SkillContext with session_manager and agent_tools

        Returns:
            str: human-readable result
        """
        # ------------------------------------------------------------------
        # Step 1 — Parse input
        # ------------------------------------------------------------------
        parsed = self._parse_request(request)
        if isinstance(parsed, str):
            return parsed  # error message

        skill_name, description = parsed

        # Check skill doesn't already exist
        skill_path = SKILLS_DIR / skill_name
        if skill_path.exists():
            return (
                f"❌ Skill '{skill_name}' already exists at {skill_path}.\n"
                f"Use /skill help {skill_name} to inspect it."
            )

        # Build tool map for prompts
        available_tools = self._build_tool_descriptions(context)

        # ------------------------------------------------------------------
        # Step 2 — LLM Call 1: Generate SKILL.md
        # ------------------------------------------------------------------
        print(f"🤖 Generating SKILL.md for '{skill_name}'...")
        skill_md_content = self._call_llm(
            context=context,
            prompt=build_skill_md_prompt(
                skill_name=skill_name,
                description=description,
                available_tools=available_tools,
            ),
        )
        if skill_md_content is None:
            return "❌ LLM call failed while generating SKILL.md. Try again."

        # Validate and auto-fix SKILL.md
        md_result = validate_skill_md(
            content=skill_md_content,
            skill_name=skill_name,
            known_tools=list(available_tools.keys()),
        )
        skill_md_content = md_result.fixed_content or skill_md_content

        # ------------------------------------------------------------------
        # Step 3 — LLM Call 2: Generate skill.py (with one retry)
        # ------------------------------------------------------------------
        print(f"🤖 Generating skill.py for '{skill_name}'...")
        skill_py_content, py_result, warnings = self._generate_skill_py(
            context=context,
            skill_name=skill_name,
            description=description,
            skill_md_content=skill_md_content,
            available_tools=available_tools,
        )

        # Hard fail — forbidden patterns survived retry
        if skill_py_content is None  or  py_result.structure_errors or py_result.has_syntax_errors():
            return (
                f"❌ Skill '{skill_name}' could NOT be saved.\n"
                f"After {MAX_RETRIES + 1} attempts, generated code still has forbidden patterns:\n"
                f"{py_result.failure_reason()}\n\n"
                f"Try rephrasing your description or switch to a more capable model:\n"
                f"  /provider litellm groq/qwen/qwen3-32b"
            )

        # ------------------------------------------------------------------
        # Step 4 — Save files
        # ------------------------------------------------------------------
        try:
            #skill_path.mkdir(parents=True, exist_ok=False)
            (skill_path / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
            (skill_path / "skill.py").write_text(skill_py_content, encoding="utf-8")
        except Exception as e:
            return f"❌ Failed to save skill files: {e}"

        # ------------------------------------------------------------------
        # Step 5 — Build response
        # ------------------------------------------------------------------
        return self._build_response(
            skill_name=skill_name,
            skill_path=skill_path,
            skill_py_content=skill_py_content,
            md_warnings=md_result.warnings,
            py_warnings=warnings,
            py_result=py_result,
        )

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _parse_request(self, request: str):
        """
        Parse '/skill generate-skill <name> | <description>'.
        Returns (skill_name, description) tuple or error string.
        """
        # Strip command prefix
        prefix = "/skill generate-skill"
        raw = request.strip()
        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()

        parts = raw.split("|", 1)
        if len(parts) != 2:
            return (
                "Usage: /skill generate-skill <skill-name> | <description>\n"
                "Example: /skill generate-skill list-python-files | "
                "List all Python files in the workspace with sizes"
            )

        skill_name = parts[0].strip().lower().replace(" ", "-")
        description = parts[1].strip()

        if not skill_name:
            return "❌ Skill name cannot be empty."
        if not description:
            return "❌ Description cannot be empty."

        # Validate skill name format
        import re
        if not re.match(r'^[a-z0-9][a-z0-9\-]*$', skill_name):
            return (
                f"❌ Invalid skill name '{skill_name}'. "
                "Use lowercase letters, numbers, and hyphens only."
            )

        return skill_name, description

    def _build_tool_descriptions(self, context: SkillContext) -> dict:
        """Build a dict of tool_name → description from context.agent_tools."""
        result = {}
        for name, tool in context.agent_tools.items():
            desc = getattr(tool, "description", "No description available")
            result[name] = desc
        return result

    def _call_llm_deprecated(self, context: SkillContext, prompt: str) -> Optional[str]:
        """
        Make a single LLM call via session_manager.
        Returns the text response or None on failure.
        """
        try:
            provider = context.session_manager.get_active_provider()
            messages = [
                {"role": "user", "content": prompt}
            ]
            response = provider.generate(messages=messages, tools=None)
            text = response.get("text", "")
            if not text or not text.strip():
                logger.error("LLM returned empty response")
                return None
            return text.strip()
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

    def _strip_thinking(self, text: str) -> str:
        """
        Remove <thinking>...</thinking> blocks from LLM output.
        Remove <think>...</think> blocks from LLM output.
        Handles multiline and nested cases conservatively.
        """
        # Remove full blocks
        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)

        # Remove stray opening/closing tags if model is sloppy
        #text = text.replace("<thinking>", "").replace("</thinking>", "")
        # Remove full blocks
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

        # Remove stray opening/closing tags if model is sloppy
        #text = text.replace("<think>", "").replace("</think>", "")

        return text.strip()

    def _call_llm(self, context: SkillContext, prompt: str) -> Optional[str]:
        from py_mono.skill.validator import _strip_markdown_fences        
        try:
            provider = context.session_manager.get_active_provider()
            messages = [{"role": "user", "content": prompt}]
            response = provider.generate(messages=messages, tools=None)

            text = response.get("text", "")
            if not text or not text.strip():
                logger.error("LLM returned empty response")
                return None

            text = text.strip()

            # 🔥 Strip <thinking> tags immediately
            text = self._strip_thinking(text)
            text = _strip_markdown_fences(text)            
            logger.error(f"llm text stripped{text}")
            print(text)

            return text

        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None
    
    def _generate_skill_py(
        self,
        context: SkillContext,
        skill_name: str,
        description: str,
        skill_md_content: str,
        available_tools: dict,
    ):
        """
        Generate and validate skill.py with one retry on failure.

        Returns:
            (code, result, warnings) where:
                code     = valid code string, or None on hard fail
                result   = SkillPyValidationResult
                warnings = list of non-fatal warning strings
        """
        from py_mono.skill.validator import SkillPyValidationResult

        retry_reason = ""
        warnings = []

        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                print(f"🔄 Retrying skill.py generation (attempt {attempt + 1})...")

            code = self._call_llm(
                context=context,
                prompt=build_skill_py_prompt(
                    skill_name=skill_name,
                    description=description,
                    skill_md_content=skill_md_content,
                    available_tools=available_tools,
                    retry_reason=retry_reason,
                ),
            )

            # ALWAYS persist raw LLM output for debugging
            debug_dir = (SKILLS_DIR / skill_name)
            debug_dir.mkdir(parents=True, exist_ok=True)

            timestamp = int(time.time())
            debug_path = debug_dir / f"skill_debug_{timestamp}.txt"

            if code:
                debug_path.write_text(code, encoding="utf-8")
            else:
                debug_path.write_text("[EMPTY RESPONSE FROM LLM]", encoding="utf-8")

            logger.debug(f"Saved debug LLM output to {debug_path}")


            if code is None:
                return None, SkillPyValidationResult(
                    valid=False,
                    syntax_errors=["LLM returned empty response"]
                ), warnings

            logger.debug(f"LLM returned code (length={len(code)})")

            if code is not None:
                code = self._normalize_code(code) 
                timestamp = int(time.time())
                debug_path = debug_dir / f"skill_debug_{timestamp}.txt"
            

            result = validate_skill_py(code=code, skill_name=skill_name)
            if result.valid:
                code = self._normalize_code(code)
                return code, result, warnings

            # Forbidden patterns — retry if first attempt, hard fail if retry
            if result.has_forbidden():
                if attempt < MAX_RETRIES:
                    retry_reason = result.failure_reason()
                    continue
                else:
                    # Hard fail after retry
                    return code, result, warnings

            # Non-forbidden failures (syntax, structure) — save with warning
            if result.has_syntax_errors() and attempt < MAX_RETRIES:
                retry_reason = result.failure_reason()
                continue

            # After retry or non-critical failures — save with warnings
            warnings.extend(result.syntax_errors)
            warnings.extend(result.structure_errors)

            if result.structure_errors or result.has_syntax_errors():
                if attempt < MAX_RETRIES:
                    retry_reason = result.failure_reason()
                    continue
                else:
                    return code, result, warnings
    
        # Should not reach here
        return None, SkillPyValidationResult(valid=False), warnings
    def _normalize_code(self, code: str) -> str:
        from py_mono.skill.validator import _strip_markdown_fences

        code = self._strip_thinking(code)
        code = _strip_markdown_fences(code)
        return code.strip()
    

    def _build_response(
        self,
        skill_name: str,
        skill_path: Path,
        skill_py_content: str,
        md_warnings: list,
        py_warnings: list,
        py_result,
    ) -> str:
        """Build the final user-facing response message."""
        lines = []

        all_warnings = md_warnings + py_warnings
        if all_warnings:
            lines.append(f"⚠️  Skill '{skill_name}' saved with warnings:")
            for w in all_warnings:
                lines.append(f"   - {w}")
            lines.append("")
        else:
            lines.append(f"✅ Skill '{skill_name}' generated successfully.")
            lines.append("")

        lines.append(f"Status: proposed — not yet executable.")
        lines.append(f"Location: {skill_path}")
        lines.append("")
        lines.append("Next steps:")
        lines.append(f"  1. Review:  /skill help {skill_name}")
        lines.append(f"  2. Approve: /approve {skill_name}")
        lines.append(f"  3. Run:     /skill {skill_name}")
        lines.append("")

        # Preview first 8 lines of skill.py
        preview_lines = skill_py_content.splitlines()[:8]
        lines.append("Preview of generated skill.py:")
        lines.append("  " + "\n  ".join(preview_lines))

        return "\n".join(lines)