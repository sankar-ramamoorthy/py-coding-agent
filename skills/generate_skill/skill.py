# skills/generate_skill/skill.py
"""
generate_skill - LLM-powered skill generator.

Generates a complete skill (SKILL.md + skill.py) from a name and description
using two LLM calls:

  Call 1: Generate SKILL.md
  Call 2: Generate skill.py (with retry on validation failure)

Validation and one pre-approval smoke test run before saving the skill as
proposed. See ADR-011, ADR-013, and ISS-015.
"""

import logging
import re
import time
from pathlib import Path
from typing import Optional

from py_mono.skill.base import SKILLS_DIR, Skill, SkillContext
from py_mono.skill.diffing import (
    build_artifact_diff,
    load_approved_baseline,
    render_diff_report,
    write_candidate,
)
from py_mono.skill.evolution import latest_failure_context
from py_mono.skill.lifecycle import (
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SKIPPED,
    STAGE_CRITIQUE,
    STAGE_GENERATE,
    STAGE_PROPOSE,
    STAGE_TEST,
    STAGE_VALIDATE,
    SkillLifecycleRun,
    parse_allowed_tools,
    smoke_test_generated_skill,
)
from py_mono.skill.prompts import build_skill_md_prompt, build_skill_py_prompt
from py_mono.skill.reporting import ReportWriteResult, write_lifecycle_report
from py_mono.skill.validator import validate_skill_md, validate_skill_py

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)
MAX_RETRIES = 1  # one retry on skill.py validation failure


