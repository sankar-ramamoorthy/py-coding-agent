from pathlib import Path

import pytest

from py_mono.skill.base import SkillContext
from py_mono.skill.worker import WorkerExecutionError, run_skill_in_worker
from py_mono.tools.tool import Tool


SKILL_CALLS_TOOL = '''
from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "demo_skill"
    def description(self):
        return "demo"
    def run(self, request, context):
        return context.agent_tools["list_files"].run(path=".")
'''


SKILL_CALLS_FUNC = '''
from py_mono.skill.base import Skill, SkillContext

class DemoSkill(Skill):
    def name(self):
        return "demo_skill"
    def description(self):
        return "demo"
    def run(self, request, context):
        return context.agent_tools["list_files"].func(path=".")
'''


def make_context():
    return SkillContext(
        workspace_root=Path("."),
        agent_tools={
            "list_files": Tool("list_files", "list files", lambda path=".": "listed"),
            "read_file": Tool("read_file", "read file", lambda path=".": "data"),
        },
        session_manager=None,
    )


def test_worker_runs_skill_and_services_allowed_tool_rpc(tmp_path):
    skill_py = tmp_path / "skill.py"
    skill_py.write_text(SKILL_CALLS_TOOL, encoding="utf-8")

    result = run_skill_in_worker(
        skill_py_path=skill_py,
        skill_name="demo_skill",
        request="/skill demo_skill",
        context=make_context(),
        allowed_tools={"list_files"},
    )

    assert result == "listed"


def test_worker_rejects_disallowed_tool_rpc(tmp_path):
    skill_py = tmp_path / "skill.py"
    skill_py.write_text(SKILL_CALLS_TOOL, encoding="utf-8")

    with pytest.raises(WorkerExecutionError, match="not allowed to use the tool 'list_files'"):
        run_skill_in_worker(
            skill_py_path=skill_py,
            skill_name="demo_skill",
            request="/skill demo_skill",
            context=make_context(),
            allowed_tools={"read_file"},
        )


def test_worker_rejects_direct_tool_func_access(tmp_path):
    skill_py = tmp_path / "skill.py"
    skill_py.write_text(SKILL_CALLS_FUNC, encoding="utf-8")

    with pytest.raises(WorkerExecutionError, match="Direct tool.func"):
        run_skill_in_worker(
            skill_py_path=skill_py,
            skill_name="demo_skill",
            request="/skill demo_skill",
            context=make_context(),
            allowed_tools={"list_files"},
        )
