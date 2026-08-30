from pathlib import Path

from py_mono.skill.lifecycle import (
    STATUS_FAILED,
    STATUS_PASSED,
    STAGE_CRITIQUE,
    SkillLifecycleRun,
    parse_allowed_tools,
    smoke_test_generated_skill,
)
from py_mono.skill.base import SkillContext
from py_mono.tools.tool import Tool


VALID_SKILL_CODE = '''
from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "demo_skill"

    def description(self):
        return "demo"

    def run(self, request, context):
        return "smoke ok"
'''


FAILING_SKILL_CODE = '''
from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "demo_skill"

    def description(self):
        return "demo"

    def run(self, request, context):
        raise ValueError("boom")
'''


USES_BLOCKED_TOOL_CODE = '''
from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "demo_skill"

    def description(self):
        return "demo"

    def run(self, request, context):
        return context.agent_tools["read_file"].run(path="x.py")
'''


def make_context():
    tools = {
        "list_files": Tool("list_files", "list files", lambda path=".": "ok"),
        "read_file": Tool("read_file", "read file", lambda path=".": "data"),
    }
    return SkillContext(workspace_root=Path("."), agent_tools=tools, session_manager=None)


def test_lifecycle_run_renders_ordered_stage_results():
    run = SkillLifecycleRun("demo_skill")
    run.add(STAGE_CRITIQUE, STATUS_PASSED, "spec accepted", ["warning"])

    rendered = run.render()

    assert "Lifecycle:" in rendered
    assert "Critique: passed - spec accepted" in rendered
    assert "warning" in rendered


def test_parse_allowed_tools_defaults_to_known_tools_when_missing():
    skill_md = "---\nname: demo_skill\nstatus: proposed\n---\n# demo\n"

    assert parse_allowed_tools(skill_md, ["list_files", "read_file"]) == {
        "list_files",
        "read_file",
    }


def test_parse_allowed_tools_intersects_requested_tools_with_known_tools():
    skill_md = (
        "---\n"
        "name: demo_skill\n"
        "status: proposed\n"
        "allowed_tools:\n"
        "  - list_files\n"
        "  - missing_tool\n"
        "---\n"
        "# demo\n"
    )

    assert parse_allowed_tools(skill_md, ["list_files", "read_file"]) == {"list_files"}


def test_smoke_test_generated_skill_passes_for_valid_skill():
    result = smoke_test_generated_skill(
        skill_name="demo_skill",
        code=VALID_SKILL_CODE,
        context=make_context(),
        allowed_tools={"list_files", "read_file"},
    )

    assert result.status == STATUS_PASSED
    assert result.output_preview == "smoke ok"
    assert result.failure_reason == ""


def test_smoke_test_generated_skill_returns_actionable_failure_reason():
    result = smoke_test_generated_skill(
        skill_name="demo_skill",
        code=FAILING_SKILL_CODE,
        context=make_context(),
        allowed_tools={"list_files", "read_file"},
    )

    assert result.status == STATUS_FAILED
    assert "ValueError: boom" in result.failure_reason


def test_smoke_test_generated_skill_enforces_allowed_tools():
    result = smoke_test_generated_skill(
        skill_name="demo_skill",
        code=USES_BLOCKED_TOOL_CODE,
        context=make_context(),
        allowed_tools={"list_files"},
    )

    assert result.status == STATUS_FAILED
    assert "not allowed to use the tool 'read_file'" in result.failure_reason
