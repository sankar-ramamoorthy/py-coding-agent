"""Helpers for pre-approval skill lifecycle checks."""

from __future__ import annotations

import importlib.util
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Optional

import yaml

from py_mono.skill.approval import wrap_agent_tools
from py_mono.skill.base import Skill, SkillContext

STAGE_CRITIQUE = "Critique"
STAGE_GENERATE = "Generate"
STAGE_VALIDATE = "Validate"
STAGE_TEST = "Test"
STAGE_PROPOSE = "Propose"

STATUS_PASSED = "passed"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

ORDERED_STAGES = (
    STAGE_CRITIQUE,
    STAGE_GENERATE,
    STAGE_VALIDATE,
    STAGE_TEST,
    STAGE_PROPOSE,
)


@dataclass
class LifecycleStageResult:
    stage: str
    status: str
    message: str
    details: list[str] = field(default_factory=list)


@dataclass
class SmokeTestResult:
    status: str
    request: str
    output_preview: str = ""
    failure_reason: str = ""

    @property
    def passed(self) -> bool:
        return self.status == STATUS_PASSED


@dataclass
class SkillLifecycleRun:
    skill_name: str
    stages: list[LifecycleStageResult] = field(default_factory=list)

    def add(
        self,
        stage: str,
        status: str,
        message: str,
        details: Optional[Iterable[str]] = None,
    ) -> None:
        self.stages.append(
            LifecycleStageResult(
                stage=stage,
                status=status,
                message=message,
                details=list(details or []),
            )
        )

    def render(self) -> str:
        lines = ["Lifecycle:"]
        for result in self.stages:
            lines.append(f"  - {result.stage}: {result.status} - {result.message}")
            for detail in result.details:
                lines.append(f"      {detail}")
        return "\n".join(lines)


def skipped_stage(stage: str, reason: str) -> LifecycleStageResult:
    return LifecycleStageResult(stage=stage, status=STATUS_SKIPPED, message=reason)


def parse_allowed_tools(skill_md_content: str, known_tools: Iterable[str]) -> set[str]:
    """Read allowed_tools from SKILL.md front matter.

    If the field is absent or malformed, match runtime behavior by allowing
    all currently available tools.
    """

    known_tool_set = set(known_tools)
    if not skill_md_content.strip().startswith("---"):
        return known_tool_set

    lines = skill_md_content.splitlines()
    end = None
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            end = index
            break

    if end is None:
        return known_tool_set

    try:
        metadata = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError:
        return known_tool_set

    raw_tools = metadata.get("allowed_tools")
    if raw_tools is None:
        return known_tool_set
    if isinstance(raw_tools, str):
        requested = {tool.strip() for tool in raw_tools.split(",") if tool.strip()}
    elif isinstance(raw_tools, list):
        requested = {str(tool).strip() for tool in raw_tools if str(tool).strip()}
    else:
        return known_tool_set

    return requested & known_tool_set


def smoke_test_generated_skill(
    *,
    skill_name: str,
    code: str,
    context: SkillContext,
    allowed_tools: set[str],
    request: Optional[str] = None,
) -> SmokeTestResult:
    """Run validated generated skill code once without approving it."""

    smoke_request = request or f"/skill {skill_name} smoke-test"
    try:
        skill = _load_skill_from_code(skill_name, code)
        safe_context = SkillContext(
            workspace_root=context.workspace_root,
            agent_tools=wrap_agent_tools(context.agent_tools, allowed_tools, skill_name),
            session_manager=context.session_manager,
        )
        safe_context.calling_skill = skill_name
        output = skill.run(smoke_request, safe_context)
        if output is None:
            return SmokeTestResult(
                status=STATUS_FAILED,
                request=smoke_request,
                failure_reason="Smoke test returned None",
            )
        preview = str(output).strip().replace("\n", " ")[:200]
        return SmokeTestResult(
            status=STATUS_PASSED,
            request=smoke_request,
            output_preview=preview,
        )
    except Exception as exc:
        return SmokeTestResult(
            status=STATUS_FAILED,
            request=smoke_request,
            failure_reason=f"{exc.__class__.__name__}: {exc}",
        )


def _load_skill_from_code(skill_name: str, code: str) -> Skill:
    with tempfile.TemporaryDirectory(prefix=f"{skill_name}_smoke_") as temp_dir:
        module_path = Path(temp_dir) / "skill.py"
        module_path.write_text(code, encoding="utf-8")
        spec = importlib.util.spec_from_file_location(
            f"skills.{skill_name}.smoke_test", module_path
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Could not create module spec for generated skill")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for value in vars(module).values():
            if isinstance(value, type) and issubclass(value, Skill) and value is not Skill:
                return value()

    raise RuntimeError("No Skill subclass found in generated code")