class GenerateSkill(Skill):
    def name(self) -> str:
        return "generate_skill"

    def description(self) -> str:
        return "Generate a new skill (SKILL.md + skill.py) using the LLM"

    def run(self, request: str, context: SkillContext) -> str:
        parsed = self._parse_request(request)
        if isinstance(parsed, str):
            return parsed

        skill_name, description, mode, failure_context = parsed
        skill_path = SKILLS_DIR / skill_name
        is_existing_skill = (skill_path / "SKILL.md").exists() or (skill_path / "skill.py").exists()
        if mode == "create" and is_existing_skill:
            mode = "regenerate"
        if mode == "evolve" and failure_context is None:
            failure_context = latest_failure_context(skill_name)
            if failure_context is None:
                return (
                    f"No usable failure context is available for skill '{skill_name}'.\n"
                    "Run the skill again to capture a failure before requesting evolution."
                )
            description = (
                f"Revise the existing skill using this failure context.\n\n"
                f"{failure_context.to_prompt_text()}"
            )
        if mode == "create" and is_existing_skill:
            return (
                f"ERROR: Skill '{skill_name}' already exists at {skill_path}.\n"
                f"Use /skill help {skill_name} to inspect it."
            )
        if mode in ("regenerate", "evolve") and not is_existing_skill:
            return f"ERROR: Skill '{skill_name}' does not exist, so it cannot be {mode}d."

        lifecycle = SkillLifecycleRun(skill_name)
        available_tools = self._build_tool_descriptions(context)

        print(f"Generating SKILL.md for '{skill_name}'...")
        skill_md_content = self._call_llm(
            context=context,
            prompt=build_skill_md_prompt(
                skill_name=skill_name,
                description=description,
                available_tools=available_tools,
            ),
        )
        if skill_md_content is None:
            lifecycle.add(
                STAGE_GENERATE,
                STATUS_FAILED,
                "LLM call failed while generating SKILL.md.",
            )
            lifecycle.add(STAGE_VALIDATE, STATUS_SKIPPED, "Generation failed.")
            lifecycle.add(STAGE_TEST, STATUS_SKIPPED, "Generation failed.")
            lifecycle.add(STAGE_PROPOSE, STATUS_SKIPPED, "Generation failed.")
            report_result = self._write_lifecycle_report(
                skill_name=skill_name,
                mode=mode,
                status="failed",
                lifecycle=lifecycle,
                skill_path=skill_path,
                report_dir=skill_path,
                next_steps=["Try again."],
            )
            return self._build_failed_lifecycle_response(
                skill_name=skill_name,
                lifecycle=lifecycle,
                next_step="Try again.",
                report_result=report_result,
            )

        md_result = validate_skill_md(
            content=skill_md_content,
            skill_name=skill_name,
            known_tools=list(available_tools.keys()),
        )
        skill_md_content = md_result.fixed_content or skill_md_content
        lifecycle.add(
            STAGE_CRITIQUE,
            STATUS_PASSED,
            "Skill specification accepted.",
            md_result.warnings,
        )

        print(f"Generating skill.py for '{skill_name}'...")
        skill_py_content, py_result, warnings = self._generate_skill_py(
            context=context,
            skill_name=skill_name,
            description=description,
            skill_md_content=skill_md_content,
            available_tools=available_tools,
        )
        lifecycle.add(STAGE_GENERATE, STATUS_PASSED, "Generated SKILL.md and skill.py.")

        if skill_py_content is None or not py_result.valid:
            failure_reason = py_result.failure_reason()
            lifecycle.add(
                STAGE_VALIDATE,
                STATUS_FAILED,
                "Generated skill.py failed validation.",
                failure_reason.splitlines(),
            )
            lifecycle.add(STAGE_TEST, STATUS_SKIPPED, "Validation failed.")
            lifecycle.add(STAGE_PROPOSE, STATUS_SKIPPED, "Validation failed.")
            next_step = (
                "Try rephrasing your description or switch to a more capable model:\n"
                "  /provider litellm groq/qwen/qwen3-32b"
            )
            report_result = self._write_lifecycle_report(
                skill_name=skill_name,
                mode=mode,
                status="failed",
                lifecycle=lifecycle,
                skill_path=skill_path,
                report_dir=skill_path,
                failure_context=failure_context,
                next_steps=next_step.splitlines(),
            )
            return self._build_failed_lifecycle_response(
                skill_name=skill_name,
                lifecycle=lifecycle,
                next_step=next_step,
                report_result=report_result,
            )

        lifecycle.add(STAGE_VALIDATE, STATUS_PASSED, "Generated skill.py passed validation.")

        smoke_result = smoke_test_generated_skill(
            skill_name=skill_name,
            code=skill_py_content,
            context=context,
            allowed_tools=parse_allowed_tools(skill_md_content, available_tools.keys()),
        )
        if not smoke_result.passed:
            lifecycle.add(
                STAGE_TEST,
                STATUS_FAILED,
                "Smoke test failed.",
                [smoke_result.failure_reason],
            )
            lifecycle.add(STAGE_PROPOSE, STATUS_SKIPPED, "Smoke test failed.")
            report_result = self._write_lifecycle_report(
                skill_name=skill_name,
                mode=mode,
                status="failed",
                lifecycle=lifecycle,
                skill_path=skill_path,
                report_dir=skill_path,
                smoke_test=smoke_result,
                failure_context=failure_context,
                next_steps=["Retry generation after adjusting the skill description."],
            )
            return self._build_failed_lifecycle_response(
                skill_name=skill_name,
                lifecycle=lifecycle,
                next_step="Retry generation after adjusting the skill description.",
                report_result=report_result,
            )

        smoke_details = []
        if smoke_result.output_preview:
            smoke_details.append(f"Output preview: {smoke_result.output_preview}")
        lifecycle.add(STAGE_TEST, STATUS_PASSED, "Smoke test passed.", smoke_details)

        try:
            skill_path.mkdir(parents=True, exist_ok=True)
            if mode == "create":
                write_path = skill_path
                (skill_path / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
                (skill_path / "skill.py").write_text(skill_py_content, encoding="utf-8")
            else:
                write_path = write_candidate(skill_path, skill_md_content, skill_py_content)
        except Exception as e:
            lifecycle.add(STAGE_PROPOSE, STATUS_FAILED, f"Failed to save skill files: {e}")
            report_result = self._write_lifecycle_report(
                skill_name=skill_name,
                mode=mode,
                status="failed",
                lifecycle=lifecycle,
                skill_path=skill_path,
                report_dir=skill_path,
                smoke_test=smoke_result,
                failure_context=failure_context,
                next_steps=["Check filesystem permissions and try again."],
            )
            return self._build_failed_lifecycle_response(
                skill_name=skill_name,
                lifecycle=lifecycle,
                next_step="Check filesystem permissions and try again.",
                report_result=report_result,
            )

        lifecycle.add(STAGE_PROPOSE, STATUS_PASSED, "Skill saved as proposed.")
        diff_report = ""
        diffs = []
        if mode in ("regenerate", "evolve"):
            baseline = load_approved_baseline(SKILLS_DIR, skill_name)
            diffs = [
                build_artifact_diff(
                    "SKILL.md",
                    baseline.skill_md_content,
                    skill_md_content,
                    baseline.available,
                    baseline.reason,
                ),
                build_artifact_diff(
                    "skill.py",
                    baseline.skill_py_content,
                    skill_py_content,
                    baseline.available,
                    baseline.reason,
                ),
            ]
            diff_report = render_diff_report(diffs)
        next_steps = self._next_steps(skill_name, write_path, mode)
        report_result = self._write_lifecycle_report(
            skill_name=skill_name,
            mode=mode,
            status="proposed",
            lifecycle=lifecycle,
            skill_path=skill_path,
            report_dir=write_path,
            candidate_path=write_path,
            smoke_test=smoke_result,
            diffs=diffs,
            failure_context=failure_context,
            next_steps=next_steps,
        )
        return self._build_response(
            skill_name=skill_name,
            skill_path=write_path,
            skill_py_content=skill_py_content,
            md_warnings=md_result.warnings,
            py_warnings=warnings,
            lifecycle=lifecycle,
            mode=mode,
            diff_report=diff_report,
            failure_context=failure_context.to_prompt_text() if failure_context else "",
            report_result=report_result,
        )

    def _parse_request(self, request: str):
        prefix = "/skill generate_skill"
        raw = request.strip()
        if raw.startswith(prefix):
            raw = raw[len(prefix):].strip()

        if raw.startswith("--evolve "):
            skill_name = raw[len("--evolve "):].strip().lower().replace(" ", "-")
            if not skill_name:
                return "ERROR: Skill name cannot be empty."
            if not re.match(r"^[a-z0-9][a-z0-9\-]*$", skill_name):
                return (
                    f"ERROR: Invalid skill name '{skill_name}'. "
                    "Use lowercase letters, numbers, and hyphens only."
                )
            return skill_name, "", "evolve", None

        parts = raw.split("|", 1)
        if len(parts) != 2:
            return (
                "Usage: /skill generate_skill <skill-name> | <description>\n"
                "       /skill generate_skill --evolve <skill-name>\n"
                "Example: /skill generate_skill list-python-files | "
                "List all Python files in the workspace with sizes"
            )

        skill_name = parts[0].strip().lower().replace(" ", "-")
        description = parts[1].strip()

        if not skill_name:
            return "ERROR: Skill name cannot be empty."
        if not description:
            return "ERROR: Description cannot be empty."

        if not re.match(r"^[a-z0-9][a-z0-9\-]*$", skill_name):
            return (
                f"ERROR: Invalid skill name '{skill_name}'. "
                "Use lowercase letters, numbers, and hyphens only."
            )

        return skill_name, description, "create", None

    def _build_tool_descriptions(self, context: SkillContext) -> dict:
        result = {}
        for name, tool in context.agent_tools.items():
            desc = getattr(tool, "description", "No description available")
            result[name] = desc
        return result

    def _strip_thinking(self, text: str) -> str:
        text = re.sub(r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
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

            text = self._strip_thinking(text.strip())
            text = _strip_markdown_fences(text)
            logger.debug("LLM response normalized for generated skill output")
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
        from py_mono.skill.validator import SkillPyValidationResult

        retry_reason = ""
        warnings = []
        code = ""
        prev_code = ""

        for attempt in range(MAX_RETRIES + 1):
            if attempt > 0:
                print(f"Retrying skill.py generation (attempt {attempt + 1})...")

            prev_code = code
            code = self._call_llm(
                context=context,
                prompt=build_skill_py_prompt(
                    skill_name=skill_name,
                    description=description,
                    skill_md_content=skill_md_content,
                    available_tools=available_tools,
                    retry_reason=retry_reason,
                    prev_code=prev_code,
                ),
            )

            debug_dir = SKILLS_DIR / skill_name
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"skill_debug_{int(time.time())}.txt"
            if code:
                debug_path.write_text(code, encoding="utf-8")
            else:
                debug_path.write_text("[EMPTY RESPONSE FROM LLM]", encoding="utf-8")
            logger.debug(f"Saved debug LLM output to {debug_path}")

            if code is None:
                return None, SkillPyValidationResult(
                    valid=False,
                    syntax_errors=["LLM returned empty response"],
                ), warnings

            code = self._normalize_code(code)
            result = validate_skill_py(code=code, skill_name=skill_name)
            if result.valid:
                return code, result, warnings

            if result.has_forbidden() and attempt < MAX_RETRIES:
                retry_reason = result.failure_reason()
                continue

            if result.has_syntax_errors() and attempt < MAX_RETRIES:
                retry_reason = result.failure_reason()
                continue

            warnings.extend(result.syntax_errors)
            warnings.extend(result.structure_errors)

            if result.structure_errors or result.has_syntax_errors():
                if attempt < MAX_RETRIES:
                    retry_reason = result.failure_reason()
                    continue
                return code, result, warnings

            return code, result, warnings

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
        lifecycle: SkillLifecycleRun,
        mode: str = "create",
        diff_report: str = "",
        failure_context: str = "",
        report_result: Optional[ReportWriteResult] = None,
    ) -> str:
        lines = []

        all_warnings = md_warnings + py_warnings
        if all_warnings:
            lines.append(f"WARNING: Skill '{skill_name}' saved with warnings:")
            for warning in all_warnings:
                lines.append(f"   - {warning}")
            lines.append("")
        else:
            lines.append(f"Skill '{skill_name}' generated successfully.")
            lines.append("")

        lines.append(lifecycle.render())
        lines.append("")
        if failure_context:
            lines.append("Failure context:")
            lines.append(failure_context)
            lines.append("")
        if diff_report:
            lines.append(diff_report)
            lines.append("")
        lines.append("Status: proposed - not yet executable.")
        lines.append(f"Location: {skill_path}")
        self._append_report_lines(lines, report_result)
        lines.append("")
        lines.append("Next steps:")
        for index, step in enumerate(self._next_steps(skill_name, skill_path, mode), 1):
            lines.append(f"  {index}. {step}")
        lines.append("")

        preview_lines = skill_py_content.splitlines()[:8]
        lines.append("Preview of generated skill.py:")
        lines.append("  " + "\n  ".join(preview_lines))

        return "\n".join(lines)

    def _build_failed_lifecycle_response(
        self,
        skill_name: str,
        lifecycle: SkillLifecycleRun,
        next_step: str,
        report_result: Optional[ReportWriteResult] = None,
    ) -> str:
        lines = [
            f"Skill '{skill_name}' could NOT be proposed.",
            "",
            lifecycle.render(),
            "",
        ]
        self._append_report_lines(lines, report_result)
        lines.extend(
            [
                "Next step:",
                f"  {next_step}",
            ]
        )
        return "\n".join(lines)

    def _next_steps(self, skill_name: str, skill_path: Path, mode: str) -> list[str]:
        return [
            f"Review:  /skill review {skill_name}",
            f"Files:   {skill_path}",
            f"Approve: /approve {skill_name}",
            f"Run:     /skill {skill_name}",
        ]

    def _write_lifecycle_report(
        self,
        *,
        skill_name: str,
        mode: str,
        status: str,
        lifecycle: SkillLifecycleRun,
        skill_path: Path,
        report_dir: Path,
        candidate_path: Optional[Path] = None,
        smoke_test=None,
        diffs=None,
        failure_context=None,
        next_steps: Optional[list[str]] = None,
    ) -> ReportWriteResult:
        return write_lifecycle_report(
            report_dir=report_dir,
            skill_name=skill_name,
            mode=mode,
            status=status,
            lifecycle=lifecycle,
            skill_path=skill_path,
            candidate_path=candidate_path,
            smoke_test=smoke_test,
            diffs=diffs or [],
            failure_context=failure_context,
            next_steps=next_steps or [],
        )

    def _append_report_lines(
        self,
        lines: list[str],
        report_result: Optional[ReportWriteResult],
    ) -> None:
        if report_result is None:
            return
        if report_result.ok and report_result.markdown_path is not None:
            lines.append(f"Lifecycle report: {report_result.markdown_path}")
            return
        lines.append(
            "WARNING: Lifecycle report could not be written: "
            f"{report_result.error or 'unknown error'}"
        )
