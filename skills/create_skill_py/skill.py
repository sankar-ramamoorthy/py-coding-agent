# 🐍 `skills/create_skill_py/skill.py`

from py_mono.skill.base import Skill, SkillContext, SKILLS_DIR
from py_mono.skill.validator import validate_skill_py, _strip_markdown_fences

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


class CreateSkillPy(Skill):

    def name(self) -> str:
        return "create_skill_py"

    def description(self) -> str:
        return "Generate a skill.py from an existing SKILL.md"

    # ------------------------------------------------------------------
    # Entry
    # ------------------------------------------------------------------
    def run(self, request: str, context: SkillContext) -> str:
        parsed = self._parse_request(request)
        if isinstance(parsed, str):
            return parsed

        skill_name, overwrite, force_llm, dry_run = parsed

        skill_path = (SKILLS_DIR / skill_name).resolve()
        if not str(skill_path).startswith(str(SKILLS_DIR.resolve())):
            return f"❌ Invalid skill path. Must be under {SKILLS_DIR}"

        md_path = skill_path / "SKILL.md"
        py_path = skill_path / "skill.py"

        # --------------------------------------------------------------
        # Validation
        # --------------------------------------------------------------
        if not md_path.exists():
            return f"❌ No SKILL.md found in {skill_path}"

        if py_path.exists() and not overwrite:
            return (
                f"❌ skill.py already exists at {py_path}\n"
                f"Use --overwrite to regenerate."
            )

        content = md_path.read_text(encoding="utf-8")

        metadata = self._extract_yaml(content)
        if isinstance(metadata, str):  # error message
            return metadata

        execution_mode = metadata.get("execution_mode", "deterministic")
        if force_llm:
            execution_mode = "hybrid"

        skill_name_md = metadata.get("name", skill_name)
        description = metadata.get("description", "Generated skill")
        allowed_tools = metadata.get("allowed_tools", [])
        expected_logic = self._extract_section(content, "Expected Logic")

        # --------------------------------------------------------------
        # Generate code
        # --------------------------------------------------------------
        code = self._build_scaffold(skill_name_md, description, allowed_tools, expected_logic)

        if execution_mode == "llm":
            logger.info(f"🤖 Generating via LLM for '{skill_name}'...")
            generated = self._call_llm(context, content, code)
            if generated:
                code = generated

        elif execution_mode == "hybrid":
            logger.info(f"🤖 Enhancing via LLM for '{skill_name}'...")
            enhanced = self._call_llm(context, content, code)
            if enhanced:
                code = enhanced

        code = self._normalize_code(code)
        result = validate_skill_py(code=code, skill_name=skill_name)
        if not result.valid:
            return f"❌ Generated skill.py failed validation:\n{result.failure_reason()}"

        # --------------------------------------------------------------
        # Dry run check - THIS IS WHERE IT GOES
        # --------------------------------------------------------------
        if dry_run:
            return (
                f"[DRY RUN] Would create {py_path}\n"
                f"Mode: {execution_mode}\n\n"
                "=== Code Preview ===\n"
                f"{code[:1000]}{'...' if len(code) > 1000 else ''}"
            )

        # --------------------------------------------------------------
        # WRITE LOGIC - HERE IT IS
        # --------------------------------------------------------------
        skill_path.mkdir(parents=True, exist_ok=True) # ensure dir exists
        write_file = context.agent_tools.get("write_file")
        if not write_file:
            return "[create_skill_py] Tool 'write_file' not found in agent_tools."

        write_result = write_file.func({"path": str(py_path), "content": code})
        if "Error" in str(write_result):
            return f"❌ Failed to write skill.py:\n{write_result}"

        mode_label = {
            "deterministic": "🧱 Deterministic",
            "llm": "🤖 LLM-generated",
            "hybrid": "⚙️ Hybrid (scaffold + LLM)",
        }[execution_mode]

        return (
            f"✅ skill.py generated for '{skill_name}'\n"
            f"Location: {py_path}\n"
            f"{mode_label}"
        )
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _parse_request(self, request: str):
        prefix = "/skill create_skill_py"
        raw = request.strip()

        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()

        if not raw:
            return "Usage: /skill create_skill_py <skill-name> [--overwrite] [--llm] [--dry_run]"

        parts = raw.split()

        skill_name = parts[0]
        overwrite = "--overwrite" in parts
        force_llm = "--llm" in parts
        dry_run = "--dry_run" in parts

        if not re.match(r'^[a-z0-9][a-z0-9\-]*$', skill_name):
            return f"❌ Invalid skill name '{skill_name}'"

        return skill_name, overwrite, force_llm , dry_run

    def _extract_yaml(self, content: str) -> Optional[dict] | str:
        if not content.startswith("---"):
            return "❌ Missing YAML front-matter. Must start with ---"

        try:
            _, yaml_block, _ = content.split("---", 2)
            import yaml
            data = yaml.safe_load(yaml_block)
        except Exception as e:
            return f"❌ Invalid YAML syntax: {e}"

        # Validate required fields
        required = ["name", "description"]
        missing = [f for f in required if f not in data]
        if missing:
            return f"❌ YAML missing required fields: {missing}"

        mode = data.get("execution_mode", "deterministic")
        if mode not in {"deterministic", "llm", "hybrid"}:
            return f"❌ Invalid execution_mode '{mode}'. Must be: deterministic|llm|hybrid"

        return data

    def _extract_section(self, md: str, section: str) -> str:
        match = re.search(rf"## {section}(.*?)(##|$)", md, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _build_scaffold(self, name, desc, tools, logic):
        class_name = "".join(
            x.capitalize() for x in name.replace("-", "_").split("_")
        ) + "Skill"

        return f'''from py_mono.skill.base import Skill, SkillContext
import logging

logger = logging.getLogger(__name__)


class {class_name}(Skill):

    def name(self) -> str:
        return "{name}"

    def description(self) -> str:
        return "{desc}"

    def run(self, request: str, context: SkillContext) -> str:
        """
        Allowed tools:
        {tools}

        Expected Logic:
        {logic}
        """
        try:
            logger.info(f"Running {{self.name()}} with request: {{request}}")

            # TODO: implement logic

            return f"[{{self.name()}}] Not yet implemented."

        except Exception as e:
            logger.error(f"Error in {{self.name()}}: {{e}}")
            return f"[{{self.name()}}] Error: {{e}}"
'''

    def _call_llm(self, context: SkillContext, md: str, scaffold: str) -> Optional[str]:
        try:
            provider = context.session_manager.get_active_provider()

            prompt = f"""
Given this SKILL.md:
{md}

And this scaffold:
{scaffold}

Implement the run() method fully.
Do not change structure.
Return only valid Python.
"""

            response = provider.generate(
                messages=[{"role": "user", "content": prompt}],
                tools=None
            )

            text = response.get("text", "")
            return text.strip() if text.strip() else None

        except Exception as e:
            logger.error(f"LLM failed: {e}")
            return None

    def _normalize_code(self, code: str) -> str:
        code = re.sub(r"<thinking>.*?</thinking>", "", code, flags=re.DOTALL)
        code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
        code = _strip_markdown_fences(code)
        return code.strip()

